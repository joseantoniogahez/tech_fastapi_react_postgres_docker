#!/usr/bin/env python3
"""Scaffold backend, frontend, or full-stack feature structure.

The scaffold creates structure and TODO checklists only. It does not register routers,
edit frontend route composition, add permissions, or implement business logic.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


VALID_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")


@dataclass(frozen=True)
class FeatureNames:
    raw: str
    slug: str
    python_package: str
    component: str
    title: str


@dataclass(frozen=True)
class ScaffoldFile:
    path: Path
    content: str


class ScaffoldError(ValueError):
    """Raised when scaffold input is invalid."""


def normalize_feature_name(raw_name: str) -> FeatureNames:
    raw = raw_name.strip()
    if not raw:
        raise ScaffoldError("Feature name is required.")
    if not VALID_NAME_PATTERN.match(raw):
        raise ScaffoldError("Feature name must start with a letter and use only letters, digits, '-' or '_'.")

    words = [word for word in re.split(r"[-_\s]+", raw) if word]
    if not words:
        raise ScaffoldError("Feature name must include at least one word.")

    slug = "-".join(word.lower() for word in words)
    python_package = "_".join(word.lower() for word in words)
    component = "".join(word[:1].upper() + word[1:].lower() for word in words)
    title = " ".join(word[:1].upper() + word[1:].lower() for word in words)
    return FeatureNames(raw=raw, slug=slug, python_package=python_package, component=component, title=title)


def ensure_repo_root(root: Path) -> Path:
    resolved = root.resolve()
    required = ["backend", "frontend", "AGENTS.md"]
    missing = [item for item in required if not (resolved / item).exists()]
    if missing:
        raise ScaffoldError(f"Root does not look like this repository. Missing: {', '.join(missing)}")
    return resolved


def write_files(files: list[ScaffoldFile], dry_run: bool) -> None:
    for scaffold_file in files:
        if scaffold_file.path.exists():
            raise ScaffoldError(f"Refusing to overwrite existing file: {scaffold_file.path}")

    for scaffold_file in files:
        if dry_run:
            print(f"[dry-run] create {scaffold_file.path}")
            continue
        scaffold_file.path.parent.mkdir(parents=True, exist_ok=True)
        scaffold_file.path.write_text(scaffold_file.content, encoding="utf-8")
        print(f"created {scaffold_file.path}")


def backend_files(root: Path, names: FeatureNames, include_model: bool) -> list[ScaffoldFile]:
    feature_dir = root / "backend" / "app" / "features" / names.python_package
    schemas_dir = feature_dir / "schemas"
    test_dir = root / "backend" / "tests" / "features" / names.python_package

    files = [
        ScaffoldFile(
            feature_dir / "__init__.py",
            f'"""Backend feature package for {names.title}."""\n',
        ),
        ScaffoldFile(
            feature_dir / "router.py",
            f'''from fastapi import APIRouter

router = APIRouter(
    prefix="/{names.slug}",
    tags=["{names.slug}"],
)


# TODO: Add endpoints after confirming API, auth, RBAC, OpenAPI, and error contracts.
''',
        ),
        ScaffoldFile(
            feature_dir / "service.py",
            f'''class {names.component}Service:
    """Application service for {names.title} behavior."""

    # TODO: Add use cases after defining acceptance criteria and domain errors.
''',
        ),
        ScaffoldFile(
            feature_dir / "repository.py",
            f'''class {names.component}Repository:
    """Persistence adapter for {names.title} data."""

    # TODO: Add repository methods when this feature owns persistence queries.
''',
        ),
        ScaffoldFile(
            feature_dir / "openapi.py",
            '''from typing import Any


# TODO: Add OpenAPI metadata constants and consume them in router endpoints.
EXAMPLE_DOC: dict[str, Any] = {}
''',
        ),
        ScaffoldFile(
            schemas_dir / "__init__.py",
            '"""Schemas for the feature."""\n',
        ),
        ScaffoldFile(
            schemas_dir / "api.py",
            '''"""Request and response schemas for the HTTP API."""

# TODO: Add pydantic API schemas.
''',
        ),
        ScaffoldFile(
            schemas_dir / "app.py",
            '''"""Application-level schemas and commands."""

# TODO: Add service commands, records, and domain-facing schemas.
''',
        ),
        ScaffoldFile(
            test_dir / "test_router.py",
            '''# TODO: Add router tests for HTTP status, response schema, auth, and error contracts.
''',
        ),
        ScaffoldFile(
            test_dir / "test_service.py",
            '''# TODO: Add service tests for use cases and domain errors.
''',
        ),
        ScaffoldFile(
            test_dir / "test_repository.py",
            '''# TODO: Add repository tests when persistence behavior is implemented.
''',
        ),
        ScaffoldFile(
            feature_dir / "SCAFFOLD_CHECKLIST.md",
            f'''# {names.title} Backend Scaffold Checklist

- [ ] Read `AGENTS.md`.
- [ ] Read `backend/docs/backend_playbook.md`.
- [ ] Confirm API, data, auth, RBAC, errors, observability, and validation impact.
- [ ] Register router module in `backend/app/core/setup/routers.py` when endpoints are added.
- [ ] Add dependency providers in `backend/app/core/setup/dependencies.py` when needed.
- [ ] Add authorization dependencies when endpoints are protected.
- [ ] Replace placeholder OpenAPI metadata in `openapi.py`.
- [ ] Update `backend/docs/operations/api_endpoints.md` when endpoint behavior changes.
- [ ] Update `backend/docs/operations/authorization_matrix.md` when permissions change.
- [ ] Update `backend/docs/operations/error_mapping.md` when domain errors change.
- [ ] Add Alembic migration if models or constraints change.
- [ ] Run `python -m pytest backend/tests`.
- [ ] Run `python -m pytest backend/tests --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=100`.
''',
        ),
    ]

    if include_model:
        files.append(
            ScaffoldFile(
                feature_dir / "models.py",
                '''"""SQLAlchemy models owned by the feature."""

# TODO: Add SQLAlchemy models and create an Alembic migration.
''',
            )
        )

    return files


def frontend_files(root: Path, names: FeatureNames, route_path: str) -> list[ScaffoldFile]:
    feature_dir = root / "frontend" / "src" / "features" / names.slug
    component_name = f"{names.component}Page"

    return [
        ScaffoldFile(
            feature_dir / f"{component_name}.tsx",
            f'''export const {component_name} = () => {{
  return (
    <main>
      {{/* TODO: Build the {names.title} UI and source user-facing text from src/shared/i18n/ui-text.ts. */}}
    </main>
  );
}};
''',
        ),
        ScaffoldFile(
            feature_dir / f"{component_name}.test.tsx",
            f'''# TODO: Add tests for {component_name} behavior, states, and user interactions.
'''.replace("#", "//"),
        ),
        ScaffoldFile(
            feature_dir / "SCAFFOLD_CHECKLIST.md",
            f'''# {names.title} Frontend Scaffold Checklist

- [ ] Read `AGENTS.md`.
- [ ] Read `frontend/docs/frontend_playbook.md`.
- [ ] Confirm route, API, auth, state, UX, a11y, observability, performance, and validation impact.
- [ ] Import `{component_name}` in `frontend/src/app/routes.tsx` when the route is ready.
- [ ] Add route path `{route_path}` in `frontend/src/app/routes.tsx` with the right guard.
- [ ] Add user-facing text keys to `frontend/src/shared/i18n/ui-text.ts`.
- [ ] Update `frontend/docs/operations/route_inventory.md` when route behavior changes.
- [ ] Update `frontend/docs/operations/api_consumer_matrix.md` when API consumers change.
- [ ] Update `frontend/docs/operations/e2e_smoke_suite.md` when auth/routing/error journeys change.
- [ ] Add page, route guard, API consumer, a11y, and e2e tests as applicable.
- [ ] Run `npm --prefix frontend run check`.
- [ ] Run `npm --prefix frontend run test:e2e:ci` when auth, routing, or error journeys change.
- [ ] Run `npm --prefix frontend run build`.

Suggested route import:

```tsx
import {{ {component_name} }} from "@/features/{names.slug}/{component_name}";
```
''',
        ),
    ]


def full_stack_files(root: Path, names: FeatureNames) -> list[ScaffoldFile]:
    checklist_dir = root / "docs" / "ai" / "scaffolds"
    return [
        ScaffoldFile(
            checklist_dir / f"{names.slug}_full_stack_checklist.md",
            f'''# {names.title} Full-Stack Scaffold Checklist

- [ ] Read `AGENTS.md`.
- [ ] Fill or review `docs/ai/templates/full_stack_feature_request.md`.
- [ ] Confirm backend API, data, auth, RBAC, errors, docs, and validation impact.
- [ ] Confirm frontend route, state, UX, a11y, e2e, docs, and validation impact.
- [ ] Complete backend scaffold placeholders.
- [ ] Complete frontend scaffold placeholders.
- [ ] Register backend router when endpoints are ready.
- [ ] Update frontend route composition when the page is ready.
- [ ] Run `npm --prefix frontend run openapi:sync` when backend OpenAPI output changes.
- [ ] Run backend validation.
- [ ] Run frontend validation.
- [ ] Run `pre-commit run --all-files` before push-level confidence when practical.
''',
        )
    ]


def scaffold_backend(args: argparse.Namespace) -> None:
    root = ensure_repo_root(Path(args.root))
    names = normalize_feature_name(args.name)
    files = backend_files(root, names, args.with_model)
    write_files(files, args.dry_run)
    print_backend_next_steps(names)


def scaffold_frontend(args: argparse.Namespace) -> None:
    root = ensure_repo_root(Path(args.root))
    names = normalize_feature_name(args.name)
    route_path = args.route or f"/{names.slug}"
    files = frontend_files(root, names, route_path)
    write_files(files, args.dry_run)
    print_frontend_next_steps(names, route_path)


def scaffold_full_stack(args: argparse.Namespace) -> None:
    root = ensure_repo_root(Path(args.root))
    names = normalize_feature_name(args.name)
    route_path = args.route or f"/{names.slug}"
    files = [
        *backend_files(root, names, args.with_model),
        *frontend_files(root, names, route_path),
        *full_stack_files(root, names),
    ]
    write_files(files, args.dry_run)
    print_backend_next_steps(names)
    print_frontend_next_steps(names, route_path)
    print(f"full-stack checklist: docs/ai/scaffolds/{names.slug}_full_stack_checklist.md")


def print_backend_next_steps(names: FeatureNames) -> None:
    print("backend next steps:")
    print(f"- register app.features.{names.python_package}.router in backend/app/core/setup/routers.py")
    print("- replace TODO placeholders with implementation and tests")
    print("- update affected backend docs and run backend validation gates")


def print_frontend_next_steps(names: FeatureNames, route_path: str) -> None:
    print("frontend next steps:")
    print(f"- import {names.component}Page in frontend/src/app/routes.tsx")
    print(f"- add route path {route_path} with the correct public/protected/permission guard")
    print("- add text catalog entries, tests, affected docs, and frontend validation gates")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scaffold feature structure for this starter kit.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--dry-run", action="store_true", help="Print files that would be created without writing them.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    backend = subparsers.add_parser("backend", help="Create backend feature structure.")
    backend.add_argument("name", help="Feature name, for example audit-log or reports.")
    backend.add_argument("--with-model", action="store_true", help="Also create models.py placeholder.")
    backend.set_defaults(func=scaffold_backend)

    frontend = subparsers.add_parser("frontend", help="Create frontend feature page structure.")
    frontend.add_argument("name", help="Feature name, for example audit-log or reports.")
    frontend.add_argument("--route", help="Suggested route path. Defaults to /<feature-name>.")
    frontend.set_defaults(func=scaffold_frontend)

    full_stack = subparsers.add_parser("full-stack", help="Create backend, frontend, and full-stack checklist structure.")
    full_stack.add_argument("name", help="Feature name, for example audit-log or reports.")
    full_stack.add_argument("--route", help="Suggested route path. Defaults to /<feature-name>.")
    full_stack.add_argument("--with-model", action="store_true", help="Also create backend models.py placeholder.")
    full_stack.set_defaults(func=scaffold_full_stack)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except ScaffoldError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
