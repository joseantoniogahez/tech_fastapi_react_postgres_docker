import asyncio
from datetime import UTC, datetime
from http import HTTPStatus

from starlette.testclient import TestClient

from app.core.authorization import PermissionId
from app.features.audit_log.models import AuditLogEntry
from utils.testing_support.api_assertions import assert_error_response
from utils.testing_support.database import MockDatabase


def _auth_headers(mock_client: TestClient, username: str, password: str) -> dict[str, str]:
    response = mock_client.post("/v1/token", data={"username": username, "password": password})
    assert response.status_code == HTTPStatus.OK
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _admin_headers(mock_client: TestClient) -> dict[str, str]:
    return _auth_headers(mock_client, "admin", "admin123")


async def _seed_audit_log_entries(mock_database: MockDatabase) -> None:
    async with mock_database.Session() as session, session.begin():
        session.add_all(
            [
                AuditLogEntry(
                    actor_user_id=1,
                    action="user.created",
                    resource_type="user",
                    resource_id="3",
                    summary="Created user reader_user",
                    created_at=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
                    updated_at=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
                ),
                AuditLogEntry(
                    actor_user_id=1,
                    action="user.updated",
                    resource_type="user",
                    resource_id="3",
                    summary="Updated user reader_user",
                    created_at=datetime(2026, 5, 1, 12, 5, tzinfo=UTC),
                    updated_at=datetime(2026, 5, 1, 12, 5, tzinfo=UTC),
                ),
            ]
        )


def test_admin_can_list_audit_log_entries(mock_client: TestClient, mock_database: MockDatabase) -> None:
    asyncio.run(_seed_audit_log_entries(mock_database))

    response = mock_client.get("/v1/audit-log", headers=_admin_headers(mock_client))

    assert response.status_code == HTTPStatus.OK
    entries = response.json()
    assert [entry["action"] for entry in entries] == ["user.updated", "user.created"]
    assert entries[0]["actor_user_id"] == 1
    assert entries[0]["resource_type"] == "user"
    assert entries[0]["resource_id"] == "3"
    assert entries[0]["summary"] == "Updated user reader_user"
    assert entries[0]["created_at"].startswith("2026-05-01T12:05:00")


def test_audit_log_requires_read_permission(mock_client: TestClient) -> None:
    reader_headers = _auth_headers(mock_client, "reader_user", "reader123")

    response = mock_client.get("/v1/audit-log", headers=reader_headers)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert_error_response(
        response,
        detail=f"Missing required permission: {PermissionId.AUDIT_LOG_READ}",
        status_code=HTTPStatus.FORBIDDEN,
        code="forbidden",
        meta={"permission_id": PermissionId.AUDIT_LOG_READ},
    )
