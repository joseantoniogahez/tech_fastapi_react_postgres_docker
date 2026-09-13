#!/usr/bin/env python3
"""Bootstrap starter-kit identity for a new application.

By default this script previews targeted identity changes. Pass --write to apply them.
It intentionally does not change feature behavior, routes, permissions, migrations, or tests.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
ENV_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
RUNTIME_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")
SOURCE_REVISION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")
FULL_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
BASE_SLUG_MAX_LENGTH = 48
RESOURCE_NAME_MAX_LENGTH = 63
NPM_PACKAGE_MAX_LENGTH = 214
RUNTIME_IDENTIFIER_MAX_LENGTH = 128
PROVENANCE_RELATIVE_PATH = Path("docs/ai/template_provenance.json")
PROVENANCE_SCHEMA_VERSION = 1
TEMPLATE_CONTRACT_VERSION = "foundation-bootstrap-v1"


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
    before: str | None
    after: str


@dataclass(frozen=True)
class SourceSnapshot:
    repository: str
    requested_revision: str
    commit: str
    tree: str


@dataclass
class TargetState:
    content: bytes
    mode: int
    device: int
    inode: int
    size: int
    modified_ns: int


@dataclass
class MutationJournal:
    target: Path
    staged: Path
    backup: Path | None
    original_state: TargetState | None
    installed_bytes: bytes
    installed_state: TargetState | None = None
    backup_moved: bool = False
    installed: bool = False
    install_collision: bool = False


TextTransform = Callable[[str, BootstrapConfig, Path], str]


def slugify(value: str) -> str:
    words = [word for word in re.split(r"[^a-zA-Z0-9]+", value.strip().lower()) if word]
    if not words:
        raise BootstrapError("Cannot derive a slug from an empty app name.")
    slug = "-".join(words)
    if not SLUG_PATTERN.match(slug) or len(slug) > BASE_SLUG_MAX_LENGTH:
        raise BootstrapError(f"Invalid slug: {slug}")
    return slug


def env_name_from_slug(slug: str) -> str:
    env_name = slug.replace("-", "_")
    if not ENV_PATTERN.match(env_name):
        raise BootstrapError(f"Invalid environment prefix: {env_name}")
    return env_name


def require_slug(value: str, field_name: str, *, max_length: int = RESOURCE_NAME_MAX_LENGTH) -> str:
    normalized = value.strip()
    if not SLUG_PATTERN.match(normalized) or len(normalized) > max_length:
        raise BootstrapError(f"{field_name} must use lowercase letters, digits, and hyphens: {value}")
    return normalized


def require_env_name(value: str, field_name: str, *, max_length: int = RESOURCE_NAME_MAX_LENGTH) -> str:
    normalized = value.strip()
    if not ENV_PATTERN.match(normalized) or len(normalized) > max_length:
        raise BootstrapError(f"{field_name} must use lowercase letters, digits, and underscores: {value}")
    return normalized


def require_runtime_identifier(value: str, field_name: str) -> str:
    normalized = value.strip()
    if (
        not RUNTIME_IDENTIFIER_PATTERN.fullmatch(normalized)
        or len(normalized) > RUNTIME_IDENTIFIER_MAX_LENGTH
    ):
        raise BootstrapError(
            f"{field_name} must be a safe case-preserving identifier using letters, digits, '.', '_', ':', '/', or '-'."
        )
    return normalized


def require_display_text(value: str, field_name: str, *, max_length: int = 200) -> str:
    normalized = value.strip()
    if not normalized:
        raise BootstrapError(f"{field_name} must not be empty.")
    if len(normalized) > max_length:
        raise BootstrapError(f"{field_name} must be at most {max_length} characters.")
    if any(ord(character) < 32 or ord(character) == 127 for character in normalized):
        raise BootstrapError(f"{field_name} must be a single line without control characters.")
    return normalized


def build_config(args: argparse.Namespace) -> BootstrapConfig:
    app_name = require_display_text(args.app_name, "app-name")

    slug = (
        require_slug(args.slug, "slug", max_length=BASE_SLUG_MAX_LENGTH) if args.slug else slugify(app_name)
    )
    env_prefix = (
        require_env_name(args.env_prefix, "env-prefix", max_length=BASE_SLUG_MAX_LENGTH)
        if args.env_prefix
        else env_name_from_slug(slug)
    )
    description = (
        require_display_text(args.description, "description", max_length=500)
        if args.description
        else f"{app_name} application built from this starter kit."
    )

    return BootstrapConfig(
        app_name=app_name,
        slug=slug,
        description=description,
        env_prefix=env_prefix,
        frontend_package_name=(
            require_slug(args.frontend_package_name, "frontend-package-name", max_length=NPM_PACKAGE_MAX_LENGTH)
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
        jwt_issuer=(require_runtime_identifier(args.jwt_issuer, "jwt-issuer") if args.jwt_issuer else slug),
        jwt_audience=(
            require_runtime_identifier(args.jwt_audience, "jwt-audience")
            if args.jwt_audience
            else f"{slug}-api"
        ),
        document_title=(
            require_display_text(args.document_title, "document-title") if args.document_title else app_name
        ),
        landing_title=require_display_text(args.landing_title, "landing-title") if args.landing_title else app_name,
        landing_subtitle=(
            require_display_text(args.landing_subtitle, "landing-subtitle")
            if args.landing_subtitle
            else f"Signin to access {app_name}."
        ),
        landing_badge=require_display_text(args.landing_badge, "landing-badge") if args.landing_badge else app_name,
    )


def ensure_repo_root(root: Path) -> Path:
    resolved = root.resolve()
    required = ["AGENTS.md", "compose.yaml", ".env_examples", "backend", "frontend"]
    missing = [item for item in required if not (resolved / item).exists()]
    if missing:
        raise BootstrapError(f"Root does not look like this repository. Missing: {', '.join(missing)}")
    return resolved


def validate_source_repository(value: str) -> str:
    candidate = value.strip()
    parsed = urlsplit(candidate)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise BootstrapError("--source-repository must be a credential-free HTTP(S) repository URL.")
    return candidate.rstrip("/")


def _run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit={result.returncode}"
        raise BootstrapError(f"Unable to verify source snapshot with git: {detail}")
    return result.stdout.strip()


def resolve_source_snapshot(root: Path, repository: str, revision: str) -> SourceSnapshot:
    normalized_revision = revision.strip()
    if (
        SOURCE_REVISION_PATTERN.fullmatch(normalized_revision) is None
        or ".." in normalized_revision
        or normalized_revision.startswith("-")
    ):
        raise BootstrapError("--source-revision must be a safe full commit or reviewed tag name.")

    if (root / PROVENANCE_RELATIVE_PATH).exists():
        raise BootstrapError(
            f"Bootstrap provenance already exists at {PROVENANCE_RELATIVE_PATH.as_posix()}; "
            "use a separately reviewed identity-change procedure."
        )

    status = _run_git(root, "status", "--porcelain")
    if status:
        raise BootstrapError("Bootstrap requires a clean compatible checkout before preview or write.")

    head_commit = _run_git(root, "rev-parse", "HEAD")
    revision_ref = normalized_revision
    if FULL_COMMIT_PATTERN.fullmatch(normalized_revision) is None:
        revision_ref = f"refs/tags/{normalized_revision}"
        try:
            resolved_commit = _run_git(root, "rev-parse", "--verify", f"{revision_ref}^{{commit}}")
        except BootstrapError as exc:
            raise BootstrapError(
                "--source-revision must be a full 40-character commit or an existing reviewed tag; "
                "branches and symbolic revisions are not accepted."
            ) from exc
    else:
        resolved_commit = _run_git(root, "rev-parse", "--verify", f"{revision_ref}^{{commit}}")
    if resolved_commit != head_commit:
        raise BootstrapError(
            f"Source revision resolves to {resolved_commit}, but checkout HEAD is {head_commit}."
        )
    source_tree = _run_git(root, "show", "-s", "--format=%T", resolved_commit)
    if re.fullmatch(r"[0-9a-f]{40}", resolved_commit) is None or re.fullmatch(r"[0-9a-f]{40}", source_tree) is None:
        raise BootstrapError("Git did not return full immutable commit and tree identifiers.")

    return SourceSnapshot(
        repository=validate_source_repository(repository),
        requested_revision=normalized_revision,
        commit=resolved_commit,
        tree=source_tree,
    )


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
    updated, count = pattern.subn(lambda match: f"{match.group(1)}{escaped}{match.group(2)}", text)
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
    bootstrap_section = re.compile(
        r"^## Use This As a New Project Starter\n.*?(?=^## Run Full Stack \(Docker\)$)",
        re.MULTILINE | re.DOTALL,
    )
    origin_section = (
        "## Template Origin\n\n"
        "This application was created from the immutable template snapshot recorded in\n"
        "`docs/ai/template_provenance.json`. The one-time bootstrap has already been applied; use a\n"
        "separately reviewed identity migration for later naming changes. The retained\n"
        "`docs/ai/start_new_project.md` documents the original bootstrap workflow only.\n\n"
    )
    updated, section_count = bootstrap_section.subn(origin_section, updated)
    if section_count != 1:
        raise BootstrapError(f"Expected the one-time bootstrap section in {path}; found {section_count}.")
    return updated


def transform_backend_readme(text: str, config: BootstrapConfig, path: Path) -> str:
    updated = replace_exact(text, "`JWT_ISSUER=fastapi-template`", f"`JWT_ISSUER={config.jwt_issuer}`", path)
    updated = replace_exact(
        updated,
        "`JWT_AUDIENCE=fastapi-template-api`",
        f"`JWT_AUDIENCE={config.jwt_audience}`",
        path,
    )
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
    document_title = html.escape(config.document_title, quote=True)
    return replace_exact(text, "<title>Portal de Acceso</title>", f"<title>{document_title}</title>", path)


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


def load_json_object(text: str, path: Path) -> dict[str, object]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise BootstrapError(f"Expected valid JSON object in {path}: {exc.msg}.") from exc
    if not isinstance(data, dict):
        raise BootstrapError(f"Expected a JSON object in {path}.")
    return data


def transform_package_json(path: Path, package_name: str) -> FileChange:
    before = path.read_text(encoding="utf-8")
    data = load_json_object(before, path)
    if data.get("name") != "frontend":
        raise BootstrapError(f"Expected package name 'frontend' in {path}; found {data.get('name')!r}.")
    data["name"] = package_name
    after = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    return FileChange(path=path, before=before, after=after)


def transform_package_lock(path: Path, package_name: str) -> FileChange:
    before = path.read_text(encoding="utf-8")
    data = load_json_object(before, path)
    if data.get("name") != "frontend":
        raise BootstrapError(f"Expected lockfile root name 'frontend' in {path}; found {data.get('name')!r}.")
    data["name"] = package_name
    packages = data.get("packages")
    if not isinstance(packages, dict):
        raise BootstrapError(f"Expected lockfile packages object in {path}.")
    root_package = packages.get("")
    if not isinstance(root_package, dict):
        raise BootstrapError(f"Expected lockfile packages[''] object in {path}.")
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


def build_provenance_change(root: Path, config: BootstrapConfig, source: SourceSnapshot) -> FileChange:
    path = root / PROVENANCE_RELATIVE_PATH
    payload = {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "template_contract_version": TEMPLATE_CONTRACT_VERSION,
        "template_repository": source.repository,
        "requested_revision": source.requested_revision,
        "template_commit": source.commit,
        "template_tree": source.tree,
        "bootstrapped_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "application": {
            "name": config.app_name,
            "slug": config.slug,
            "frontend_package_name": config.frontend_package_name,
            "compose_projects": [
                config.compose_dev_name,
                config.compose_test_name,
                config.compose_prod_name,
            ],
            "jwt_issuer": config.jwt_issuer,
            "jwt_audience": config.jwt_audience,
        },
        "notice": (
            "This application originated from the recorded template snapshot and is not the pristine template."
        ),
    }
    return FileChange(path=path, before=None, after=json.dumps(payload, indent=2, ensure_ascii=True) + "\n")


def collect_changes(
    root: Path,
    config: BootstrapConfig,
    source: SourceSnapshot,
) -> list[FileChange]:
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
        build_provenance_change(root, config, source),
    ]
    return [change for change in changes if change.before != change.after]


def print_summary(
    config: BootstrapConfig,
    source: SourceSnapshot,
    changes: list[FileChange],
    write: bool,
) -> None:
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
    print(f"template repository: {source.repository}")
    print(f"template commit: {source.commit}")
    print(f"template tree: {source.tree}")
    print(f"provenance artifact: {PROVENANCE_RELATIVE_PATH.as_posix()}")
    print()
    if not changes:
        print("no changes needed")
        return
    for change in changes:
        print(f"{'will update' if write else 'would update'} {change.path}")


def _path_exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _validate_target(
    change: FileChange,
    root: Path,
    expected_state: TargetState | None = None,
) -> tuple[Path, TargetState | None]:
    resolved_target = change.path.resolve()
    if not resolved_target.is_relative_to(root) or change.path.is_symlink():
        raise BootstrapError(f"Refusing unsafe bootstrap target: {change.path}")

    if change.before is None:
        if _path_exists(change.path):
            raise BootstrapError(f"Bootstrap target appeared after preflight: {change.path}")
        return resolved_target.relative_to(root), None

    if not change.path.is_file():
        raise BootstrapError(f"Bootstrap target changed after preflight: {change.path}")
    current_state = _capture_target_state(change.path)
    if expected_state is None:
        try:
            current_text = current_state.content.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        except UnicodeDecodeError as exc:
            raise BootstrapError(f"Bootstrap target changed after preflight: {change.path}") from exc
        if current_text != change.before:
            raise BootstrapError(f"Bootstrap target changed after preflight: {change.path}")
    elif current_state != expected_state:
        raise BootstrapError(f"Bootstrap target changed after preflight: {change.path}")
    return resolved_target.relative_to(root), current_state


def _capture_target_state(path: Path) -> TargetState:
    with path.open("rb") as target_file:
        before = os.fstat(target_file.fileno())
        content = target_file.read()
        after = os.fstat(target_file.fileno())

    fields_before = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        stat.S_IMODE(before.st_mode),
    )
    fields_after = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        stat.S_IMODE(after.st_mode),
    )
    current = path.stat(follow_symlinks=False)
    fields_current = (
        current.st_dev,
        current.st_ino,
        current.st_size,
        current.st_mtime_ns,
        stat.S_IMODE(current.st_mode),
    )
    if fields_before != fields_after or fields_after != fields_current or len(content) != after.st_size:
        raise BootstrapError(f"Bootstrap target changed while it was being read: {path}")
    return TargetState(
        content=content,
        mode=stat.S_IMODE(after.st_mode),
        device=after.st_dev,
        inode=after.st_ino,
        size=after.st_size,
        modified_ns=after.st_mtime_ns,
    )


def _mutation_label(target: Path, root: Path) -> str:
    try:
        return target.relative_to(root).as_posix()
    except ValueError:
        return target.name


def _make_windows_target_removable(path: Path) -> None:
    if os.name == "nt":
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE)


def _restore_backup_exclusively(backup: Path, target: Path, original_mode: int) -> None:
    """Restore without replacing a target that appeared concurrently."""
    os.link(backup, target)
    _make_windows_target_removable(backup)
    backup.unlink()
    if os.name == "nt":
        os.chmod(target, original_mode)


def _rollback_mutations(mutations: list[MutationJournal], root: Path) -> list[str]:
    failures: list[str] = []
    for mutation in reversed(mutations):
        label = _mutation_label(mutation.target, root)
        try:
            if mutation.installed and _path_exists(mutation.target):
                if (
                    mutation.target.is_symlink()
                    or not mutation.target.is_file()
                ):
                    raise OSError("installed target changed before rollback")
                current_state = _capture_target_state(mutation.target)
                if mutation.installed_state is not None:
                    if current_state != mutation.installed_state:
                        raise OSError("installed target changed before rollback")
                elif current_state.content != mutation.installed_bytes:
                    raise OSError("installed target changed before rollback")
                _make_windows_target_removable(mutation.target)
                mutation.target.unlink()
            elif not mutation.installed and mutation.backup_moved and _path_exists(mutation.target):
                raise OSError("target appeared before rollback")

            if mutation.backup_moved:
                if mutation.backup is None or not mutation.backup.is_file():
                    raise OSError("transaction backup is unavailable")
                if mutation.original_state is None:
                    raise OSError("transaction backup has no recorded original state")
                mutation.target.parent.mkdir(parents=True, exist_ok=True)
                _restore_backup_exclusively(mutation.backup, mutation.target, mutation.original_state.mode)

            if mutation.original_state is None:
                safe_collision = mutation.install_collision and not mutation.installed and not mutation.backup_moved
                if _path_exists(mutation.target) and not safe_collision:
                    raise OSError("new target appeared or still exists after rollback")
            elif not mutation.target.is_file() or _capture_target_state(mutation.target) != mutation.original_state:
                raise OSError("original target was not restored exactly")
        except BaseException:  # Continue restoring independent targets after one rollback failure.
            failures.append(label)
    return failures


def _retry_readonly_removal(function: Callable[..., object], path: str, exc: BaseException) -> None:
    if os.name != "nt":
        raise exc
    os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
    function(path)


def _remove_transaction(transaction_root: Path, *, applied: bool) -> None:
    try:
        shutil.rmtree(transaction_root, onexc=_retry_readonly_removal)
    except OSError as exc:
        state = "applied" if applied else "restored"
        raise BootstrapError(
            f"Bootstrap changes were {state}, but transaction cleanup was incomplete; "
            f"inspect {transaction_root.name} before continuing."
        ) from exc


def _create_install_source(
    staged_path: Path,
    target: Path,
    transaction_root: Path,
    index: int,
    install_sources: list[Path],
) -> Path:
    """Create an adjacent install source so replacements inherit the target directory ACL."""
    target.parent.mkdir(parents=True, exist_ok=True)
    prefix = f".bootstrap-install-{transaction_root.name.removeprefix('.bootstrap-')}-{index}-"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0) | getattr(os, "O_CLOEXEC", 0)
    descriptor: int | None = None
    install_source: Path | None = None
    for _ in range(128):
        candidate = target.parent / f"{prefix}{secrets.token_hex(8)}"
        try:
            descriptor = os.open(candidate, flags, 0o666)
        except FileExistsError:
            continue
        install_source = candidate
        install_sources.append(install_source)
        break
    if descriptor is None or install_source is None:
        raise BootstrapError(f"Could not create an exclusive bootstrap install source beside {target}.")

    try:
        with os.fdopen(descriptor, "wb") as install_file:
            install_file.write(staged_path.read_bytes())
            install_file.flush()
            os.fsync(install_file.fileno())
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise
    return install_source


def _cleanup_install_sources(paths: list[Path], root: Path) -> list[str]:
    failures: list[str] = []
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            failures.append(_mutation_label(path, root))
    return failures


def apply_changes(changes: list[FileChange], root: Path) -> None:
    resolved_root = root.resolve()
    transaction_root = Path(tempfile.mkdtemp(prefix=".bootstrap-", dir=resolved_root))
    stage_root = transaction_root / "stage"
    backup_root = transaction_root / "backup"
    original_states: dict[Path, TargetState | None] = {}
    staged_paths: dict[Path, Path] = {}
    install_sources: list[Path] = []
    mutations: list[MutationJournal] = []

    try:
        for change in changes:
            relative_path, captured_state = _validate_target(change, resolved_root)
            original_states[change.path] = captured_state
            staged_path = stage_root / relative_path
            staged_path.parent.mkdir(parents=True, exist_ok=True)
            with staged_path.open("w", encoding="utf-8", newline="\n") as staged_file:
                staged_file.write(change.after)
            staged_paths[change.path] = staged_path

        backup_root.mkdir(parents=True)
        for index, change in enumerate(changes):
            original_state = original_states[change.path]
            relative_path, _ = _validate_target(change, resolved_root, original_state)
            staged_path = staged_paths[change.path]
            backup_path = backup_root / relative_path if change.before is not None else None
            mutation = MutationJournal(
                target=change.path,
                staged=staged_path,
                backup=backup_path,
                original_state=original_state,
                installed_bytes=staged_path.read_bytes(),
            )
            mutations.append(mutation)

            install_source = _create_install_source(
                staged_path,
                change.path,
                transaction_root,
                index,
                install_sources,
            )

            if backup_path is not None:
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                os.replace(change.path, backup_path)
                mutation.backup_moved = True
                backup_state = _capture_target_state(backup_path)
                if original_state is None or backup_state != original_state:
                    mutation.original_state = backup_state
                    raise BootstrapError(f"Bootstrap target changed during commit: {change.path}")

            change.path.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(install_source, change.path)
            except BaseException as link_error:
                try:
                    mutation.installed = _path_exists(change.path) and os.path.samefile(
                        install_source,
                        change.path,
                    )
                except OSError:
                    mutation.installed = False
                if isinstance(link_error, FileExistsError) and not mutation.installed:
                    mutation.install_collision = True
                raise
            else:
                mutation.installed = True
            install_source.unlink()
            install_sources.remove(install_source)
            if original_state is not None:
                os.chmod(change.path, original_state.mode)
            mutation.installed_state = _capture_target_state(change.path)
    except BaseException as exc:
        cleanup_failures = _cleanup_install_sources(install_sources, resolved_root)
        rollback_failures = _rollback_mutations(mutations, resolved_root)
        if rollback_failures or cleanup_failures:
            retained = transaction_root.name
            targets = ", ".join(sorted(set(rollback_failures + cleanup_failures)))
            raise BootstrapError(
                "Bootstrap failed and rollback was incomplete; "
                f"recovery data was retained at {retained}; unrestored: {targets}."
            ) from exc
        _remove_transaction(transaction_root, applied=False)
        if isinstance(exc, BootstrapError):
            raise
        raise BootstrapError(f"Bootstrap failed; previous files restored: {exc}") from exc
    else:
        _remove_transaction(transaction_root, applied=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview or apply new-app identity bootstrap changes.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--write", action="store_true", help="Apply changes. Without this flag, only preview.")
    parser.add_argument(
        "--source-repository",
        required=True,
        help="Credential-free HTTP(S) URL of the template repository used for this application.",
    )
    parser.add_argument(
        "--source-revision",
        required=True,
        help="Full 40-character commit or existing reviewed tag that must resolve to the clean checkout HEAD.",
    )
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
        source = resolve_source_snapshot(root, args.source_repository, args.source_revision)
        changes = collect_changes(root, config, source)
        print_summary(config, source, changes, args.write)
        if args.write:
            apply_changes(changes, root)
            print()
            print("bootstrap changes applied:")
            for change in changes:
                print(f"updated {change.path}")
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
