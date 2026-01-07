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

