import asyncio
import logging
import re
from collections.abc import Generator
from pathlib import Path
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Response
from pydantic import ValidationError
from starlette.requests import Request
from starlette.testclient import TestClient

from app.core.config.settings import RateLimitSettings
from app.core.errors.domain import DomainErrorType
from app.core.errors.services import RateLimitedError, ServiceUnavailableError
from app.core.rate_limit import (
    RATE_LIMIT_HEADER,
    RATE_LIMIT_REMAINING_HEADER,
    RATE_LIMIT_RESET_HEADER,
    RETRY_AFTER_HEADER,
    MemoryCounterStore,
    RateLimiter,
    RateLimitRule,
    RedisCounterStore,
    build_rate_limiter,
    rate_limit_dependency,
)
from app.core.setup.dependencies import get_readiness_check_registry
from app.core.setup.factory import app_lifespan
from app.main import app


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class RecordingStore:
    def __init__(self, results: list[tuple[int, int]] | None = None) -> None:
        self.results = list(results or [(1, 60)])
        self.keys: list[str] = []
        self.closed = False

    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        self.keys.append(key)
        return self.results.pop(0)

    async def ping(self) -> None:
        return None

    async def aclose(self) -> None:
        self.closed = True


class UnavailableStore(RecordingStore):
    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        raise ConnectionError("redis://private-host:6379/0")

    async def ping(self) -> None:
        raise ConnectionError("redis unavailable")


class FakeRedisClient:
    def __init__(self, result: object = (2, 59)) -> None:
        self.result = result
        self.command_args: tuple[object, ...] | None = None
        self.ping_calls = 0
        self.closed = False

    async def execute_command(self, *args: object) -> object:
        self.command_args = args
        if isinstance(self.result, Exception):
            raise self.result
        return self.result

    async def ping(self) -> object:
        self.ping_calls += 1
        return True

    async def aclose(self) -> None:
        self.closed = True


class FakeRedisPyClient:
    def __init__(self, result: object) -> None:
        self.result = result
        self.script_args: tuple[object, ...] | None = None
        self.ping_calls = 0
        self.closed = False

    async def execute_command(self, *args: object) -> object:
        self.script_args = args
        return self.result

    async def ping(self) -> object:
        self.ping_calls += 1
        return True

    async def aclose(self) -> None:
        self.closed = True


def _request(
    *,
    client_host: str = "203.0.113.10",
    forwarded_for: str | None = None,
) -> Request:
    headers = [] if forwarded_for is None else [(b"x-forwarded-for", forwarded_for.encode("ascii"))]
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/v1/token",
            "headers": headers,
            "query_string": b"",
            "scheme": "https",
            "http_version": "1.1",
            "client": (client_host, 50000),
            "server": ("api.example", 443),
        }
    )
    request.state.request_id = "req-rate-limit-test"
    return request


def _memory_limiter(clock: FakeClock, *, enabled: bool = True) -> RateLimiter:
    settings = RateLimitSettings(
        RATE_LIMIT_ENABLED=enabled,
        RATE_LIMIT_STORAGE="memory",
        RATE_LIMIT_LOGIN=10,
        RATE_LIMIT_REGISTER=5,
        RATE_LIMIT_WINDOW_SECONDS=60,
    )
    return RateLimiter(settings, MemoryCounterStore(clock=clock) if enabled else None)


@pytest.fixture
def installed_memory_limiter(mock_client: TestClient) -> Generator[tuple[TestClient, FakeClock]]:
    original = app.state.rate_limiter
    clock = FakeClock()
    limiter = _memory_limiter(clock)
    app.state.rate_limiter = limiter
    try:
        yield mock_client, clock
    finally:
        app.state.rate_limiter = original
        asyncio.run(limiter.aclose())


def test_memory_counter_store_uses_fixed_windows_and_closes() -> None:
    clock = FakeClock()
    store = MemoryCounterStore(clock=clock)

    assert asyncio.run(store.increment("key", 60)) == (1, 60)
    clock.advance(1.2)
    assert asyncio.run(store.increment("key", 60)) == (2, 59)
    clock.advance(58.8)
    assert asyncio.run(store.increment("key", 60)) == (1, 60)

    asyncio.run(store.aclose())
    with pytest.raises(RuntimeError, match="closed"):
        asyncio.run(store.ping())
    with pytest.raises(RuntimeError, match="closed"):
        asyncio.run(store.increment("key", 60))


def test_limiter_uses_direct_peer_and_neutral_hashed_key_without_pii() -> None:
    store = RecordingStore([(1, 60), (2, 59)])
    limiter = RateLimiter(RateLimitSettings(), store)
    direct_peer = "203.0.113.10"

    first_headers = asyncio.run(
        limiter.check(
            _request(client_host=direct_peer, forwarded_for="198.51.100.7"),
            "login",
        )
    )
    asyncio.run(
        limiter.check(
            _request(client_host=direct_peer, forwarded_for="attacker@example.test"),
            "login",
        )
    )

    assert first_headers == {
        RATE_LIMIT_HEADER: "10",
        RATE_LIMIT_REMAINING_HEADER: "9",
        RATE_LIMIT_RESET_HEADER: "60",
    }
    assert store.keys[0] == store.keys[1]
    assert re.fullmatch(r"foundation:rate-limit:v1:[0-9a-f]{64}", store.keys[0])
    for sensitive_value in (direct_peer, "198.51.100.7", "attacker@example.test", "login"):
        assert sensitive_value not in store.keys[0]


def test_disabled_limiter_never_touches_a_store() -> None:
    settings = RateLimitSettings(RATE_LIMIT_ENABLED=False)
    limiter = RateLimiter(settings, None)

    assert asyncio.run(limiter.check(_request(), "login")) == {}
    asyncio.run(limiter.ping())
    asyncio.run(limiter.aclose())


def test_limiter_distinguishes_quota_exhaustion_and_store_outage(caplog: pytest.LogCaptureFixture) -> None:
    settings = RateLimitSettings(RATE_LIMIT_LOGIN=1)
    exhausted = RateLimiter(settings, RecordingStore([(2, 41)]))
    caplog.set_level(logging.WARNING, logger="app.rate_limit")

    with pytest.raises(RateLimitedError) as quota_error:
        asyncio.run(exhausted.check(_request(), "login"))
    assert quota_error.value.error_type == DomainErrorType.RATE_LIMITED
    assert quota_error.value.headers == {
        RATE_LIMIT_HEADER: "1",
        RATE_LIMIT_REMAINING_HEADER: "0",
        RATE_LIMIT_RESET_HEADER: "41",
        RETRY_AFTER_HEADER: "41",
    }

    unavailable = RateLimiter(settings, UnavailableStore())
    with pytest.raises(ServiceUnavailableError) as outage_error:
        asyncio.run(unavailable.check(_request(), "login"))
    assert outage_error.value.error_type == DomainErrorType.SERVICE_UNAVAILABLE
    assert "private-host" not in caplog.text
    assert "203.0.113.10" not in caplog.text


def test_redis_store_uses_one_atomic_lua_eval_and_closes_client() -> None:
    client = FakeRedisClient()
    store = RedisCounterStore("rediss://redis.example:6379/0", "unit-test-secret", client=client)

    assert asyncio.run(store.increment("namespace:hash", 60)) == (2, 59)
    assert client.command_args is not None
    command, script, key_count, key, window = client.command_args
    assert command == "EVAL"
    assert key_count == 1
    assert key == "namespace:hash"
    assert window == 60
    assert "INCR" in str(script)
    assert "EXPIRE" in str(script)
    assert "TTL" in str(script)

    asyncio.run(store.ping())
    assert client.ping_calls == 1
    asyncio.run(store.aclose())
    asyncio.run(store.aclose())
    assert client.closed is True
    with pytest.raises(RuntimeError, match="closed"):
        asyncio.run(store.increment("namespace:hash", 60))


def test_redis_store_creates_client_lazily_and_rejects_invalid_script_result() -> None:
    expected_client = FakeRedisPyClient(result="invalid")
    store = RedisCounterStore("rediss://redis.example:6379/0", "unit-test-secret")

    with patch("redis.asyncio.Redis.from_url", return_value=expected_client) as from_url:
        with pytest.raises(RuntimeError, match="invalid rate-limit counter"):
            asyncio.run(store.increment("namespace:hash", 60))
        asyncio.run(store.ping())
        asyncio.run(store.aclose())

    from_url.assert_called_once_with(
        "rediss://redis.example:6379/0",
        password="unit-test-secret",  # pragma: allowlist secret
        decode_responses=False,
        socket_connect_timeout=2.0,
        socket_timeout=2.0,
    )
    assert expected_client.script_args is not None
    assert expected_client.script_args[0] == "EVAL"
    assert expected_client.script_args[2:] == (1, "namespace:hash", 60)
    assert expected_client.ping_calls == 1
    assert expected_client.closed is True


def test_rate_limit_objects_reject_invalid_internal_contracts() -> None:
    with pytest.raises(ValueError, match="surface names"):
        RateLimitRule("Invalid-Surface", 1)
    with pytest.raises(ValueError, match="positive"):
        RateLimitRule("login", 0)
    with pytest.raises(ValueError, match="counter store"):
        RateLimiter(RateLimitSettings(), None)

    limiter = RateLimiter(RateLimitSettings(), RecordingStore())
    with pytest.raises(ValueError, match="Unknown rate-limit surface"):
        asyncio.run(limiter.check(_request(), "unknown"))


def test_limiter_defensive_missing_store_paths_fail_closed() -> None:
    limiter = RateLimiter(RateLimitSettings(), RecordingStore())
    limiter._store = None  # type: ignore[assignment]
    with pytest.raises(ServiceUnavailableError):
        asyncio.run(limiter.check(_request(), "login"))

    shared_settings = RateLimitSettings(
        RATE_LIMIT_STORAGE="redis",
        REDIS_URL="rediss://redis.example:6379/0",
        REDIS_PASSWORD="unit-test-secret",  # pragma: allowlist secret
    )
    shared_limiter = RateLimiter(shared_settings, RecordingStore())
    shared_limiter._store = None  # type: ignore[assignment]
    with pytest.raises(RuntimeError, match="Shared rate-limit store"):
        asyncio.run(shared_limiter.ping())


def test_build_rate_limiter_covers_memory_disabled_redis_and_defensive_url_path() -> None:
    assert isinstance(build_rate_limiter(RateLimitSettings())._store, MemoryCounterStore)
    assert build_rate_limiter(RateLimitSettings(RATE_LIMIT_ENABLED=False))._store is None

    redis_settings = RateLimitSettings(
        RATE_LIMIT_STORAGE="redis",
        REDIS_URL="rediss://redis.example:6379/0",
        REDIS_PASSWORD="unit-test-secret",  # pragma: allowlist secret
    )
    assert isinstance(build_rate_limiter(redis_settings)._store, RedisCounterStore)
    redis_settings.REDIS_URL = None
    with pytest.raises(RuntimeError, match="incomplete"):
        build_rate_limiter(redis_settings)


def test_rate_limit_dependency_fails_closed_without_installed_limiter() -> None:
    dependency = rate_limit_dependency("login")
    test_app = MagicMock()
    test_app.state = MagicMock(spec=[])
    request = Request({"type": "http", "app": test_app})

    async def run_dependency() -> None:
        await dependency(request, Response())

    with pytest.raises(ServiceUnavailableError):
        asyncio.run(run_dependency())


def test_readiness_registers_redis_only_for_enabled_shared_store() -> None:
    async def database_check() -> None:
        return None

    local_app = MagicMock()
    local_app.state.rate_limiter = _memory_limiter(FakeClock())
    local_registry = get_readiness_check_registry(
        Request({"type": "http", "app": local_app}),
        database_check,
    )
    assert [definition.name for definition in local_registry.definitions()] == ["database"]

    shared_store = RecordingStore()
    shared_settings = RateLimitSettings(
        RATE_LIMIT_STORAGE="redis",
        REDIS_URL="rediss://redis.example:6379/0",
        REDIS_PASSWORD="unit-test-secret",  # pragma: allowlist secret
    )
    shared_app = MagicMock()
    shared_app.state.rate_limiter = RateLimiter(shared_settings, shared_store)
    shared_registry = get_readiness_check_registry(
        Request({"type": "http", "app": shared_app}),
        database_check,
    )
    assert [definition.name for definition in shared_registry.definitions()] == ["database", "redis"]
    redis_check = shared_registry.definitions()[1].check

    async def run_redis_check() -> None:
        await redis_check()

    asyncio.run(run_redis_check())


def test_app_lifespan_closes_the_limiter() -> None:
    limiter = MagicMock()
    limiter.aclose = AsyncMock()

    async def run_lifespan() -> None:
        test_app = FastAPI()
        test_app.state.rate_limit_settings = RateLimitSettings()
        with patch("app.core.setup.factory.build_rate_limiter", return_value=limiter):
            async with app_lifespan(test_app):
                assert test_app.state.rate_limiter is limiter

    asyncio.run(run_lifespan())
    limiter.aclose.assert_awaited_once_with()


def test_login_route_enforces_exact_limit_and_starts_a_new_window(
    installed_memory_limiter: tuple[TestClient, FakeClock],
) -> None:
    client, clock = installed_memory_limiter
    responses = [
        client.post(
            "/v1/token",
            data={"username": "unknown", "password": "WrongPass1"},  # pragma: allowlist secret
        )
        for _ in range(10)
    ]

    assert all(response.status_code == 401 for response in responses)
    assert responses[-1].headers[RATE_LIMIT_HEADER] == "10"
    assert responses[-1].headers[RATE_LIMIT_REMAINING_HEADER] == "0"
    exhausted = client.post(
        "/v1/token",
        data={"username": "unknown", "password": "WrongPass1"},  # pragma: allowlist secret
    )
    assert exhausted.status_code == 429
    assert exhausted.json()["code"] == "rate_limited"
    for header in (
        *(
            RATE_LIMIT_HEADER,
            RATE_LIMIT_REMAINING_HEADER,
            RATE_LIMIT_RESET_HEADER,
        ),
        RETRY_AFTER_HEADER,
    ):
        assert exhausted.headers[header].isdigit()

    clock.advance(60)
    assert (
        client.post(
            "/v1/token",
            data={"username": "unknown", "password": "WrongPass1"},  # pragma: allowlist secret
        ).status_code
        == 401
    )


def test_register_route_enforces_exact_limit_and_new_window(
    installed_memory_limiter: tuple[TestClient, FakeClock],
) -> None:
    client, clock = installed_memory_limiter
    payload = {"username": "admin", "password": "StrongPass1"}  # pragma: allowlist secret

    assert [client.post("/v1/users/register", json=payload).status_code for _ in range(5)] == [409] * 5
    exhausted = client.post("/v1/users/register", json=payload)
    assert exhausted.status_code == 429
    assert exhausted.json()["code"] == "rate_limited"

    clock.advance(60)
    assert client.post("/v1/users/register", json=payload).status_code == 409


def test_auth_route_fails_closed_on_store_outage(mock_client: TestClient) -> None:
    original = app.state.rate_limiter
    limiter = RateLimiter(RateLimitSettings(), UnavailableStore())
    app.state.rate_limiter = limiter
    try:
        response = mock_client.post(
            "/v1/token",
            data={"username": "admin", "password": "admin123"},  # pragma: allowlist secret
        )
    finally:
        app.state.rate_limiter = original

    assert response.status_code == 503
    assert response.json()["code"] == "service_unavailable"
    assert response.json()["meta"] == {"dependency": "rate_limit_store"}
    assert response.headers["X-Request-ID"] == response.json()["request_id"]


def test_auth_route_skips_store_when_explicitly_disabled(mock_client: TestClient) -> None:
    original = app.state.rate_limiter
    limiter = _memory_limiter(FakeClock(), enabled=False)
    app.state.rate_limiter = limiter
    try:
        response = mock_client.post(
            "/v1/token",
            data={"username": "admin", "password": "admin123"},  # pragma: allowlist secret
        )
    finally:
        app.state.rate_limiter = original

    assert response.status_code == 200
    assert RATE_LIMIT_HEADER not in response.headers


def test_openapi_describes_rate_limit_errors_and_numeric_headers() -> None:
    schema = app.openapi()
    for path in ("/v1/token", "/v1/users/register"):
        responses = schema["paths"][path]["post"]["responses"]
        assert {"429", "503"}.issubset(responses)
        quota_headers = responses["429"]["headers"]
        for header in (
            RATE_LIMIT_HEADER,
            RATE_LIMIT_REMAINING_HEADER,
            RATE_LIMIT_RESET_HEADER,
            RETRY_AFTER_HEADER,
        ):
            assert quota_headers[header]["schema"]["type"] == "integer"


def test_rate_limit_settings_enforce_production_topology_and_authentication(tmp_path: Path) -> None:
    assert RateLimitSettings().RATE_LIMIT_LOGIN == 10
    assert RateLimitSettings().RATE_LIMIT_REGISTER == 5
    assert RateLimitSettings().RATE_LIMIT_WINDOW_SECONDS == 60
    assert RateLimitSettings().REDIS_TIMEOUT_SECONDS == 2.0
    assert RateLimitSettings(RATE_LIMIT_ENABLED=False).RATE_LIMIT_ENABLED is False

    for invalid_timeout in (0, 30.1):
        with pytest.raises(ValidationError):
            RateLimitSettings(REDIS_TIMEOUT_SECONDS=invalid_timeout)

    with pytest.raises(ValidationError, match="explicit settings"):
        RateLimitSettings(APP_ENV="production")
    with pytest.raises(ValidationError, match="cannot be disabled"):
        RateLimitSettings(
            APP_ENV="production",
            RATE_LIMIT_ENABLED=False,
            RATE_LIMIT_STORAGE="redis",
            RATE_LIMIT_LOGIN=10,
            RATE_LIMIT_REGISTER=5,
            RATE_LIMIT_WINDOW_SECONDS=60,
            REDIS_URL="rediss://redis.example:6379/0",
            REDIS_PASSWORD="unit-test-secret",  # pragma: allowlist secret
        )
    with pytest.raises(ValidationError, match="shared Redis"):
        RateLimitSettings(
            APP_ENV="production",
            RATE_LIMIT_ENABLED=True,
            RATE_LIMIT_STORAGE="memory",
            RATE_LIMIT_LOGIN=10,
            RATE_LIMIT_REGISTER=5,
            RATE_LIMIT_WINDOW_SECONDS=60,
            REDIS_URL="rediss://redis.example:6379/0",
        )
    with pytest.raises(ValidationError, match="REDIS_PASSWORD"):
        RateLimitSettings(RATE_LIMIT_STORAGE="redis", REDIS_URL="rediss://redis.example:6379/0")
    with pytest.raises(ValidationError, match="REDIS_URL is required"):
        RateLimitSettings(RATE_LIMIT_STORAGE="redis", REDIS_PASSWORD="unit-test-secret")  # pragma: allowlist secret
    with pytest.raises(ValidationError, match="Plaintext Redis"):
        RateLimitSettings(
            RATE_LIMIT_STORAGE="redis",
            REDIS_URL="redis://redis:6379/0",
            REDIS_PASSWORD="unit-test-secret",  # pragma: allowlist secret
        )
    with pytest.raises(ValidationError, match="must not contain credentials"):
        RateLimitSettings(
            RATE_LIMIT_STORAGE="redis",
            REDIS_URL="rediss://user:secret@redis.example:6379/0",  # pragma: allowlist secret
            REDIS_PASSWORD="unit-test-secret",  # pragma: allowlist secret
        )

    invalid_urls = (
        "",
        "https://redis.example:6379/0",
        "rediss://redis.example:6379/0?timeout=1",
        "rediss://redis.example:6379/cache",
        "rediss://redis.example:not-a-port/0",
    )
    for redis_url in invalid_urls:
        with pytest.raises(ValidationError):
            RateLimitSettings(
                RATE_LIMIT_STORAGE="redis",
                REDIS_URL=redis_url,
                REDIS_PASSWORD="unit-test-secret",  # pragma: allowlist secret
            )

    for field, value in (
        ("RATE_LIMIT_STORAGE", "unsupported"),
        ("RATE_LIMIT_NAMESPACE", "invalid namespace"),
    ):
        with pytest.raises(ValidationError):
            RateLimitSettings(**cast(Any, {field: value}))

    with pytest.raises(ValidationError, match="only one"):
        RateLimitSettings(
            RATE_LIMIT_STORAGE="redis",
            REDIS_URL="rediss://redis.example:6379/0",
            REDIS_PASSWORD="unit-test-secret",  # pragma: allowlist secret
            REDIS_PASSWORD_FILE=tmp_path / "also-secret",
        )
    with pytest.raises(ValidationError, match="cannot be empty"):
        RateLimitSettings(
            RATE_LIMIT_STORAGE="redis",
            REDIS_URL="rediss://redis.example:6379/0",
            REDIS_PASSWORD="",
        )
    with pytest.raises(ValidationError, match="readable"):
        RateLimitSettings(
            RATE_LIMIT_STORAGE="redis",
            REDIS_URL="rediss://redis.example:6379/0",
            REDIS_PASSWORD_FILE=tmp_path / "missing-secret",
        )
    empty_secret = tmp_path / "empty-secret"
    empty_secret.write_text("\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="cannot be empty"):
        RateLimitSettings(
            RATE_LIMIT_STORAGE="redis",
            REDIS_URL="rediss://redis.example:6379/0",
            REDIS_PASSWORD_FILE=empty_secret,
        )

    secret_file = tmp_path / "redis-password"
    secret_file.write_text("file-secret\n", encoding="utf-8")  # pragma: allowlist secret
    settings = RateLimitSettings(
        APP_ENV="staging",
        RATE_LIMIT_ENABLED=True,
        RATE_LIMIT_STORAGE="redis",
        RATE_LIMIT_LOGIN=10,
        RATE_LIMIT_REGISTER=5,
        RATE_LIMIT_WINDOW_SECONDS=60,
        REDIS_URL="redis://redis:6379/0",
        REDIS_PASSWORD_FILE=secret_file,
        REDIS_ALLOW_PLAINTEXT=True,
    )
    assert settings.redis_password_value() == "file-secret"  # pragma: allowlist secret
    assert "file-secret" not in repr(settings)  # pragma: allowlist secret

    assert RateLimitSettings(REDIS_URL="   ").REDIS_URL is None
    with pytest.raises(RuntimeError, match="not configured"):
        RateLimitSettings().redis_password_value()
