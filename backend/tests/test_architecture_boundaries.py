from __future__ import annotations

from core.boundary_engine import assert_no_cross_module_foreign_keys, assert_no_lateral_module_imports


def test_no_lateral_module_imports() -> None:
    assert_no_lateral_module_imports()


def test_no_cross_module_foreign_keys() -> None:
    assert_no_cross_module_foreign_keys()
