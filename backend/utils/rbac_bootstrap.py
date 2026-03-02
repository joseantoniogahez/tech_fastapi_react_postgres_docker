import argparse
import asyncio
import os
import sys
from dataclasses import dataclass

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.authorization import PERMISSION_SPECS, PermissionScope
from app.database import AsyncSessionDatabase
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole
from app.security.policies import (
    PasswordPolicyError,
    UsernamePolicyError,
    UsernamePolicyErrorCode,
    format_password_policy_summary,
    normalize_username,
    validate_password_policy,
)

BASE_PERMISSION_SPECS: tuple[tuple[str, str], ...] = PERMISSION_SPECS

BASE_PERMISSION_IDS: tuple[str, ...] = tuple(permission_id for permission_id, _ in BASE_PERMISSION_SPECS)

BASE_ROLE_PERMISSION_SPECS: dict[str, tuple[str, ...]] = {
    "admin_role": BASE_PERMISSION_IDS,
    "reader_role": (),
}


@dataclass(frozen=True)
class BootstrapReport:
    permissions_created: int
    permissions_updated: int
    roles_created: int
    role_permissions_created: int
    admin_user_created: bool
    admin_role_assigned: bool
    admin_username: str


def _normalize_username(username: str) -> str:
    try:
        return normalize_username(username)
    except UsernamePolicyError as exc:
        if exc.code is UsernamePolicyErrorCode.REQUIRED:
            raise ValueError("Admin username is required.") from exc

        raise ValueError(
            "Admin username has invalid format. Use lowercase letters, numbers, dot, underscore, hyphen."
        ) from exc


def _validate_password_policy(password: str, username: str) -> None:
    try:
        validate_password_policy(password, username)
    except PasswordPolicyError as exc:
        raise ValueError(
            f"Admin password does not meet policy: {format_password_policy_summary(exc.violations)}."
        ) from exc


async def _sync_permissions(session: AsyncSession) -> tuple[dict[str, Permission], int, int]:
    result = await session.execute(select(Permission).where(Permission.id.in_(BASE_PERMISSION_IDS)))
    permissions = {permission.id: permission for permission in result.scalars()}

    created_count = 0
    updated_count = 0
    for permission_id, permission_name in BASE_PERMISSION_SPECS:
        permission = permissions.get(permission_id)
        if permission is None:
            permission = Permission(id=permission_id, name=permission_name)
            permissions[permission_id] = permission
            session.add(permission)
            created_count += 1
            continue

        if permission.name != permission_name:
            permission.name = permission_name
            updated_count += 1

    await session.flush()
    return permissions, created_count, updated_count


async def _sync_roles(session: AsyncSession) -> tuple[dict[str, Role], int]:
    role_names = tuple(BASE_ROLE_PERMISSION_SPECS.keys())
    result = await session.execute(select(Role).where(Role.name.in_(role_names)))
    roles = {role.name: role for role in result.scalars()}

    created_count = 0
    for role_name in role_names:
        if role_name in roles:
            continue

        role = Role(name=role_name)
        roles[role_name] = role
        session.add(role)
        created_count += 1

    await session.flush()
    return roles, created_count


async def _sync_role_permissions(session: AsyncSession, roles_by_name: dict[str, Role]) -> int:
    base_role_ids = tuple(roles_by_name[role_name].id for role_name in BASE_ROLE_PERMISSION_SPECS)
    result = await session.execute(select(RolePermission).where(RolePermission.role_id.in_(base_role_ids)))
    existing_pairs = {(role_permission.role_id, role_permission.permission_id) for role_permission in result.scalars()}

    desired_pairs = {
        (roles_by_name[role_name].id, permission_id)
        for role_name, permission_ids in BASE_ROLE_PERMISSION_SPECS.items()
        for permission_id in permission_ids
    }

    missing_pairs = desired_pairs - existing_pairs
    for role_id, permission_id in sorted(missing_pairs):
        session.add(
            RolePermission(
                role_id=role_id,
                permission_id=permission_id,
                scope=PermissionScope.ANY,
            )
        )

    await session.flush()
    return len(missing_pairs)


async def _ensure_admin_user(
    session: AsyncSession,
    *,
    admin_username: str,
    admin_password: str | None,
    password_hasher: PasswordHasher,
) -> tuple[User, bool]:
    existing_user = await session.scalar(select(User).where(User.username == admin_username).limit(1))
    if existing_user is not None:
        return existing_user, False

    if admin_password is None or not admin_password.strip():
        raise ValueError("Admin user does not exist. Provide --admin-password or set RBAC_BOOTSTRAP_ADMIN_PASSWORD.")

    _validate_password_policy(admin_password, admin_username)
    user = User(
        username=admin_username,
        hashed_password=password_hasher.hash(admin_password),
        disabled=False,
    )
    session.add(user)
    await session.flush()
    return user, True


async def _ensure_admin_role_assignment(session: AsyncSession, *, user_id: int, admin_role_id: int) -> bool:
    existing_assignment = await session.scalar(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == admin_role_id,
        )
    )
    if existing_assignment is not None:
        return False

    session.add(UserRole(user_id=user_id, role_id=admin_role_id))
    await session.flush()
    return True


async def bootstrap_rbac(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    admin_username: str,
    admin_password: str | None,
) -> BootstrapReport:
    normalized_admin_username = _normalize_username(admin_username)
    password_hasher = PasswordHasher()

    async with session_factory() as session:
        async with session.begin():
            _, permissions_created, permissions_updated = await _sync_permissions(session)
            roles_by_name, roles_created = await _sync_roles(session)
            role_permissions_created = await _sync_role_permissions(session, roles_by_name)
            admin_user, admin_user_created = await _ensure_admin_user(
                session,
                admin_username=normalized_admin_username,
                admin_password=admin_password,
                password_hasher=password_hasher,
            )
            admin_role_assigned = await _ensure_admin_role_assignment(
                session,
                user_id=admin_user.id,
                admin_role_id=roles_by_name["admin_role"].id,
            )

    return BootstrapReport(
        permissions_created=permissions_created,
        permissions_updated=permissions_updated,
        roles_created=roles_created,
        role_permissions_created=role_permissions_created,
        admin_user_created=admin_user_created,
        admin_role_assigned=admin_role_assigned,
        admin_username=normalized_admin_username,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Idempotent RBAC bootstrap utility.")
    parser.add_argument(
        "--admin-username",
        default=os.getenv("RBAC_BOOTSTRAP_ADMIN_USERNAME", "admin"),
        help="Bootstrap admin username (default: RBAC_BOOTSTRAP_ADMIN_USERNAME or 'admin').",
    )
    parser.add_argument(
        "--admin-password",
        default=os.getenv("RBAC_BOOTSTRAP_ADMIN_PASSWORD"),
        help="Bootstrap admin password (required only when admin user does not exist).",
    )
    return parser


def _format_report(report: BootstrapReport) -> str:
    return (
        "RBAC bootstrap completed.\n"
        f"- admin_username: {report.admin_username}\n"
        f"- permissions_created: {report.permissions_created}\n"
        f"- permissions_updated: {report.permissions_updated}\n"
        f"- roles_created: {report.roles_created}\n"
        f"- role_permissions_created: {report.role_permissions_created}\n"
        f"- admin_user_created: {report.admin_user_created}\n"
        f"- admin_role_assigned: {report.admin_role_assigned}"
    )


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        report = asyncio.run(
            bootstrap_rbac(
                AsyncSessionDatabase,
                admin_username=args.admin_username,
                admin_password=args.admin_password,
            )
        )
    except ValueError as exc:
        print(f"RBAC bootstrap failed: {exc}", file=sys.stderr)
        return 1

    print(_format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
