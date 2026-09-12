import asyncio
import re
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass

from app.features.health.schemas import ReadinessCheckResponse, ReadinessResponse, ReadinessStatus

ReadinessCheck = Callable[[], Awaitable[None]]
_CHECK_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


@dataclass(frozen=True)
class ReadinessCheckDefinition:
    name: str
    check: ReadinessCheck


class ReadinessCheckRegistry:
    def __init__(self, checks: Iterable[ReadinessCheckDefinition] = ()) -> None:
        self._checks: dict[str, ReadinessCheck] = {}
        for definition in checks:
            self.register(definition.name, definition.check)

    def register(self, name: str, check: ReadinessCheck) -> None:
        if _CHECK_NAME_PATTERN.fullmatch(name) is None:
            raise ValueError("Readiness check names must be lowercase snake_case and at most 64 characters.")
        if name in self._checks:
            raise ValueError(f"Readiness check '{name}' is already registered.")
        self._checks[name] = check

    def definitions(self) -> tuple[ReadinessCheckDefinition, ...]:
        return tuple(ReadinessCheckDefinition(name=name, check=self._checks[name]) for name in sorted(self._checks))


class ReadinessService:
    def __init__(
        self,
        registry: ReadinessCheckRegistry,
        *,
        timeout_seconds: float,
        max_concurrency: int,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("Readiness timeout must be greater than zero.")
        if max_concurrency < 1:
            raise ValueError("Readiness concurrency must be at least one.")
        self._registry = registry
        self._timeout_seconds = timeout_seconds
        self._max_concurrency = max_concurrency

    async def _run_check(
        self,
        definition: ReadinessCheckDefinition,
        semaphore: asyncio.Semaphore,
    ) -> ReadinessCheckResponse:
        status = ReadinessStatus.OK
        try:
            async with semaphore:
                async with asyncio.timeout(self._timeout_seconds):
                    await definition.check()
        except Exception:
            status = ReadinessStatus.UNAVAILABLE
        return ReadinessCheckResponse(name=definition.name, status=status)

    async def evaluate(self) -> ReadinessResponse:
        semaphore = asyncio.Semaphore(self._max_concurrency)
        checks = await asyncio.gather(
            *(self._run_check(definition, semaphore) for definition in self._registry.definitions())
        )
        status = (
            ReadinessStatus.OK
            if checks and all(check.status == ReadinessStatus.OK for check in checks)
            else ReadinessStatus.UNAVAILABLE
        )
        return ReadinessResponse(status=status, checks=list(checks))
