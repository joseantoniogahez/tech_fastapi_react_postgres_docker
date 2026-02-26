import re
from collections import Counter
from pathlib import Path

import pytest

from app.const.permission import (
    PERMISSION_CATALOG,
    PERMISSION_CATALOG_BY_ID,
    PERMISSION_ID_PATTERN,
    PermissionDefinition,
    _validate_permission_catalog,
    build_permission_id,
)
from app.dependencies.authorization_books import BOOK_PERMISSION_IDS

PERMISSION_TOKEN_PATTERN = re.compile(r"`([a-z][a-z0-9_]*:[a-z][a-z0-9_]*)`")
AUTHORIZATION_MATRIX_PATH = Path(__file__).resolve().parent.parent / "docs" / "authorization_matrix.md"


def _extract_permission_ids_from_markdown(markdown: str) -> set[str]:
    return {match.group(1) for match in PERMISSION_TOKEN_PATTERN.finditer(markdown)}


def test_permission_catalog_has_no_duplicate_ids() -> None:
    permission_ids = [permission.id for permission in PERMISSION_CATALOG]
    duplicated_ids = sorted(permission_id for permission_id, count in Counter(permission_ids).items() if count > 1)
    assert duplicated_ids == []


def test_permission_catalog_ids_follow_resource_action_naming() -> None:
    invalid_ids = sorted(
        permission.id for permission in PERMISSION_CATALOG if PERMISSION_ID_PATTERN.fullmatch(permission.id) is None
    )
    assert invalid_ids == []


def test_book_authorization_dependencies_reference_catalog_permissions() -> None:
    catalog_ids = set(PERMISSION_CATALOG_BY_ID)
    orphan_ids = sorted(set(BOOK_PERMISSION_IDS.values()) - catalog_ids)
    assert orphan_ids == []


def test_authorization_matrix_references_catalog_permissions_only() -> None:
    matrix_markdown = AUTHORIZATION_MATRIX_PATH.read_text(encoding="utf-8")
    documented_permission_ids = _extract_permission_ids_from_markdown(matrix_markdown)
    catalog_ids = set(PERMISSION_CATALOG_BY_ID)

    orphan_documented_ids = sorted(documented_permission_ids - catalog_ids)
    assert orphan_documented_ids == []

    missing_documented_ids = sorted(catalog_ids - documented_permission_ids)
    assert missing_documented_ids == []


def test_build_permission_id_raises_for_invalid_format() -> None:
    with pytest.raises(ValueError, match="Invalid permission id 'Books:create'"):
        build_permission_id(resource="Books", action="create")


def test_validate_permission_catalog_raises_for_duplicate_ids() -> None:
    duplicate_catalog = (
        PermissionDefinition(resource="books", action="create", name="Create books"),
        PermissionDefinition(resource="books", action="create", name="Create books duplicate"),
    )

    with pytest.raises(ValueError, match="Duplicate permission ids in PERMISSION_CATALOG: books:create"):
        _validate_permission_catalog(duplicate_catalog)
