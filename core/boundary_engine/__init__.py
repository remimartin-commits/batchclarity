"""
Framework-agnostic module boundary checks (TASK-019).
Used by backend tests; parameterised paths so other monorepos can reuse.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = _REPO_ROOT / "backend"
MODULES_ROOT = BACKEND_ROOT / "app" / "modules"

TABLE_NAME_RE = re.compile(r'__tablename__\s*=\s*"([^"]+)"')
FK_RE = re.compile(r'ForeignKey\("([^".]+)\.[^"]+"\)')


def _module_py_files(modules_root: Path = MODULES_ROOT) -> list[Path]:
    return [
        path
        for path in modules_root.rglob("*.py")
        if "__pycache__" not in path.parts and path.name != "__init__.py"
    ]


def _module_name(path: Path, modules_root: Path) -> str:
    return path.relative_to(modules_root).parts[0]


def _build_table_to_module_map(modules_root: Path) -> dict[str, str]:
    table_map: dict[str, str] = {}
    for path in _module_py_files(modules_root):
        module = _module_name(path, modules_root)
        text = path.read_text(encoding="utf-8")
        for match in TABLE_NAME_RE.finditer(text):
            table_map[match.group(1)] = module
    return table_map


def assert_no_lateral_module_imports(
    modules_root: Path = MODULES_ROOT,
) -> None:
    violations: list[str] = []
    for path in _module_py_files(modules_root):
        source_module = _module_name(path, modules_root)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app.modules."):
                parts = node.module.split(".")
                if len(parts) >= 3 and parts[2] != source_module:
                    violations.append(
                        f"{path.relative_to(modules_root)} imports {node.module}"
                    )
    assert not violations, "Cross-module imports found:\n" + "\n".join(sorted(violations))


def assert_no_cross_module_foreign_keys(
    modules_root: Path = MODULES_ROOT,
) -> None:
    table_map = _build_table_to_module_map(modules_root)
    violations: list[str] = []
    for path in _module_py_files(modules_root):
        source_module = _module_name(path, modules_root)
        text = path.read_text(encoding="utf-8")
        for match in FK_RE.finditer(text):
            target_table = match.group(1)
            target_module = table_map.get(target_table)
            if target_module and target_module != source_module:
                violations.append(
                    f"{path.relative_to(modules_root)} has FK to '{target_table}' ({target_module})"
                )
    assert not violations, "Cross-module foreign keys found:\n" + "\n".join(sorted(violations))
