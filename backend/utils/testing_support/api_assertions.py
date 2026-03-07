from typing import Any

from app.core.errors.setup.handlers import REQUEST_ID_HEADER


def assert_error_response(
    response: Any,
    *,
    detail: str,
    status_code: int,
    code: str,
    meta: Any | None = None,
) -> None:
    payload = response.json()

    assert payload["detail"] == detail
    assert payload["status"] == status_code
    assert payload["code"] == code
    if meta is None:
        assert "meta" not in payload
    else:
        assert payload["meta"] == meta

    assert isinstance(payload.get("request_id"), str)
    assert payload["request_id"]
    assert response.headers[REQUEST_ID_HEADER] == payload["request_id"]
