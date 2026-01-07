"""
Template Engine for parametrized template generation
"""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class TemplateEngine:
    """Engine for rendering parametrized templates using Jinja2"""

    def __init__(self, template_dir: Path):
        """
        Initialize template engine

        Args:
            template_dir: Directory containing template files
        """
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, context: dict) -> str:
        """
        Render a template with given context

        Args:
            template_name: Name of template file (relative to template_dir)
            context: Variables to inject into template

        Returns:
            Rendered template content
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            msg = f"Template not found: {template_name}"
            raise FileNotFoundError(msg) from None

    def load_template_config(self, template_path: Path) -> dict:
        """
        Load template configuration from YAML file

        Args:
            template_path: Path to template.yaml file

        Returns:
            Template configuration dictionary
        """
        with open(template_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get_available_variables(self, template_config: dict) -> list[str]:
        """
        Extract available variables from template config

        Args:
            template_config: Template configuration dictionary

        Returns:
            List of variable names
        """
        variables = []
        if "variables" in template_config:
            for var_name, _var_config in template_config["variables"].items():
                variables.append(var_name)
        return variables

    def generate_project(
        self,
        template_name: str,
        variables: dict[str, Any],
        output_dir: Path,
        stack_plugin_manager: Any = None,
        phase_metrics_callback: Callable[[str, float, bool, str | None], None] | None = None,
    ) -> dict[str, Any]:
        """
        Generate complete project from template

        Args:
            template_name: Name of template to use
            variables: Project variables
            output_dir: Output directory for generated files
            stack_plugin_manager: Optional StackPluginManager instance for stack-specific commands
            phase_metrics_callback: Optional hook to receive per-phase metrics (phase_id, duration,
                success flag, optional error message)

        Returns:
            Dictionary with generation results
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        template_config_path = self.template_dir / template_name / "template.yaml"
        if not template_config_path.exists():
            msg = f"Template config not found: {template_config_path}"
            raise FileNotFoundError(msg)

        config = self.load_template_config(template_config_path)
        generated_files = []

        # Create a new environment with loader pointing to the specific template directory
        template_specific_dir = self.template_dir / template_name
        template_env = Environment(
            loader=FileSystemLoader(str(template_specific_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Load stack plugin if manager provided
        stack_plugin = None
        stack_commands = {}
        stack_structure = {}
        if stack_plugin_manager:
            stack_name = variables.get("stack")
            if stack_name:
                stack_plugin = stack_plugin_manager.get_plugin(stack_name)
                if stack_plugin:
                    stack_commands = stack_plugin.commands
                    stack_structure = stack_plugin.structure

        # Generate each phase
        for phase in config.get("phases", []):
            phase_id = phase.get("id")
            if not phase_id:
                continue

            start_time = time.perf_counter()
            success = True
            error_msg = None
            try:
                # Inject stack plugin data into variables
                phase_vars = {
                    **variables,
                    "stack_commands": stack_commands,
                    "stack_structure": stack_structure,
                    "stack_plugin": stack_plugin,
                }
                content = self.generate_phase(phase, phase_vars, template_env=template_env)

                # Determine output filename
                phase_name = phase_id.lower().replace("_", "-")
                output_file = output_dir / f"{phase_id}_{phase_name}.md"
                output_file.write_text(content, encoding="utf-8")
                generated_files.append(str(output_file))

            except Exception as e:
                success = False
                error_msg = str(e)
                print(f"Error generating phase {phase_id}: {e}")
                continue
            finally:
                if phase_metrics_callback:
                    elapsed = time.perf_counter() - start_time
                    phase_metrics_callback(phase_id, elapsed, success, error_msg)

        return {
            "success": True,
            "generated_files": generated_files,
            "template": template_name,
            "variables_used": variables,
        }

    def generate_phase(self, phase_config: dict[str, Any], variables: dict[str, Any], template_env: Any = None) -> str:
        """
        Generate a PRP phase from template

        Args:
            phase_config: Phase configuration from template.yaml
            variables: Project variables (may include stack_commands, stack_structure)
            template_env: Optional Jinja2 Environment (if None, uses self.env)

        Returns:
            Generated phase content
        """
        template_file = phase_config.get("template")
        if not template_file:
            msg = f"Phase {phase_config.get('id')} has no template"
            raise ValueError(msg)

        # Merge phase-specific variables with project variables
        phase_vars = {**variables}
        if "variables" in phase_config:
            for var_name, var_config in phase_config["variables"].items():
                phase_vars[var_name] = var_config.get("default")

        # Use provided environment or fall back to instance environment
        env = template_env or self.env
        try:
            template = env.get_template(template_file)
            return template.render(**phase_vars)
        except TemplateNotFound:
            msg = f"Template not found: {template_file}"
            raise FileNotFoundError(msg) from None
