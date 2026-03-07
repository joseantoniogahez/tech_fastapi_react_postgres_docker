import asyncio
from unittest.mock import AsyncMock, MagicMock

from starlette.requests import Request

from app.core.setup.dependencies import get_outbox_repository, get_outbox_service, get_request_permission_scope_cache
from app.features.outbox.repository import OutboxRepository
from app.features.outbox.service import OutboxService


def _request(path: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "http_version": "1.1",
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }
    )


def test_get_request_permission_scope_cache_reuses_request_state_cache() -> None:
    request = _request("/permission-cache")

    async def run_test() -> None:
        first_cache = await get_request_permission_scope_cache(request)
        first_cache[(10, "roles:manage")] = "any"

        second_cache = await get_request_permission_scope_cache(request)
        assert second_cache is first_cache
        assert second_cache[(10, "roles:manage")] == "any"

    asyncio.run(run_test())


def test_get_outbox_repository_builds_outbox_repository() -> None:
    session = MagicMock()

    async def run_test() -> None:
        repository = await get_outbox_repository(session)

        assert isinstance(repository, OutboxRepository)
        assert repository.session is session

    asyncio.run(run_test())


def test_get_outbox_service_builds_outbox_service() -> None:
    outbox_repository = MagicMock()
    unit_of_work = MagicMock()
    unit_of_work.__aenter__ = AsyncMock(return_value=unit_of_work)
    unit_of_work.__aexit__ = AsyncMock(return_value=None)

    async def run_test() -> None:
        service = await get_outbox_service(outbox_repository=outbox_repository, unit_of_work=unit_of_work)

        assert isinstance(service, OutboxService)
        assert service.outbox_repository is outbox_repository
        assert service.unit_of_work is unit_of_work

    asyncio.run(run_test())
