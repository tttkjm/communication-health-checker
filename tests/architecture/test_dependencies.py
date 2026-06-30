"""アーキテクチャ準拠の機械検証。"""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "communication_health_checker"


def _python_files(*parts: str) -> list[Path]:
    return list((SRC.joinpath(*parts)).rglob("*.py"))


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def test_domain_does_not_depend_on_outer_layers() -> None:
    for path in _python_files("domain"):
        for mod in _imports(path):
            assert not mod.startswith("communication_health_checker.application"), f"{path}: domain -> application"
            assert not mod.startswith("communication_health_checker.infrastructure"), (
                f"{path}: domain -> infrastructure"
            )
            assert not mod.startswith("apps"), f"{path}: domain -> apps"


def test_application_does_not_depend_on_infrastructure() -> None:
    for path in _python_files("application"):
        for mod in _imports(path):
            assert not mod.startswith("communication_health_checker.infrastructure"), (
                f"{path}: application -> infrastructure"
            )
            assert not mod.startswith("apps"), f"{path}: application -> apps"


def test_dto_does_not_depend_on_domain() -> None:
    for path in _python_files("application", "dto"):
        for mod in _imports(path):
            assert not mod.startswith("communication_health_checker.domain"), f"{path}: dto -> domain (ACL 違反)"


def test_core_package_not_polluted_by_web_framework() -> None:
    forbidden = ("fastapi", "uvicorn", "starlette")
    for path in SRC.rglob("*.py"):
        for mod in _imports(path):
            top = mod.split(".")[0]
            assert top not in forbidden, f"{path}: コアパッケージに {top} が混入"


def test_init_files_are_empty_except_core_and_modules() -> None:
    allowed_nonempty = {SRC / "domain" / "models" / "core" / "__init__.py", SRC / "modules" / "__init__.py"}
    for path in SRC.rglob("__init__.py"):
        if path in allowed_nonempty:
            continue
        body = path.read_text(encoding="utf-8").strip()
        assert body == "", f"{path}: __init__.py は空であるべき"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
