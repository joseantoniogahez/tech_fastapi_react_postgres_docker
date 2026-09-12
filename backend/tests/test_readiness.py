import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.requests import Request

from app.core.config.settings import DatabaseSettings, ReadinessSettings
from app.core.setup.dependencies import (
    get_database_readiness_check,
    get_readiness_check_registry,
    get_readiness_service,
    get_readiness_settings,
)
from app.features.health.schemas import ReadinessStatus
from app.features.health.service import ReadinessCheckDefinition, ReadinessCheckRegistry, ReadinessService


async def _successful_check() -> None:
    return None


def test_readiness_registry_validates_unique_names_and_sorts_definitions() -> None:
    registry = ReadinessCheckRegistry(
        [
            ReadinessCheckDefinition(name="search", check=_successful_check),
            ReadinessCheckDefinition(name="database", check=_successful_check),
        ]
    )

    assert [definition.name for definition in registry.definitions()] == ["database", "search"]

    with pytest.raises(ValueError, match="already registered"):
        registry.register("database", _successful_check)
    with pytest.raises(ValueError, match="lowercase snake_case"):
        registry.register("Invalid-Name", _successful_check)


@pytest.mark.parametrize(
    ("timeout_seconds", "max_concurrency", "message"),
    [
        (0.0, 1, "timeout"),
        (1.0, 0, "concurrency"),
    ],
)
def test_readiness_service_rejects_invalid_runtime_limits(
    timeout_seconds: float,
    max_concurrency: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        ReadinessService(
            ReadinessCheckRegistry(),
            timeout_seconds=timeout_seconds,
            max_concurrency=max_concurrency,
        )


def test_readiness_service_reports_safe_results_in_deterministic_order() -> None:
    async def unavailable_check() -> None:
        raise RuntimeError("postgresql://user:password@private-host/internal")  # pragma: allowlist secret

    registry = ReadinessCheckRegistry()
    registry.register("search", _successful_check)
    registry.register("database", unavailable_check)
    service = ReadinessService(registry, timeout_seconds=1.0, max_concurrency=2)

    result = asyncio.run(service.evaluate())

    assert result.status == ReadinessStatus.UNAVAILABLE
    assert [(check.name, check.status) for check in result.checks] == [
        ("database", ReadinessStatus.UNAVAILABLE),
        ("search", ReadinessStatus.OK),
    ]
    assert "private-host" not in result.model_dump_json()
    assert "password" not in result.model_dump_json()


def test_readiness_service_bounds_concurrency_and_times_out_checks() -> None:
    active = 0
    peak = 0

    async def tracked_check() -> None:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1

    registry = ReadinessCheckRegistry()
    for name in ("database", "jobs", "search"):
        registry.register(name, tracked_check)
    service = ReadinessService(registry, timeout_seconds=1.0, max_concurrency=2)

    result = asyncio.run(service.evaluate())

    assert peak == 2
    assert result.status == ReadinessStatus.OK

    async def slow_check() -> None:
        await asyncio.sleep(0.05)

    timeout_registry = ReadinessCheckRegistry([ReadinessCheckDefinition("database", slow_check)])
    timeout_result = asyncio.run(
        ReadinessService(timeout_registry, timeout_seconds=0.001, max_concurrency=1).evaluate()
    )
    assert timeout_result.status == ReadinessStatus.UNAVAILABLE


def test_readiness_service_treats_an_empty_registry_as_unavailable() -> None:
    result = asyncio.run(ReadinessService(ReadinessCheckRegistry(), timeout_seconds=1.0, max_concurrency=1).evaluate())

    assert result.status == ReadinessStatus.UNAVAILABLE
    assert result.checks == []


def test_database_readiness_check_executes_a_neutral_probe() -> None:
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=session)
    session_context.__aexit__ = AsyncMock(return_value=None)
    session_factory = MagicMock(spec=async_sessionmaker)
    session_factory.return_value = session_context

    with patch("app.core.setup.dependencies.get_async_session_factory", return_value=session_factory):
        check = get_database_readiness_check()

        async def run_check() -> None:
            await check()

        asyncio.run(run_check())

    statement = session.execute.await_args.args[0]
    assert str(statement) == "SELECT 1"


def test_readiness_dependency_graph_registers_database_and_applies_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("READINESS_TIMEOUT_SECONDS", "1.25")
    monkeypatch.setenv("READINESS_MAX_CONCURRENCY", "3")
    settings = get_readiness_settings()
    request = Request({"type": "http", "app": MagicMock()})
    registry = get_readiness_check_registry(request, _successful_check)
    service = get_readiness_service(registry, settings)

    assert isinstance(settings, ReadinessSettings)
    assert [definition.name for definition in registry.definitions()] == ["database"]
    assert asyncio.run(service.evaluate()).status == ReadinessStatus.OK


@pytest.mark.parametrize("app_env", ["staging", "production", "prod"])
def test_database_settings_require_postgresql_in_production_like_environments(app_env: str) -> None:
    with pytest.raises(ValidationError, match="PostgreSQL is required"):
        DatabaseSettings(APP_ENV=app_env, DB_TYPE="sqlite+aiosqlite")


def test_database_settings_require_postgresql_when_compose_contract_is_enabled() -> None:
    with pytest.raises(ValidationError, match="PostgreSQL is required"):
        DatabaseSettings(DB_REQUIRE_POSTGRESQL=True, DB_TYPE="sqlite+aiosqlite")

    settings = DatabaseSettings(
        APP_ENV="development",
        DB_REQUIRE_POSTGRESQL=True,
        DB_TYPE=" PostgreSQL+AsyncPG ",
    )
    assert settings.DB_TYPE == "postgresql+asyncpg"


def test_readiness_and_database_settings_reject_invalid_values() -> None:
    with pytest.raises(ValidationError):
        ReadinessSettings(READINESS_TIMEOUT_SECONDS=31)
    with pytest.raises(ValidationError):
        ReadinessSettings(READINESS_MAX_CONCURRENCY=33)
    with pytest.raises(ValidationError, match="DB_TYPE cannot be empty"):
        DatabaseSettings(DB_TYPE="   ")
