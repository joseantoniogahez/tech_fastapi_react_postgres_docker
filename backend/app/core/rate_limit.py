from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from math import ceil
from time import monotonic
from typing import Any, Protocol

from fastapi import Request, Response

from app.core.config.settings import RateLimitSettings
from app.core.errors.services import RateLimitedError, ServiceUnavailableError

logger = logging.getLogger("app.rate_limit")
_SURFACE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,31}$")

RATE_LIMIT_HEADER = "X-RateLimit-Limit"
RATE_LIMIT_REMAINING_HEADER = "X-RateLimit-Remaining"
RATE_LIMIT_RESET_HEADER = "X-RateLimit-Reset"
RETRY_AFTER_HEADER = "Retry-After"
RATE_LIMIT_RESPONSE_HEADERS = (
    RATE_LIMIT_HEADER,
    RATE_LIMIT_REMAINING_HEADER,
    RATE_LIMIT_RESET_HEADER,
)


class CounterStore(Protocol):
    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]: ...

    async def ping(self) -> None: ...

    async def aclose(self) -> None: ...


class RedisClient(Protocol):
    async def execute_command(self, *args: object) -> Any: ...

    async def ping(self) -> object: ...

    async def aclose(self) -> None: ...


class RedisPyClient:
    def __init__(self, client: Any) -> None:
        self._client = client

    async def execute_command(self, *args: object) -> Any:
        return await self._client.execute_command(*args)

    async def ping(self) -> object:
        return await self._client.ping()

    async def aclose(self) -> None:
        await self._client.aclose()


class MemoryCounterStore:
    def __init__(self, *, clock: Callable[[], float] = monotonic) -> None:
        self._clock = clock
        self._counters: dict[str, tuple[int, float]] = {}
        self._lock = asyncio.Lock()
        self._closed = False

    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        if self._closed:
            raise RuntimeError("Counter store is closed.")
        async with self._lock:
            now = self._clock()
            count, expires_at = self._counters.get(key, (0, now + window_seconds))
            if expires_at <= now:
                count, expires_at = 0, now + window_seconds
            count += 1
            self._counters[key] = (count, expires_at)
            return count, max(1, ceil(expires_at - now))

    async def ping(self) -> None:
        if self._closed:
            raise RuntimeError("Counter store is closed.")

    async def aclose(self) -> None:
        async with self._lock:
            self._counters.clear()
            self._closed = True


class RedisCounterStore:
    _INCREMENT_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
if ttl < 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
  ttl = redis.call('TTL', KEYS[1])
end
return {count, ttl}
"""

    def __init__(
        self,
        redis_url: str,
        password: str,
        *,
        timeout_seconds: float = 2.0,
        client: RedisClient | None = None,
    ) -> None:
        self._redis_url = redis_url
        self._password = password
        self._timeout_seconds = timeout_seconds
        self._client = client
        self._closed = False

    def _get_client(self) -> RedisClient:
        if self._closed:
            raise RuntimeError("Counter store is closed.")
        if self._client is None:
            from redis.asyncio import Redis

            self._client = RedisPyClient(
                Redis.from_url(
                    self._redis_url,
                    password=self._password,
                    decode_responses=False,
                    socket_connect_timeout=self._timeout_seconds,
                    socket_timeout=self._timeout_seconds,
                )
            )
        return self._client

    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        result = await self._get_client().execute_command(
            "EVAL",
            self._INCREMENT_SCRIPT,
            1,
            key,
            window_seconds,
        )
        if not isinstance(result, (list, tuple)) or len(result) != 2:
            raise RuntimeError("Redis returned an invalid rate-limit counter result.")
        count, ttl = result
        return int(count), max(1, int(ttl))

    async def ping(self) -> None:
        await self._get_client().ping()

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        client, self._client = self._client, None
        if client is not None:
            await client.aclose()


@dataclass(frozen=True)
class RateLimitRule:
    surface: str
    limit: int

    def __post_init__(self) -> None:
        if _SURFACE_PATTERN.fullmatch(self.surface) is None:
            raise ValueError("Rate-limit surface names must be lowercase snake_case.")
        if self.limit < 1:
            raise ValueError("Rate-limit values must be positive.")


class RateLimiter:
    def __init__(
        self,
        settings: RateLimitSettings,
        store: CounterStore | None,
    ) -> None:
        if settings.RATE_LIMIT_ENABLED and store is None:
            raise ValueError("Enabled rate limiting requires a counter store.")
        self._settings = settings
        self._store = store

    @property
    def uses_shared_store(self) -> bool:
        return self._settings.uses_shared_store

    def _rule_for(self, surface: str) -> RateLimitRule:
        limits = {
            "login": self._settings.RATE_LIMIT_LOGIN,
            "register": self._settings.RATE_LIMIT_REGISTER,
        }
        try:
            return RateLimitRule(surface, limits[surface])
        except KeyError:
            raise ValueError(f"Unknown rate-limit surface: {surface}.") from None

    def _counter_key(self, surface: str, client_host: str) -> str:
        digest = hashlib.sha256(f"{surface}\0{client_host}".encode()).hexdigest()
        return f"{self._settings.RATE_LIMIT_NAMESPACE}:{digest}"

    async def check(self, request: Request, surface: str) -> dict[str, str]:
        if not self._settings.RATE_LIMIT_ENABLED:
            return {}

        rule = self._rule_for(surface)
        client_host = request.client.host if request.client is not None else "unknown"
        store = self._store
        if store is None:
            raise ServiceUnavailableError(details={"dependency": "rate_limit_store"})

        try:
            count, reset_after = await store.increment(
                self._counter_key(rule.surface, client_host),
                self._settings.RATE_LIMIT_WINDOW_SECONDS,
            )
        except Exception:
            request_id = getattr(request.state, "request_id", "-")
            logger.warning(
                "event=rate_limit_store_unavailable request_id=%s surface=%s",
                request_id,
                rule.surface,
            )
            raise ServiceUnavailableError(details={"dependency": "rate_limit_store"}) from None

        headers = {
            RATE_LIMIT_HEADER: str(rule.limit),
            RATE_LIMIT_REMAINING_HEADER: str(max(0, rule.limit - count)),
            RATE_LIMIT_RESET_HEADER: str(reset_after),
        }
        if count > rule.limit:
            request_id = getattr(request.state, "request_id", "-")
            logger.warning(
                "event=rate_limit_rejected request_id=%s surface=%s",
                request_id,
                rule.surface,
            )
            raise RateLimitedError(
                details={"retry_after_seconds": reset_after},
                headers={**headers, RETRY_AFTER_HEADER: str(reset_after)},
            )
        return headers

    async def ping(self) -> None:
        if self.uses_shared_store:
            if self._store is None:
                raise RuntimeError("Shared rate-limit store is unavailable.")
            await self._store.ping()

    async def aclose(self) -> None:
        if self._store is not None:
            await self._store.aclose()


def build_rate_limiter(settings: RateLimitSettings) -> RateLimiter:
    store: CounterStore | None = None
    if settings.RATE_LIMIT_ENABLED:
        if settings.RATE_LIMIT_STORAGE == "redis":
            redis_url = settings.REDIS_URL
            if redis_url is None:
                raise RuntimeError("Validated Redis rate-limit settings are incomplete.")
            store = RedisCounterStore(
                redis_url,
                settings.redis_password_value(),
                timeout_seconds=settings.REDIS_TIMEOUT_SECONDS,
            )
        else:
            store = MemoryCounterStore()
    return RateLimiter(settings, store)


def rate_limit_dependency(surface: str) -> Callable[[Request, Response], Awaitable[None]]:
    RateLimitRule(surface, 1)

    async def dependency(request: Request, response: Response) -> None:
        limiter = getattr(request.app.state, "rate_limiter", None)
        if not isinstance(limiter, RateLimiter):
            raise ServiceUnavailableError(details={"dependency": "rate_limit_store"})
        headers = await limiter.check(request, surface)
        request.state.rate_limit_headers = headers
        for name, value in headers.items():
            response.headers[name] = value

    return dependency


LOGIN_RATE_LIMIT_DEPENDENCY = rate_limit_dependency("login")
REGISTER_RATE_LIMIT_DEPENDENCY = rate_limit_dependency("register")
