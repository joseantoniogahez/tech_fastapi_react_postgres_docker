import asyncio

from starlette.requests import Request

from app.dependencies.services import get_request_permission_scope_cache


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
        first_cache[(10, "books:update")] = "any"

        second_cache = await get_request_permission_scope_cache(request)
        assert second_cache is first_cache
        assert second_cache[(10, "books:update")] == "any"

    asyncio.run(run_test())
