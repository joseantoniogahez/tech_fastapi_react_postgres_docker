import ast
from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / "app"
FEATURES_PATH = APP_PATH / "features"

IGNORED_CLASS_FILES = {"__init__.py", "models.py"}
NAMING_GUARD_FILE_NAMES = {"router.py", "service.py", "operations.py"}


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if path.name != "__init__.py")


def _parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))


def _collect_class_names(paths: list[Path]) -> set[str]:
    class_names: set[str] = set()
    for path in paths:
        if path.name in IGNORED_CLASS_FILES:
            continue
        module = _parse_module(path)
        class_names.update(node.name for node in module.body if isinstance(node, ast.ClassDef))
    return class_names


def _model_files() -> list[Path]:
    return sorted(path for path in FEATURES_PATH.rglob("models*.py"))


def _api_schema_files() -> list[Path]:
    legacy_api_schema_files = set(FEATURES_PATH.rglob("schemas_api.py"))
    package_api_schema_files = set(FEATURES_PATH.rglob("schemas/api.py"))
    return sorted(legacy_api_schema_files | package_api_schema_files)


def _naming_guard_files() -> list[Path]:
    return sorted(path for path in FEATURES_PATH.rglob("*.py") if path.name in NAMING_GUARD_FILE_NAMES)


def _collect_plain_id_parameters() -> list[str]:
    offenders: list[str] = []
    for path in _naming_guard_files():
        module = _parse_module(path)
        for node in ast.walk(module):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            arguments = list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs)
            if node.args.vararg is not None:
                arguments.append(node.args.vararg)
            if node.args.kwarg is not None:
                arguments.append(node.args.kwarg)
            if any(argument.arg == "id" for argument in arguments):
                relative_path = path.relative_to(APP_PATH.parent).as_posix()
                offenders.append(f"{relative_path}:{node.lineno}:{node.name}")
    return sorted(offenders)


def test_api_schema_class_names_do_not_overlap_with_models() -> None:
    overlapping_names = sorted(_collect_class_names(_model_files()) & _collect_class_names(_api_schema_files()))
    assert overlapping_names == []


def test_router_and_service_parameters_do_not_use_generic_id_name() -> None:
    assert _collect_plain_id_parameters() == []
