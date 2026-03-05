import asyncio
from http import HTTPStatus

from sqlalchemy import select
from starlette.testclient import TestClient

from app.authorization import PERMISSION_SPECS, PermissionId
from app.models.role import Role
from app.models.role_inheritance import RoleInheritance
from app.models.role_permission import RolePermission
from app.models.user_role import UserRole
from utils.testing_support.api_assertions import assert_error_response
from utils.testing_support.database import MockDatabase


def _auth_headers(mock_client: TestClient, username: str, password: str) -> dict[str, str]:
    response = mock_client.post("/v1/token", data={"username": username, "password": password})
    assert response.status_code == HTTPStatus.OK
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _admin_headers(mock_client: TestClient) -> dict[str, str]:
    return _auth_headers(mock_client, "admin", "admin123")


async def _get_role_id(mock_database: MockDatabase, role_name: str) -> int | None:
    async with mock_database.Session() as session:
        return await session.scalar(select(Role.id).where(Role.name == role_name))


async def _get_role_permission_scope(
    mock_database: MockDatabase,
    *,
    role_id: int,
    permission_id: str,
) -> str | None:
    async with mock_database.Session() as session:
        return await session.scalar(
            select(RolePermission.scope).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )


async def _user_role_exists(
    mock_database: MockDatabase,
    *,
    user_id: int,
    role_id: int,
) -> bool:
    async with mock_database.Session() as session:
        user_role_id = await session.scalar(
            select(UserRole.user_id).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        )
        return user_role_id is not None


async def _role_inheritance_exists(
    mock_database: MockDatabase,
    *,
    role_id: int,
    parent_role_id: int,
) -> bool:
    async with mock_database.Session() as session:
        inheritance_role_id = await session.scalar(
            select(RoleInheritance.role_id).where(
                RoleInheritance.role_id == role_id,
                RoleInheritance.parent_role_id == parent_role_id,
            )
        )
        return inheritance_role_id is not None


def test_admin_can_list_roles_with_permissions(mock_client: TestClient) -> None:
    response = mock_client.get("/v1/rbac/roles", headers=_admin_headers(mock_client))

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    by_name = {role["name"]: role for role in payload}

    assert "admin_role" in by_name
    assert "reader_role" in by_name

    admin_permissions = {permission["id"]: permission["scope"] for permission in by_name["admin_role"]["permissions"]}
    assert admin_permissions[PermissionId.BOOK_CREATE] == "any"
    assert admin_permissions[PermissionId.ROLE_MANAGE] == "any"
    assert admin_permissions[PermissionId.ROLE_PERMISSION_MANAGE] == "any"
    assert admin_permissions[PermissionId.USER_ROLE_MANAGE] == "any"
    assert by_name["reader_role"]["permissions"] == []


def test_admin_can_list_permission_catalog(mock_client: TestClient) -> None:
    response = mock_client.get("/v1/rbac/permissions", headers=_admin_headers(mock_client))

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    permission_ids = [permission["id"] for permission in payload]

    assert permission_ids == sorted(permission_id for permission_id, _ in PERMISSION_SPECS)


def test_reader_cannot_list_roles_without_roles_manage_permission(mock_client: TestClient) -> None:
    response = mock_client.get(
        "/v1/rbac/roles",
        headers=_auth_headers(mock_client, "reader_user", "reader123"),
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert_error_response(
        response,
        detail=f"Missing required permission: {PermissionId.ROLE_MANAGE}",
        status_code=HTTPStatus.FORBIDDEN,
        code="forbidden",
        meta={"permission_id": PermissionId.ROLE_MANAGE},
    )


def test_reader_cannot_manage_role_permissions_without_permission(mock_client: TestClient) -> None:
    response = mock_client.put(
        f"/v1/rbac/roles/1/permissions/{PermissionId.BOOK_CREATE}",
        json={"scope": "any"},
        headers=_auth_headers(mock_client, "reader_user", "reader123"),
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert_error_response(
        response,
        detail=f"Missing required permission: {PermissionId.ROLE_PERMISSION_MANAGE}",
        status_code=HTTPStatus.FORBIDDEN,
        code="forbidden",
        meta={"permission_id": PermissionId.ROLE_PERMISSION_MANAGE},
    )


def test_reader_cannot_manage_user_role_assignments_without_permission(
    mock_client: TestClient,
) -> None:
    response = mock_client.put(
        "/v1/rbac/users/3/roles/2",
        headers=_auth_headers(mock_client, "reader_user", "reader123"),
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert_error_response(
        response,
        detail=f"Missing required permission: {PermissionId.USER_ROLE_MANAGE}",
        status_code=HTTPStatus.FORBIDDEN,
        code="forbidden",
        meta={"permission_id": PermissionId.USER_ROLE_MANAGE},
    )


def test_admin_can_create_and_rename_role(mock_client: TestClient) -> None:
    create_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": " Catalog_Curator "},
        headers=_admin_headers(mock_client),
    )

    assert create_response.status_code == HTTPStatus.CREATED
    assert create_response.json()["name"] == "catalog_curator"

    role_id = create_response.json()["id"]
    update_response = mock_client.put(
        f"/v1/rbac/roles/{role_id}",
        json={"name": "Catalog_Manager"},
        headers=_admin_headers(mock_client),
    )

    assert update_response.status_code == HTTPStatus.OK
    assert update_response.json()["id"] == role_id
    assert update_response.json()["name"] == "catalog_manager"


def test_admin_cannot_create_duplicate_role_name(mock_client: TestClient) -> None:
    response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "admin_role"},
        headers=_admin_headers(mock_client),
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert_error_response(
        response,
        detail="Role name already exists",
        status_code=HTTPStatus.CONFLICT,
        code="conflict",
        meta={"name": "admin_role"},
    )


def test_admin_cannot_rename_role_to_existing_name(mock_client: TestClient) -> None:
    create_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "rename_conflict_role"},
        headers=_admin_headers(mock_client),
    )
    assert create_response.status_code == HTTPStatus.CREATED

    role_id = create_response.json()["id"]
    response = mock_client.put(
        f"/v1/rbac/roles/{role_id}",
        json={"name": "admin_role"},
        headers=_admin_headers(mock_client),
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert_error_response(
        response,
        detail="Role name already exists",
        status_code=HTTPStatus.CONFLICT,
        code="conflict",
        meta={"name": "admin_role"},
    )


def test_admin_can_assign_and_remove_role_permission(
    mock_client: TestClient,
    mock_database: MockDatabase,
) -> None:
    create_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "scope_editor"},
        headers=_admin_headers(mock_client),
    )
    assert create_response.status_code == HTTPStatus.CREATED
    role_id = create_response.json()["id"]

    assign_response = mock_client.put(
        f"/v1/rbac/roles/{role_id}/permissions/{PermissionId.BOOK_UPDATE}",
        json={"scope": "tenant"},
        headers=_admin_headers(mock_client),
    )

    assert assign_response.status_code == HTTPStatus.OK
    assert assign_response.json() == {
        "id": PermissionId.BOOK_UPDATE,
        "name": "Update books",
        "scope": "tenant",
    }
    assert (
        asyncio.run(
            _get_role_permission_scope(
                mock_database,
                role_id=role_id,
                permission_id=PermissionId.BOOK_UPDATE,
            )
        )
        == "tenant"
    )

    remove_response = mock_client.delete(
        f"/v1/rbac/roles/{role_id}/permissions/{PermissionId.BOOK_UPDATE}",
        headers=_admin_headers(mock_client),
    )

    assert remove_response.status_code == HTTPStatus.NO_CONTENT
    assert (
        asyncio.run(
            _get_role_permission_scope(
                mock_database,
                role_id=role_id,
                permission_id=PermissionId.BOOK_UPDATE,
            )
        )
        is None
    )


def test_admin_can_update_existing_role_permission_scope(mock_client: TestClient) -> None:
    create_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "scope_upgrade_role"},
        headers=_admin_headers(mock_client),
    )
    assert create_response.status_code == HTTPStatus.CREATED

    role_id = create_response.json()["id"]
    first_response = mock_client.put(
        f"/v1/rbac/roles/{role_id}/permissions/{PermissionId.BOOK_CREATE}",
        json={"scope": "own"},
        headers=_admin_headers(mock_client),
    )
    assert first_response.status_code == HTTPStatus.OK

    second_response = mock_client.put(
        f"/v1/rbac/roles/{role_id}/permissions/{PermissionId.BOOK_CREATE}",
        json={"scope": "tenant"},
        headers=_admin_headers(mock_client),
    )

    assert second_response.status_code == HTTPStatus.OK
    assert second_response.json() == {
        "id": PermissionId.BOOK_CREATE,
        "name": "Create books",
        "scope": "tenant",
    }


def test_admin_can_assign_and_remove_role_inheritance(
    mock_client: TestClient,
    mock_database: MockDatabase,
) -> None:
    parent_role_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "catalog_parent"},
        headers=_admin_headers(mock_client),
    )
    assert parent_role_response.status_code == HTTPStatus.CREATED
    parent_role_id = parent_role_response.json()["id"]

    child_role_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "catalog_child"},
        headers=_admin_headers(mock_client),
    )
    assert child_role_response.status_code == HTTPStatus.CREATED
    child_role_id = child_role_response.json()["id"]

    assign_permission_response = mock_client.put(
        f"/v1/rbac/roles/{parent_role_id}/permissions/{PermissionId.BOOK_CREATE}",
        json={"scope": "tenant"},
        headers=_admin_headers(mock_client),
    )
    assert assign_permission_response.status_code == HTTPStatus.OK

    assign_inheritance_response = mock_client.put(
        f"/v1/rbac/roles/{child_role_id}/inherits/{parent_role_id}",
        headers=_admin_headers(mock_client),
    )
    assert assign_inheritance_response.status_code == HTTPStatus.NO_CONTENT
    assert (
        asyncio.run(
            _role_inheritance_exists(
                mock_database,
                role_id=child_role_id,
                parent_role_id=parent_role_id,
            )
        )
        is True
    )

    list_roles_response = mock_client.get("/v1/rbac/roles", headers=_admin_headers(mock_client))
    assert list_roles_response.status_code == HTTPStatus.OK
    by_name = {role["name"]: role for role in list_roles_response.json()}
    child_permissions = {
        permission["id"]: permission["scope"] for permission in by_name["catalog_child"]["permissions"]
    }
    assert child_permissions[PermissionId.BOOK_CREATE] == "tenant"

    remove_inheritance_response = mock_client.delete(
        f"/v1/rbac/roles/{child_role_id}/inherits/{parent_role_id}",
        headers=_admin_headers(mock_client),
    )
    assert remove_inheritance_response.status_code == HTTPStatus.NO_CONTENT
    assert (
        asyncio.run(
            _role_inheritance_exists(
                mock_database,
                role_id=child_role_id,
                parent_role_id=parent_role_id,
            )
        )
        is False
    )


def test_assign_role_inheritance_rejects_self_inheritance(mock_client: TestClient) -> None:
    role_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "self_inherit_role"},
        headers=_admin_headers(mock_client),
    )
    assert role_response.status_code == HTTPStatus.CREATED
    role_id = role_response.json()["id"]

    response = mock_client.put(
        f"/v1/rbac/roles/{role_id}/inherits/{role_id}",
        headers=_admin_headers(mock_client),
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert_error_response(
        response,
        detail="Role cannot inherit from itself",
        status_code=HTTPStatus.BAD_REQUEST,
        code="invalid_input",
    )


def test_assign_role_inheritance_rejects_cycles(mock_client: TestClient) -> None:
    parent_role_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "cycle_parent"},
        headers=_admin_headers(mock_client),
    )
    assert parent_role_response.status_code == HTTPStatus.CREATED
    parent_role_id = parent_role_response.json()["id"]

    child_role_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "cycle_child"},
        headers=_admin_headers(mock_client),
    )
    assert child_role_response.status_code == HTTPStatus.CREATED
    child_role_id = child_role_response.json()["id"]

    first_link_response = mock_client.put(
        f"/v1/rbac/roles/{child_role_id}/inherits/{parent_role_id}",
        headers=_admin_headers(mock_client),
    )
    assert first_link_response.status_code == HTTPStatus.NO_CONTENT

    cycle_response = mock_client.put(
        f"/v1/rbac/roles/{parent_role_id}/inherits/{child_role_id}",
        headers=_admin_headers(mock_client),
    )
    assert cycle_response.status_code == HTTPStatus.CONFLICT
    assert_error_response(
        cycle_response,
        detail="Role inheritance cycle detected",
        status_code=HTTPStatus.CONFLICT,
        code="conflict",
        meta={"role_id": parent_role_id, "parent_role_id": child_role_id},
    )


def test_remove_missing_role_inheritance_is_noop(mock_client: TestClient) -> None:
    parent_role_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "inherit_parent_noop"},
        headers=_admin_headers(mock_client),
    )
    assert parent_role_response.status_code == HTTPStatus.CREATED
    parent_role_id = parent_role_response.json()["id"]

    child_role_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "inherit_child_noop"},
        headers=_admin_headers(mock_client),
    )
    assert child_role_response.status_code == HTTPStatus.CREATED
    child_role_id = child_role_response.json()["id"]

    response = mock_client.delete(
        f"/v1/rbac/roles/{child_role_id}/inherits/{parent_role_id}",
        headers=_admin_headers(mock_client),
    )
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""


def test_assign_role_permission_rejects_invalid_scope(mock_client: TestClient) -> None:
    create_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "invalid_scope_role"},
        headers=_admin_headers(mock_client),
    )
    assert create_response.status_code == HTTPStatus.CREATED

    role_id = create_response.json()["id"]
    response = mock_client.put(
        f"/v1/rbac/roles/{role_id}/permissions/{PermissionId.BOOK_CREATE}",
        json={"scope": "regional"},
        headers=_admin_headers(mock_client),
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert_error_response(
        response,
        detail="Invalid permission scope 'regional'. Expected one of ['any', 'own', 'tenant'].",
        status_code=HTTPStatus.BAD_REQUEST,
        code="invalid_input",
    )


def test_assign_role_permission_returns_not_found_for_unknown_permission(
    mock_client: TestClient,
) -> None:
    response = mock_client.put(
        "/v1/rbac/roles/1/permissions/books:read",
        json={"scope": "any"},
        headers=_admin_headers(mock_client),
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert_error_response(
        response,
        detail="Permission books:read not found",
        status_code=HTTPStatus.NOT_FOUND,
        code="not_found",
        meta={"permission_id": "books:read"},
    )


def test_remove_missing_role_permission_is_noop(mock_client: TestClient) -> None:
    create_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "empty_permission_role"},
        headers=_admin_headers(mock_client),
    )
    assert create_response.status_code == HTTPStatus.CREATED

    role_id = create_response.json()["id"]
    response = mock_client.delete(
        f"/v1/rbac/roles/{role_id}/permissions/{PermissionId.BOOK_DELETE}",
        headers=_admin_headers(mock_client),
    )

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""


def test_admin_can_assign_and_remove_user_role(
    mock_client: TestClient,
    mock_database: MockDatabase,
) -> None:
    create_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "reader_delegate"},
        headers=_admin_headers(mock_client),
    )
    assert create_response.status_code == HTTPStatus.CREATED
    role_id = create_response.json()["id"]

    assign_response = mock_client.put(
        f"/v1/rbac/users/3/roles/{role_id}",
        headers=_admin_headers(mock_client),
    )

    assert assign_response.status_code == HTTPStatus.OK
    assert assign_response.json() == {
        "user_id": 3,
        "role_id": role_id,
    }
    assert asyncio.run(_user_role_exists(mock_database, user_id=3, role_id=role_id)) is True

    remove_response = mock_client.delete(
        f"/v1/rbac/users/3/roles/{role_id}",
        headers=_admin_headers(mock_client),
    )

    assert remove_response.status_code == HTTPStatus.NO_CONTENT
    assert asyncio.run(_user_role_exists(mock_database, user_id=3, role_id=role_id)) is False


def test_assign_existing_user_role_is_idempotent(mock_client: TestClient) -> None:
    response = mock_client.put(
        "/v1/rbac/users/3/roles/2",
        headers=_admin_headers(mock_client),
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "user_id": 3,
        "role_id": 2,
    }


def test_assign_user_role_returns_not_found_for_unknown_user(mock_client: TestClient) -> None:
    response = mock_client.put(
        "/v1/rbac/users/999/roles/1",
        headers=_admin_headers(mock_client),
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert_error_response(
        response,
        detail="User 999 not found",
        status_code=HTTPStatus.NOT_FOUND,
        code="not_found",
        meta={"id": 999},
    )


def test_remove_missing_user_role_is_noop(mock_client: TestClient) -> None:
    response = mock_client.delete(
        "/v1/rbac/users/1/roles/2",
        headers=_admin_headers(mock_client),
    )

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""


def test_update_role_returns_not_found_for_missing_role(mock_client: TestClient) -> None:
    response = mock_client.put(
        "/v1/rbac/roles/999",
        json={"name": "missing_role"},
        headers=_admin_headers(mock_client),
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert_error_response(
        response,
        detail="Role 999 not found",
        status_code=HTTPStatus.NOT_FOUND,
        code="not_found",
        meta={"id": 999},
    )


def test_admin_can_delete_role_and_related_assignments(
    mock_client: TestClient,
    mock_database: MockDatabase,
) -> None:
    create_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "transient_admin"},
        headers=_admin_headers(mock_client),
    )
    assert create_response.status_code == HTTPStatus.CREATED
    role_id = create_response.json()["id"]

    assign_permission_response = mock_client.put(
        f"/v1/rbac/roles/{role_id}/permissions/{PermissionId.BOOK_CREATE}",
        json={"scope": "any"},
        headers=_admin_headers(mock_client),
    )
    assert assign_permission_response.status_code == HTTPStatus.OK

    assign_user_role_response = mock_client.put(
        f"/v1/rbac/users/3/roles/{role_id}",
        headers=_admin_headers(mock_client),
    )
    assert assign_user_role_response.status_code == HTTPStatus.OK

    create_inheriting_role_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "transient_inheritor"},
        headers=_admin_headers(mock_client),
    )
    assert create_inheriting_role_response.status_code == HTTPStatus.CREATED
    inheritor_role_id = create_inheriting_role_response.json()["id"]

    assign_inheritance_response = mock_client.put(
        f"/v1/rbac/roles/{inheritor_role_id}/inherits/{role_id}",
        headers=_admin_headers(mock_client),
    )
    assert assign_inheritance_response.status_code == HTTPStatus.NO_CONTENT

    delete_response = mock_client.delete(
        f"/v1/rbac/roles/{role_id}",
        headers=_admin_headers(mock_client),
    )

    assert delete_response.status_code == HTTPStatus.NO_CONTENT
    assert asyncio.run(_get_role_id(mock_database, "transient_admin")) is None
    assert (
        asyncio.run(
            _get_role_permission_scope(
                mock_database,
                role_id=role_id,
                permission_id=PermissionId.BOOK_CREATE,
            )
        )
        is None
    )
    assert asyncio.run(_user_role_exists(mock_database, user_id=3, role_id=role_id)) is False
    assert (
        asyncio.run(_role_inheritance_exists(mock_database, role_id=inheritor_role_id, parent_role_id=role_id)) is False
    )
