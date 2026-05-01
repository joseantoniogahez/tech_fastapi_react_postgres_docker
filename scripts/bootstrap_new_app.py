#!/usr/bin/env python3
"""Bootstrap starter-kit identity for a new application.

By default this script previews targeted identity changes. Pass --write to apply them.
It intentionally does not change feature behavior, routes, permissions, migrations, or tests.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
ENV_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class BootstrapError(ValueError):
    """Raised when bootstrap input or repository state is invalid."""


@dataclass(frozen=True)
class BootstrapConfig:
    app_name: str
    slug: str
    description: str
    env_prefix: str
    frontend_package_name: str
    compose_dev_name: str
    compose_test_name: str
    compose_prod_name: str
    api_host: str
    db_host: str
    ui_host: str
    db_name: str
    jwt_issuer: str
    jwt_audience: str
    document_title: str
    landing_title: str
    landing_subtitle: str
    landing_badge: str


@dataclass(frozen=True)
class FileChange:
    path: Path
    before: str
    after: str


TextTransform = Callable[[str, BootstrapConfig], str]


def slugify(value: str) -> str:
    words = [word for word in re.split(r"[^a-zA-Z0-9]+", value.strip().lower()) if word]
    if not words:
        raise BootstrapError("Cannot derive a slug from an empty app name.")
    slug = "-".join(words)
    if not SLUG_PATTERN.match(slug):
        raise BootstrapError(f"Invalid slug: {slug}")
    return slug


def env_name_from_slug(slug: str) -> str:
    env_name = slug.replace("-", "_")
    if not ENV_PATTERN.match(env_name):
        raise BootstrapError(f"Invalid environment prefix: {env_name}")
    return env_name


def require_slug(value: str, field_name: str) -> str:
    normalized = value.strip().lower()
    if not SLUG_PATTERN.match(normalized):
        raise BootstrapError(f"{field_name} must use lowercase letters, digits, and hyphens: {value}")
    return normalized


def require_env_name(value: str, field_name: str) -> str:
    normalized = value.strip().lower()
    if not ENV_PATTERN.match(normalized):
        raise BootstrapError(f"{field_name} must use lowercase letters, digits, and underscores: {value}")
    return normalized


def build_config(args: argparse.Namespace) -> BootstrapConfig:
    app_name = args.app_name.strip()
    if not app_name:
        raise BootstrapError("--app-name is required.")

    slug = require_slug(args.slug, "slug") if args.slug else slugify(app_name)
    env_prefix = require_env_name(args.env_prefix, "env-prefix") if args.env_prefix else env_name_from_slug(slug)
    description = (
        args.description.strip() if args.description else f"{app_name} application built from this starter kit."
    )

    return BootstrapConfig(
        app_name=app_name,
        slug=slug,
        description=description,
        env_prefix=env_prefix,
        frontend_package_name=(
            require_slug(args.frontend_package_name, "frontend-package-name")
            if args.frontend_package_name
            else f"{slug}-frontend"
        ),
        compose_dev_name=(
            require_slug(args.compose_dev_name, "compose-dev-name") if args.compose_dev_name else f"{slug}-dev"
        ),
        compose_test_name=(
            require_slug(args.compose_test_name, "compose-test-name") if args.compose_test_name else f"{slug}-tests"
        ),
        compose_prod_name=(
            require_slug(args.compose_prod_name, "compose-prod-name") if args.compose_prod_name else f"{slug}-prod"
        ),
        api_host=require_env_name(args.api_host, "api-host") if args.api_host else f"{env_prefix}_api",
        db_host=require_env_name(args.db_host, "db-host") if args.db_host else f"{env_prefix}_db",
        ui_host=require_env_name(args.ui_host, "ui-host") if args.ui_host else f"{env_prefix}_frontend",
        db_name=require_env_name(args.db_name, "db-name") if args.db_name else f"{env_prefix}_main",
        jwt_issuer=require_slug(args.jwt_issuer, "jwt-issuer") if args.jwt_issuer else slug,
        jwt_audience=require_slug(args.jwt_audience, "jwt-audience") if args.jwt_audience else f"{slug}-api",
        document_title=args.document_title.strip() if args.document_title else app_name,
        landing_title=args.landing_title.strip() if args.landing_title else app_name,
        landing_subtitle=args.landing_subtitle.strip() if args.landing_subtitle else f"Signin to access {app_name}.",
        landing_badge=args.landing_badge.strip() if args.landing_badge else app_name,
    )


def ensure_repo_root(root: Path) -> Path:
    resolved = root.resolve()
    required = ["AGENTS.md", "compose.yaml", ".env_examples", "backend", "frontend"]
    missing = [item for item in required if not (resolved / item).exists()]
    if missing:
        raise BootstrapError(f"Root does not look like this repository. Missing: {', '.join(missing)}")
    return resolved


def replace_exact(text: str, old: str, new: str, path: Path) -> str:
    if old not in text:
        raise BootstrapError(f"Expected text not found in {path}: {old}")
    return text.replace(old, new)


def replace_line_value(text: str, key: str, value: str, path: Path) -> str:
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    replacement = f"{key}={value}"
    updated, count = pattern.subn(replacement, text)
    if count != 1:
        raise BootstrapError(f"Expected exactly one {key}= line in {path}; found {count}.")
    return updated


def replace_compose_name(text: str, value: str, path: Path) -> str:
    updated, count = re.subn(r"^name:\s*.+$", f"name: {value}", text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise BootstrapError(f"Expected exactly one top-level name in {path}; found {count}.")
    return updated


def replace_ts_message(text: str, key: str, value: str, path: Path) -> str:
    escaped = json.dumps(value, ensure_ascii=False)
    pattern = re.compile(rf'^(  "{re.escape(key)}":\s*)".*?"(,.*)$', re.MULTILINE)
    updated, count = pattern.subn(rf"\1{escaped}\2", text)
    if count != 1:
        raise BootstrapError(f"Expected exactly one i18n key {key} in {path}; found {count}.")
    return updated


def transform_root_readme(text: str, config: BootstrapConfig, path: Path) -> str:
    updated = replace_exact(text, "# FastAPI + React + PostgreSQL Docker Template", f"# {config.app_name}", path)
    updated = replace_exact(
        updated,
        "Full-stack template application with JWT authentication and RBAC.",
        config.description,
        path,
    )
    updated = replace_exact(
        updated,
        "`compose.test.yaml` sets `name: tech-tests`",
        f"`compose.test.yaml` sets `name: {config.compose_test_name}`",
        path,
    )
    updated = replace_exact(
        updated,
        "`compose.prod.yaml` sets `name: tech-prod`",
        f"`compose.prod.yaml` sets `name: {config.compose_prod_name}`",
        path,
    )
    return updated


def transform_backend_readme(text: str, config: BootstrapConfig, path: Path) -> str:
    updated = replace_exact(text, "`JWT_ISSUER=fastapi-template`", f"`JWT_ISSUER={config.jwt_issuer}`", path)
    updated = replace_exact(text, "`JWT_AUDIENCE=fastapi-template-api`", f"`JWT_AUDIENCE={config.jwt_audience}`", path)
    updated = replace_exact(
        updated,
        "`DB_HOST=system_db`, `DB_NAME=main_db`",
        f"`DB_HOST={config.db_host}`, `DB_NAME={config.db_name}`",
        path,
    )
    updated = replace_exact(updated, 'DB_NAME = "main_db"', f'DB_NAME = "{config.db_name}"', path)
    updated = replace_exact(updated, 'DB_NAME="main_db"', f'DB_NAME="{config.db_name}"', path)
    return updated


def transform_env_examples(text: str, config: BootstrapConfig, path: Path) -> str:
    updated = text
    replacements = {
        "API_HOST": config.api_host,
        "JWT_ISSUER": config.jwt_issuer,
        "JWT_AUDIENCE": config.jwt_audience,
        "DB_HOST": config.db_host,
        "DB_NAME": config.db_name,
        "UI_HOST": config.ui_host,
    }
    for key, value in replacements.items():
        updated = replace_line_value(updated, key, value, path)
    return updated


def transform_compose_yaml(text: str, config: BootstrapConfig, path: Path) -> str:
    updated = replace_compose_name(text, config.compose_dev_name, path)
    updated = replace_exact(updated, "${JWT_ISSUER:-fastapi-template}", f"${{JWT_ISSUER:-{config.jwt_issuer}}}", path)
    updated = replace_exact(
        updated, "${JWT_AUDIENCE:-fastapi-template-api}", f"${{JWT_AUDIENCE:-{config.jwt_audience}}}", path
    )
    return updated


def transform_compose_test(text: str, config: BootstrapConfig, path: Path) -> str:
    return replace_compose_name(text, config.compose_test_name, path)


def transform_compose_prod(text: str, config: BootstrapConfig, path: Path) -> str:
    return replace_compose_name(text, config.compose_prod_name, path)


def transform_settings(text: str, config: BootstrapConfig, path: Path) -> str:
    updated = replace_exact(
        text, 'JWT_ISSUER: str = "fastapi-template"', f'JWT_ISSUER: str = "{config.jwt_issuer}"', path
    )
    updated = replace_exact(
        updated,
        'JWT_AUDIENCE: str = "fastapi-template-api"',
        f'JWT_AUDIENCE: str = "{config.jwt_audience}"',
        path,
    )
    return updated


def transform_index_html(text: str, config: BootstrapConfig, path: Path) -> str:
    return replace_exact(text, "<title>Portal de Acceso</title>", f"<title>{config.document_title}</title>", path)


def transform_ui_text(text: str, config: BootstrapConfig, path: Path) -> str:
    updated = text
    updates = {
        "auth.login.footer.backToLanding": f"Regresa a {config.app_name}",
        "landing.badge.portal": config.landing_badge,
        "landing.loading.title": f"Cargando {config.app_name}...",
        "landing.subtitle": config.landing_subtitle,
        "landing.title": config.landing_title,
    }
    for key, value in updates.items():
        updated = replace_ts_message(updated, key, value, path)
    return updated


def transform_package_json(path: Path, package_name: str) -> FileChange:
    before = path.read_text(encoding="utf-8")
    data = json.loads(before)
    if data.get("name") != "frontend":
        raise BootstrapError(f"Expected package name 'frontend' in {path}; found {data.get('name')!r}.")
    data["name"] = package_name
    after = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    return FileChange(path=path, before=before, after=after)


def transform_package_lock(path: Path, package_name: str) -> FileChange:
    before = path.read_text(encoding="utf-8")
    data = json.loads(before)
    if data.get("name") != "frontend":
        raise BootstrapError(f"Expected lockfile root name 'frontend' in {path}; found {data.get('name')!r}.")
    data["name"] = package_name
    root_package = data.get("packages", {}).get("")
    if isinstance(root_package, dict):
        if root_package.get("name") != "frontend":
            raise BootstrapError(
                f"Expected lockfile packages[''].name 'frontend' in {path}; found {root_package.get('name')!r}."
            )
        root_package["name"] = package_name
    after = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    return FileChange(path=path, before=before, after=after)


def text_change(path: Path, config: BootstrapConfig, transform: TextTransform) -> FileChange:
    before = path.read_text(encoding="utf-8")
    after = transform(before, config, path)
    return FileChange(path=path, before=before, after=after)


def collect_changes(root: Path, config: BootstrapConfig) -> list[FileChange]:
    changes = [
        text_change(root / "README.md", config, transform_root_readme),
        text_change(root / "backend" / "README.md", config, transform_backend_readme),
        text_change(root / ".env_examples", config, transform_env_examples),
        text_change(root / "compose.yaml", config, transform_compose_yaml),
        text_change(root / "compose.test.yaml", config, transform_compose_test),
        text_change(root / "compose.prod.yaml", config, transform_compose_prod),
        text_change(root / "backend" / "app" / "core" / "config" / "settings.py", config, transform_settings),
        text_change(root / "frontend" / "index.html", config, transform_index_html),
        text_change(root / "frontend" / "src" / "shared" / "i18n" / "ui-text.ts", config, transform_ui_text),
        transform_package_json(root / "frontend" / "package.json", config.frontend_package_name),
        transform_package_lock(root / "frontend" / "package-lock.json", config.frontend_package_name),
    ]
    return [change for change in changes if change.before != change.after]


def print_summary(config: BootstrapConfig, changes: list[FileChange], write: bool) -> None:
    mode = "write" if write else "dry-run"
    print(f"bootstrap mode: {mode}")
    print(f"app name: {config.app_name}")
    print(f"slug: {config.slug}")
    print(f"env prefix: {config.env_prefix}")
    print(f"frontend package: {config.frontend_package_name}")
    print(f"compose names: {config.compose_dev_name}, {config.compose_test_name}, {config.compose_prod_name}")
    print(f"hosts: api={config.api_host}, db={config.db_host}, ui={config.ui_host}")
    print(f"db name: {config.db_name}")
    print(f"jwt: issuer={config.jwt_issuer}, audience={config.jwt_audience}")
    print()
    if not changes:
        print("no changes needed")
        return
    for change in changes:
        print(f"{'updated' if write else 'would update'} {change.path}")


def apply_changes(changes: list[FileChange]) -> None:
    for change in changes:
        change.path.write_text(change.after, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview or apply new-app identity bootstrap changes.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--write", action="store_true", help="Apply changes. Without this flag, only preview.")
    parser.add_argument("--app-name", required=True, help='Human app name, for example "Example Portal".')
    parser.add_argument("--description", default="", help="Root README description for the new app.")
    parser.add_argument("--slug", help="Lowercase app slug. Defaults to slugified app name.")
    parser.add_argument("--env-prefix", help="Lowercase underscore env prefix. Defaults to slug with underscores.")
    parser.add_argument("--frontend-package-name", help="Frontend npm package name. Defaults to <slug>-frontend.")
    parser.add_argument("--compose-dev-name", help="Docker Compose dev project name. Defaults to <slug>-dev.")
    parser.add_argument("--compose-test-name", help="Docker Compose test project name. Defaults to <slug>-tests.")
    parser.add_argument("--compose-prod-name", help="Docker Compose prod project name. Defaults to <slug>-prod.")
    parser.add_argument("--api-host", help="API container hostname. Defaults to <env-prefix>_api.")
    parser.add_argument("--db-host", help="Database container hostname. Defaults to <env-prefix>_db.")
    parser.add_argument("--ui-host", help="Frontend container hostname. Defaults to <env-prefix>_frontend.")
    parser.add_argument("--db-name", help="Database name. Defaults to <env-prefix>_main.")
    parser.add_argument("--jwt-issuer", help="JWT issuer. Defaults to <slug>.")
    parser.add_argument("--jwt-audience", help="JWT audience. Defaults to <slug>-api.")
    parser.add_argument("--document-title", help="frontend/index.html title. Defaults to app name.")
    parser.add_argument("--landing-title", help="Landing page H1. Defaults to app name.")
    parser.add_argument("--landing-subtitle", help="Landing page subtitle. Defaults to app-specific login copy.")
    parser.add_argument("--landing-badge", help="Landing page badge. Defaults to app name.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        root = ensure_repo_root(Path(args.root))
        config = build_config(args)
        changes = collect_changes(root, config)
        print_summary(config, changes, args.write)
        if args.write:
            apply_changes(changes)
            print()
            print("next steps:")
            print("- review changed files")
            print("- run Docker Compose config validation for affected profiles")
            print("- run backend and frontend validation gates from docs/ai/new_app_bootstrap_checklist.md")
        else:
            print()
            print("preview only; rerun with --write to apply")
    except BootstrapError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
