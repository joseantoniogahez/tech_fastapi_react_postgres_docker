import ast
from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / "app"
MODELS_PATH = APP_PATH / "models"
API_SCHEMAS_PATH = APP_PATH / "schemas" / "api"
NAMING_GUARD_PATHS = (
    APP_PATH / "routers",
    APP_PATH / "services",
)
IGNORED_CLASS_FILES = {"__init__.py", "base.py"}


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if path.name != "__init__.py")


def _parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _collect_class_names(root: Path) -> set[str]:
    class_names: set[str] = set()
    for path in _iter_python_files(root):
        if path.name in IGNORED_CLASS_FILES:
            continue
        module = _parse_module(path)
        class_names.update(node.name for node in module.body if isinstance(node, ast.ClassDef))
    return class_names


def _collect_plain_id_parameters() -> list[str]:
    offenders: list[str] = []
    for root in NAMING_GUARD_PATHS:
        for path in _iter_python_files(root):
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
    overlapping_names = sorted(_collect_class_names(MODELS_PATH) & _collect_class_names(API_SCHEMAS_PATH))
    assert overlapping_names == []


def test_router_and_service_parameters_do_not_use_generic_id_name() -> None:
    assert _collect_plain_id_parameters() == []
