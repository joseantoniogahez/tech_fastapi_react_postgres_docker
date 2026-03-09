import asyncio
from http import HTTPStatus
from typing import Any

from sqlalchemy import select
from starlette.testclient import TestClient

from app.core.authorization import PERMISSION_SPECS, PermissionId
from app.features.rbac.models import Role, RoleInheritance, RolePermission, UserRole
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


def test_admin_can_list_roles_and_permission_catalog(mock_client: TestClient) -> None:
    roles_response = mock_client.get("/v1/rbac/roles", headers=_admin_headers(mock_client))
    assert roles_response.status_code == HTTPStatus.OK
    by_name = {role["name"]: role for role in roles_response.json()}
    assert "admin_role" in by_name
    assert "reader_role" in by_name
    admin_permissions = {permission["id"]: permission["scope"] for permission in by_name["admin_role"]["permissions"]}
    assert admin_permissions[PermissionId.ROLE_MANAGE] == "any"
    assert admin_permissions[PermissionId.ROLE_PERMISSION_MANAGE] == "any"
    assert admin_permissions[PermissionId.USER_ROLE_MANAGE] == "any"
    assert admin_permissions[PermissionId.USER_MANAGE] == "any"
    assert by_name["admin_role"]["parent_role_ids"] == []
    assert by_name["reader_role"]["permissions"] == []
    assert by_name["reader_role"]["parent_role_ids"] == []

    permissions_response = mock_client.get("/v1/rbac/permissions", headers=_admin_headers(mock_client))
    assert permissions_response.status_code == HTTPStatus.OK
    permission_ids = [permission["id"] for permission in permissions_response.json()]
    assert permission_ids == sorted(permission_id for permission_id, _ in PERMISSION_SPECS)


def test_rbac_admin_endpoints_require_expected_permissions(mock_client: TestClient) -> None:
    reader_headers = _auth_headers(mock_client, "reader_user", "reader123")
    cases: tuple[dict[str, Any], ...] = (
        {
            "method": "GET",
            "path": "/v1/rbac/roles",
            "permission_id": PermissionId.ROLE_MANAGE,
        },
        {
            "method": "GET",
            "path": "/v1/rbac/users",
            "permission_id": PermissionId.USER_MANAGE,
        },
        {
            "method": "PUT",
            "path": f"/v1/rbac/roles/1/permissions/{PermissionId.ROLE_MANAGE}",
            "json": {"scope": "any"},
            "permission_id": PermissionId.ROLE_PERMISSION_MANAGE,
        },
        {
            "method": "PUT",
            "path": "/v1/rbac/users/3",
            "json": {"disabled": True},
            "permission_id": PermissionId.USER_MANAGE,
        },
        {
            "method": "PUT",
            "path": "/v1/rbac/users/3/roles/2",
            "permission_id": PermissionId.USER_ROLE_MANAGE,
        },
        {
            "method": "GET",
            "path": "/v1/rbac/users/3/roles",
            "permission_id": PermissionId.USER_ROLE_MANAGE,
        },
        {
            "method": "GET",
            "path": "/v1/rbac/roles/2/users",
            "permission_id": PermissionId.USER_ROLE_MANAGE,
        },
    )

    for case in cases:
        if case["method"] == "GET":
            response = mock_client.get(case["path"], headers=reader_headers)
        else:
            response = mock_client.put(case["path"], headers=reader_headers, json=case.get("json"))

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert_error_response(
            response,
            detail=f"Missing required permission: {case['permission_id']}",
            status_code=HTTPStatus.FORBIDDEN,
            code="forbidden",
            meta={"permission_id": case["permission_id"]},
        )


def test_role_lifecycle_create_rename_and_delete_cascades(
    mock_client: TestClient,
    mock_database: MockDatabase,
) -> None:
    create_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": " transient_admin "},
        headers=_admin_headers(mock_client),
    )
    assert create_response.status_code == HTTPStatus.CREATED
    role_id = create_response.json()["id"]
    assert create_response.json()["name"] == "transient_admin"

    update_response = mock_client.put(
        f"/v1/rbac/roles/{role_id}",
        json={"name": "transient_admin_v2"},
        headers=_admin_headers(mock_client),
    )
    assert update_response.status_code == HTTPStatus.OK
    assert update_response.json()["name"] == "transient_admin_v2"

    assign_permission_response = mock_client.put(
        f"/v1/rbac/roles/{role_id}/permissions/{PermissionId.USER_ROLE_MANAGE}",
        json={"scope": "any"},
        headers=_admin_headers(mock_client),
    )
    assert assign_permission_response.status_code == HTTPStatus.OK

    assign_user_role_response = mock_client.put(
        f"/v1/rbac/users/3/roles/{role_id}",
        headers=_admin_headers(mock_client),
    )
    assert assign_user_role_response.status_code == HTTPStatus.OK

    inheritor_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "transient_inheritor"},
        headers=_admin_headers(mock_client),
    )
    assert inheritor_response.status_code == HTTPStatus.CREATED
    inheritor_role_id = inheritor_response.json()["id"]

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

    assert asyncio.run(_get_role_id(mock_database, "transient_admin_v2")) is None
    assert (
        asyncio.run(
            _get_role_permission_scope(
                mock_database,
                role_id=role_id,
                permission_id=PermissionId.USER_ROLE_MANAGE,
            )
        )
        is None
    )
    assert asyncio.run(_user_role_exists(mock_database, user_id=3, role_id=role_id)) is False
    assert (
        asyncio.run(
            _role_inheritance_exists(
                mock_database,
                role_id=inheritor_role_id,
                parent_role_id=role_id,
            )
        )
        is False
    )


def test_role_name_conflicts_are_rejected(mock_client: TestClient) -> None:
    create_conflict = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "admin_role"},
        headers=_admin_headers(mock_client),
    )
    assert create_conflict.status_code == HTTPStatus.CONFLICT
    assert_error_response(
        create_conflict,
        detail="Role name already exists",
        status_code=HTTPStatus.CONFLICT,
        code="conflict",
        meta={"name": "admin_role"},
    )

    create_role = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "rename_conflict_role"},
        headers=_admin_headers(mock_client),
    )
    assert create_role.status_code == HTTPStatus.CREATED
    role_id = create_role.json()["id"]

    rename_conflict = mock_client.put(
        f"/v1/rbac/roles/{role_id}",
        json={"name": "admin_role"},
        headers=_admin_headers(mock_client),
    )
    assert rename_conflict.status_code == HTTPStatus.CONFLICT
    assert_error_response(
        rename_conflict,
        detail="Role name already exists",
        status_code=HTTPStatus.CONFLICT,
        code="conflict",
        meta={"name": "admin_role"},
    )


def test_role_permission_management_happy_path(
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

    first_response = mock_client.put(
        f"/v1/rbac/roles/{role_id}/permissions/{PermissionId.USER_ROLE_MANAGE}",
        json={"scope": "own"},
        headers=_admin_headers(mock_client),
    )
    assert first_response.status_code == HTTPStatus.OK

    second_response = mock_client.put(
        f"/v1/rbac/roles/{role_id}/permissions/{PermissionId.USER_ROLE_MANAGE}",
        json={"scope": "tenant"},
        headers=_admin_headers(mock_client),
    )
    assert second_response.status_code == HTTPStatus.OK
    assert second_response.json() == {
        "id": PermissionId.USER_ROLE_MANAGE,
        "name": "Manage user role assignments",
        "scope": "tenant",
    }
    assert (
        asyncio.run(
            _get_role_permission_scope(
                mock_database,
                role_id=role_id,
                permission_id=PermissionId.USER_ROLE_MANAGE,
            )
        )
        == "tenant"
    )

    remove_response = mock_client.delete(
        f"/v1/rbac/roles/{role_id}/permissions/{PermissionId.USER_ROLE_MANAGE}",
        headers=_admin_headers(mock_client),
    )
    assert remove_response.status_code == HTTPStatus.NO_CONTENT
    assert (
        asyncio.run(
            _get_role_permission_scope(
                mock_database,
                role_id=role_id,
                permission_id=PermissionId.USER_ROLE_MANAGE,
            )
        )
        is None
    )


def test_role_permission_rejects_invalid_scope(mock_client: TestClient) -> None:
    create_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "invalid_scope_role"},
        headers=_admin_headers(mock_client),
    )
    assert create_response.status_code == HTTPStatus.CREATED
    role_id = create_response.json()["id"]

    response = mock_client.put(
        f"/v1/rbac/roles/{role_id}/permissions/{PermissionId.ROLE_MANAGE}",
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


def test_role_inheritance_management_happy_path(
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
        f"/v1/rbac/roles/{parent_role_id}/permissions/{PermissionId.ROLE_PERMISSION_MANAGE}",
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
    assert child_permissions[PermissionId.ROLE_PERMISSION_MANAGE] == "tenant"
    assert by_name["catalog_child"]["parent_role_ids"] == [parent_role_id]

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


def test_role_inheritance_rejections_self_and_cycle(mock_client: TestClient) -> None:
    self_role_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "self_inherit_role"},
        headers=_admin_headers(mock_client),
    )
    assert self_role_response.status_code == HTTPStatus.CREATED
    self_role_id = self_role_response.json()["id"]

    self_response = mock_client.put(
        f"/v1/rbac/roles/{self_role_id}/inherits/{self_role_id}",
        headers=_admin_headers(mock_client),
    )
    assert self_response.status_code == HTTPStatus.BAD_REQUEST
    assert_error_response(
        self_response,
        detail="Role cannot inherit from itself",
        status_code=HTTPStatus.BAD_REQUEST,
        code="invalid_input",
    )

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

    first_link = mock_client.put(
        f"/v1/rbac/roles/{child_role_id}/inherits/{parent_role_id}",
        headers=_admin_headers(mock_client),
    )
    assert first_link.status_code == HTTPStatus.NO_CONTENT

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


def test_user_role_management_happy_path(
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
    assert assign_response.json() == {"user_id": 3, "role_id": role_id}
    assert asyncio.run(_user_role_exists(mock_database, user_id=3, role_id=role_id)) is True

    remove_response = mock_client.delete(
        f"/v1/rbac/users/3/roles/{role_id}",
        headers=_admin_headers(mock_client),
    )
    assert remove_response.status_code == HTTPStatus.NO_CONTENT
    assert asyncio.run(_user_role_exists(mock_database, user_id=3, role_id=role_id)) is False


def test_user_role_assignment_visibility_endpoints(mock_client: TestClient) -> None:
    create_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "assignment_visible_role"},
        headers=_admin_headers(mock_client),
    )
    assert create_response.status_code == HTTPStatus.CREATED
    role_id = create_response.json()["id"]

    assign_response = mock_client.put(
        f"/v1/rbac/users/3/roles/{role_id}",
        headers=_admin_headers(mock_client),
    )
    assert assign_response.status_code == HTTPStatus.OK

    list_user_roles_response = mock_client.get(
        "/v1/rbac/users/3/roles",
        headers=_admin_headers(mock_client),
    )
    assert list_user_roles_response.status_code == HTTPStatus.OK
    assert list_user_roles_response.json() == [
        {"id": role_id, "name": "assignment_visible_role"},
        {"id": 2, "name": "reader_role"},
    ]

    list_role_users_response = mock_client.get(
        f"/v1/rbac/roles/{role_id}/users",
        headers=_admin_headers(mock_client),
    )
    assert list_role_users_response.status_code == HTTPStatus.OK
    assert list_role_users_response.json() == [
        {"id": 3, "username": "reader_user", "disabled": False},
    ]


def test_admin_user_management_crud_soft_delete(mock_client: TestClient) -> None:
    create_response = mock_client.post(
        "/v1/rbac/users",
        json={
            "username": " ops_user ",
            "password": "OpsUser123",  # pragma: allowlist secret
            "role_ids": [2],
        },
        headers=_admin_headers(mock_client),
    )
    assert create_response.status_code == HTTPStatus.CREATED
    created_user = create_response.json()
    assert created_user["username"] == "ops_user"
    assert created_user["disabled"] is False
    assert created_user["role_ids"] == [2]
    user_id = created_user["id"]

    list_response = mock_client.get(
        "/v1/rbac/users",
        headers=_admin_headers(mock_client),
    )
    assert list_response.status_code == HTTPStatus.OK
    by_id = {user["id"]: user for user in list_response.json()}
    assert by_id[user_id]["username"] == "ops_user"
    assert by_id[user_id]["role_ids"] == [2]

    get_response = mock_client.get(
        f"/v1/rbac/users/{user_id}",
        headers=_admin_headers(mock_client),
    )
    assert get_response.status_code == HTTPStatus.OK
    assert get_response.json() == created_user

    update_response = mock_client.put(
        f"/v1/rbac/users/{user_id}",
        json={
            "username": "ops_user_v2",
            "current_password": "OpsUser123",  # pragma: allowlist secret
            "new_password": "OpsUser456",  # pragma: allowlist secret
            "role_ids": [1],
        },
        headers=_admin_headers(mock_client),
    )
    assert update_response.status_code == HTTPStatus.OK
    assert update_response.json() == {
        "id": user_id,
        "username": "ops_user_v2",
        "disabled": False,
        "role_ids": [1],
    }

    delete_response = mock_client.delete(
        f"/v1/rbac/users/{user_id}",
        headers=_admin_headers(mock_client),
    )
    assert delete_response.status_code == HTTPStatus.NO_CONTENT

    delete_again_response = mock_client.delete(
        f"/v1/rbac/users/{user_id}",
        headers=_admin_headers(mock_client),
    )
    assert delete_again_response.status_code == HTTPStatus.NO_CONTENT

    disabled_user_response = mock_client.get(
        f"/v1/rbac/users/{user_id}",
        headers=_admin_headers(mock_client),
    )
    assert disabled_user_response.status_code == HTTPStatus.OK
    assert disabled_user_response.json()["disabled"] is True

    login_disabled_response = mock_client.post(
        "/v1/token",
        data={"username": "ops_user_v2", "password": "OpsUser456"},  # pragma: allowlist secret
    )
    assert login_disabled_response.status_code == HTTPStatus.FORBIDDEN


def test_rbac_admin_not_found_matrix(mock_client: TestClient) -> None:
    headers = _admin_headers(mock_client)
    cases: tuple[dict[str, Any], ...] = (
        {
            "method": "PUT",
            "path": "/v1/rbac/roles/999",
            "json": {"name": "missing_role"},
            "detail": "Role 999 not found",
            "meta": {"id": 999},
        },
        {
            "method": "PUT",
            "path": "/v1/rbac/users/999/roles/1",
            "json": None,
            "detail": "User 999 not found",
            "meta": {"id": 999},
        },
        {
            "method": "PUT",
            "path": "/v1/rbac/roles/1/permissions/resources:read",
            "json": {"scope": "any"},
            "detail": "Permission resources:read not found",
            "meta": {"permission_id": "resources:read"},
        },
        {
            "method": "GET",
            "path": "/v1/rbac/users/999/roles",
            "json": None,
            "detail": "User 999 not found",
            "meta": {"id": 999},
        },
        {
            "method": "GET",
            "path": "/v1/rbac/roles/999/users",
            "json": None,
            "detail": "Role 999 not found",
            "meta": {"id": 999},
        },
        {
            "method": "GET",
            "path": "/v1/rbac/users/999",
            "json": None,
            "detail": "User 999 not found",
            "meta": {"id": 999},
        },
        {
            "method": "PUT",
            "path": "/v1/rbac/users/999",
            "json": {"disabled": True},
            "detail": "User 999 not found",
            "meta": {"id": 999},
        },
        {
            "method": "DELETE",
            "path": "/v1/rbac/users/999",
            "json": None,
            "detail": "User 999 not found",
            "meta": {"id": 999},
        },
    )

    for case in cases:
        if case["method"] == "GET":
            response = mock_client.get(case["path"], headers=headers)
        elif case["method"] == "DELETE":
            response = mock_client.delete(case["path"], headers=headers)
        else:
            response = mock_client.put(case["path"], headers=headers, json=case["json"])
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert_error_response(
            response,
            detail=case["detail"],
            status_code=HTTPStatus.NOT_FOUND,
            code="not_found",
            meta=case["meta"],
        )
