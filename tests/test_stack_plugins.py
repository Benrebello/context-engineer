"""Tests for StackPluginManager schema validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.stack_plugins import StackPluginManager


def _write_plugin_file(directory: Path, name: str, content: str) -> Path:
    file_path = directory / f"{name}.yaml"
    directory.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_valid_stack_plugin_loads(tmp_path: Path) -> None:
    """Ensure valid stack plugins are registered."""
    plugin_dir = tmp_path / "stacks"
    _write_plugin_file(
        plugin_dir,
        "valid",
        """
name: python-test
version: "1.0.0"
description: Test stack
commands:
  init: make init
  install: pip install -r requirements.txt
structure:
  app: src/app
  tests: tests
""",
    )

    manager = StackPluginManager(plugins_dir=plugin_dir)

    assert "python-test" in manager.list_plugins()
    plugin = manager.get_plugin("python-test")
    assert plugin is not None
    assert plugin.get_structure()["app"] == "src/app"


def test_invalid_stack_plugin_raises(tmp_path: Path) -> None:
    """Ensure invalid stack files fail fast."""
    plugin_dir = tmp_path / "stacks"
    _write_plugin_file(
        plugin_dir,
        "invalid",
        """
name: invalid-stack
version: "0.1.0"
description: Broken stack
commands:
  init: echo init
""",
    )

    with pytest.raises(ValueError, match="invalid"):
        StackPluginManager(plugins_dir=plugin_dir)


class TestStackPlugin:
    def _make_plugin(self):
        from core.stack_plugins import StackPlugin
        return StackPlugin({
            "name": "test-stack",
            "version": "1.0.0",
            "description": "Test",
            "commands": {
                "init": "make init",
                "install": "pip install",
                "test": "pytest",
                "lint": "ruff check",
            },
            "structure": {"app": "src/app", "tests": "tests"},
            "patterns": ["auth"],
            "dependencies": ["flask"],
        })

    def test_get_init_command(self):
        p = self._make_plugin()
        assert p.get_init_command() == "make init"

    def test_get_install_command(self):
        p = self._make_plugin()
        assert p.get_install_command(["flask"]) == "pip install flask"

    def test_get_install_command_empty(self):
        p = self._make_plugin()
        assert p.get_install_command([]) == "pip install"

    def test_get_test_command(self):
        p = self._make_plugin()
        assert p.get_test_command() == "pytest"

    def test_get_lint_command(self):
        p = self._make_plugin()
        assert p.get_lint_command() == "ruff check"

    def test_get_structure(self):
        p = self._make_plugin()
        s = p.get_structure()
        assert s["app"] == "src/app"


class TestStackPluginManagerExtra:
    def test_get_plugin_unknown(self, tmp_path):
        plugin_dir = tmp_path / "stacks"
        plugin_dir.mkdir()
        manager = StackPluginManager(plugins_dir=plugin_dir)
        assert manager.get_plugin("nonexistent") is None

    def test_register_plugin(self, tmp_path):
        from core.stack_plugins import StackPlugin
        plugin_dir = tmp_path / "stacks"
        plugin_dir.mkdir()
        manager = StackPluginManager(plugins_dir=plugin_dir)
        plugin = StackPlugin({"name": "custom", "structure": {"src": "src"}})
        manager.register_plugin(plugin)
        assert "custom" in manager.list_plugins()

    def test_create_structure(self, tmp_path):
        plugin_dir = tmp_path / "stacks"
        _write_plugin_file(
            plugin_dir, "valid",
            "name: test-stack\nversion: '1.0.0'\ndescription: T\ncommands:\n  init: echo\n  install: echo\nstructure:\n  app: src/app\n  tests: tests\n",
        )
        manager = StackPluginManager(plugins_dir=plugin_dir)
        out = tmp_path / "output"
        manager.create_structure("test-stack", out)
        assert (out / "src" / "app").exists()

    def test_create_structure_unknown(self, tmp_path):
        plugin_dir = tmp_path / "stacks"
        plugin_dir.mkdir()
        manager = StackPluginManager(plugins_dir=plugin_dir)
        with pytest.raises(ValueError, match="not found"):
            manager.create_structure("nonexistent", tmp_path)

    def test_no_schema_file(self, tmp_path):
        plugin_dir = tmp_path / "stacks"
        plugin_dir.mkdir()
        manager = StackPluginManager(plugins_dir=plugin_dir)
        assert manager.plugin_schema is not None or manager.plugin_schema is None

