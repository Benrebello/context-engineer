"""
Stack Plugins System for Multi-Stack Support
"""

from pathlib import Path
from typing import Any

import yaml
from jsonschema import ValidationError
from jsonschema import validate as jsonschema_validate


class StackPlugin:
    """Represents a stack plugin"""

    def __init__(self, config: dict):
        """
        Initialize stack plugin

        Args:
            config: Stack configuration dictionary
        """
        self.name = config.get("name", "")
        self.version = config.get("version", "1.0.0")
        self.description = config.get("description", "")
        self.commands = config.get("commands", {})
        self.structure = config.get("structure", {})
        self.patterns = config.get("patterns", [])
        self.dependencies = config.get("dependencies", [])
        self.config = config

    def get_init_command(self) -> str:
        """Get initialization command"""
        return str(self.commands.get("init", ""))

    def get_install_command(self, deps: list[str]) -> str:
        """Get install command with dependencies"""
        install_cmd = self.commands.get("install", "")
        if deps:
            return f"{install_cmd} {' '.join(deps)}"
        return str(install_cmd)

    def get_test_command(self) -> str:
        """Get test command"""
        return str(self.commands.get("test", ""))

    def get_lint_command(self) -> str:
        """Get lint command"""
        return str(self.commands.get("lint", ""))

    def get_structure(self) -> dict[str, str]:
        """Get directory structure"""
        return dict(self.structure)


class StackPluginManager:
    """Manages stack plugins"""

    def __init__(self, plugins_dir: Path | None = None):
        """
        Initialize plugin manager

        Args:
            plugins_dir: Directory containing stack plugin files
        """
        base_dir = Path(__file__).parent.parent
        self.plugins_dir = plugins_dir or base_dir / "stacks"
        self.schemas_dir = base_dir / "schemas"
        self.plugin_schema_path = self.schemas_dir / "stack_plugin.schema.yaml"
        self.plugin_schema = self._load_plugin_schema()
        self.plugins: dict[str, Any] = {}
        self._load_plugins()

    def _load_plugin_schema(self) -> dict | None:
        """Load YAML schema for stack plugins."""
        if not self.plugin_schema_path.exists():
            print("Warning: Stack plugin schema not found; skipping validation.")
            return None

        with open(self.plugin_schema_path, encoding="utf-8") as schema_file:
            schema = yaml.safe_load(schema_file) or {}
            if not schema:
                print("Warning: Stack plugin schema is empty; skipping validation.")
                return None
            return schema

    def _load_plugins(self) -> None:
        """Load all stack plugins"""
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            return

        for plugin_file in self.plugins_dir.glob("*.yaml"):
            with open(plugin_file, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}

            self._validate_plugin_config(plugin_file, config)
            plugin = StackPlugin(config)
            self.plugins[plugin.name] = plugin

    def _validate_plugin_config(self, plugin_file: Path, config: dict) -> None:
        """Validate a stack plugin against the schema."""
        if not self.plugin_schema:
            return

        try:
            jsonschema_validate(instance=config, schema=self.plugin_schema)
        except ValidationError as exc:
            msg = f"Stack plugin '{plugin_file.name}' is invalid: {exc.message}"
            raise ValueError(msg) from exc

    def get_plugin(self, stack_name: str) -> StackPlugin | None:
        """
        Get plugin by name

        Args:
            stack_name: Name of the stack

        Returns:
            StackPlugin or None if not found
        """
        return self.plugins.get(stack_name)

    def list_plugins(self) -> list[str]:
        """List all available plugins"""
        return list(self.plugins.keys())

    def register_plugin(self, plugin: StackPlugin) -> None:
        """
        Register a new plugin

        Args:
            plugin: StackPlugin instance
        """
        self.plugins[plugin.name] = plugin

    def create_structure(self, stack_name: str, output_dir: Path) -> None:
        """
        Create directory structure for a stack

        Args:
            stack_name: Name of the stack
            output_dir: Output directory
        """
        plugin = self.get_plugin(stack_name)
        if not plugin:
            msg = f"Stack plugin '{stack_name}' not found"
            raise ValueError(msg)

        structure = plugin.get_structure()
        base_dir = Path(output_dir)

        for _dir_name, dir_path in structure.items():
            full_path = base_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
