import ast
from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / "app"
FEATURES_PATH = APP_PATH / "features"

INIT_ALLOWED_ASSIGNMENTS: set[str] = set()

ALLOWED_CROSS_FEATURE_IMPORT_PREFIXES: dict[str, tuple[str, ...]] = {
    "auth": ("app.features.rbac.models",),
    "rbac": (
        "app.features.auth.models",
        "app.features.auth.principal",
    ),
}


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py"))


def _parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))


def _imported_modules(module: ast.Module) -> set[str]:
    imported: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
    return imported


def _feature_owner(path: Path) -> str:
    return path.relative_to(FEATURES_PATH).parts[0]


def _imported_feature(imported_module: str) -> str | None:
    if not imported_module.startswith("app.features."):
        return None
    parts = imported_module.split(".")
    if len(parts) < 3:
        return None
    return parts[2]


def _is_allowed_init_assignment_name(name: str) -> bool:
    return name in INIT_ALLOWED_ASSIGNMENTS or name.isupper()


def _is_allowed_cross_feature_import(owner_feature: str, imported_module: str) -> bool:
    allowed_prefixes = ALLOWED_CROSS_FEATURE_IMPORT_PREFIXES.get(owner_feature, ())
    return any(
        imported_module == allowed_prefix or imported_module.startswith(f"{allowed_prefix}.")
        for allowed_prefix in allowed_prefixes
    )


def test_feature_modules_do_not_import_other_features_without_explicit_allowlist() -> None:
    offenders: list[str] = []

    for path in _iter_python_files(FEATURES_PATH):
        owner_feature = _feature_owner(path)
        module = _parse_module(path)
        imports = _imported_modules(module)
        for imported_module in imports:
            imported_feature = _imported_feature(imported_module)
            if imported_feature is None or imported_feature == owner_feature:
                continue
            if _is_allowed_cross_feature_import(owner_feature, imported_module):
                continue
            offenders.append(f"{path.relative_to(APP_PATH.parent).as_posix()} -> {imported_module}")

    assert offenders == []


def test_init_modules_do_not_define_main_logic() -> None:
    offenders: list[str] = []
    for path in _iter_python_files(APP_PATH):
        if path.name != "__init__.py":
            continue
        module = _parse_module(path)
        for node in module.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                continue
            if isinstance(node, ast.Assign):
                assignment_targets = {target.id for target in node.targets if isinstance(target, ast.Name)}
                if assignment_targets and all(
                    _is_allowed_init_assignment_name(target) for target in assignment_targets
                ):
                    continue
            if (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and _is_allowed_init_assignment_name(node.target.id)
            ):
                continue
            offenders.append(path.relative_to(APP_PATH.parent).as_posix())
            break

    assert offenders == []
