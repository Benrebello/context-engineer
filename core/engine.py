"""
Main Context Engineer Engine
Orchestrates PRD/PRP generation and Task creation
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path

import yaml
from jinja2 import TemplateNotFound

from .cache import IntelligenceCache
from .metrics import MetricsCollector
from .pattern_library import PatternLibrary
from .planning import EffortEstimator
from .stack_plugins import StackPlugin, StackPluginManager
from .template_engine import TemplateEngine
from .userstory_integration import TaskGenerator, UserStoryRefiner
from .validators import PRPValidator

logger = logging.getLogger(__name__)


class ContextEngine:
    """Main engine for Context Engineer framework"""

    def __init__(
        self,
        templates_dir: Path | None = None,
        patterns_dir: Path | None = None,
        schemas_dir: Path | None = None,
        cache_dir: Path | None = None,
        use_transformers: bool = False,
        embedding_model: str | None = None,
    ):
        """
        Initialize Context Engine

        Args:
            templates_dir: Directory containing templates
            patterns_dir: Directory containing patterns
            schemas_dir: Directory containing JSON schemas
            cache_dir: Directory for intelligence cache
            use_transformers: Whether to enable transformer search in IntelligenceCache
        """
        base_dir = Path(__file__).parent.parent

        self.templates_dir = templates_dir or base_dir / "templates"
        self.patterns_dir = patterns_dir or base_dir / "patterns"
        self.schemas_dir = schemas_dir or base_dir / "schemas"
        self.cache_dir = cache_dir or base_dir / ".cache"

        # Initialize components
        self.template_engine = TemplateEngine(self.templates_dir)
        self.pattern_library = PatternLibrary(self.patterns_dir)
        self.validator = PRPValidator(self.schemas_dir)
        self.userstory_refiner = UserStoryRefiner()
        self.task_generator = TaskGenerator(self.userstory_refiner)
        self.cache = IntelligenceCache(self.cache_dir, use_transformers=use_transformers, model_name=embedding_model)

        # Initialize stack plugin manager
        stacks_dir = base_dir / "stacks"
        self.stack_plugin_manager = StackPluginManager(stacks_dir)

        # Initialize effort estimator
        metrics_collector = MetricsCollector(self.cache_dir.parent / "metrics")
        self.effort_estimator = EffortEstimator(metrics_collector)
        self.metrics_collector = metrics_collector

    def init_project(self, template: str, project_name: str, stack: str, output_dir: Path, **variables) -> dict:
        """
        Initialize a new project from template

        Args:
            template: Template name to use
            project_name: Name of the project
            stack: Technology stack
            output_dir: Output directory
            **variables: Additional template variables

        Returns:
            Dictionary with initialization results
        """
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        project_vars = {"project_name": project_name, "stack": stack, **variables}

        # Create directory structure based on stack
        created_dirs = []
        stack_plugin = self.stack_plugin_manager.get_plugin(stack)
        if stack_plugin:
            try:
                self.stack_plugin_manager.create_structure(stack, output_dir)
                structure = stack_plugin.get_structure()
                created_dirs = list(structure.values())
                # Create __init__.py files for Python projects
                if stack.startswith("python"):
                    for dir_path in structure.values():
                        init_file = output_dir / dir_path / "__init__.py"
                        if not init_file.exists():
                            init_file.parent.mkdir(parents=True, exist_ok=True)
                            init_file.write_text('"""Module initialization"""\n', encoding="utf-8")
            except Exception as e:
                logger.warning("Could not create stack structure: %s", e, exc_info=True)

        # Create basic project files
        created_files = self._create_basic_project_files(output_dir, project_name, stack, stack_plugin)

        # Ensure metrics file exists for this project
        metrics_file = self.metrics_collector.metrics_dir / f"{project_name}.json"
        if not metrics_file.exists():
            try:
                self.metrics_collector.record_project_start(project_name)
            except Exception as metrics_error:
                logger.warning("Could not initialize metrics for %s: %s", project_name, metrics_error)

        phase_durations: list[float] = []

        def _record_phase_metrics(
            phase_id: str, duration_seconds: float, success: bool, error_message: str | None
        ) -> None:
            """Capture per-phase metrics for observability."""
            phase_durations.append(duration_seconds)
            try:
                self.metrics_collector.record_phase_generation(
                    project_name=project_name,
                    phase_id=phase_id,
                    duration_seconds=duration_seconds,
                    success=success,
                    error_message=error_message,
                )
            except Exception as metrics_error:
                logger.warning("Could not record metrics for %s: %s", phase_id, metrics_error)

        # Generate PRP templates
        result = self.template_engine.generate_project(
            template_name=template,
            variables=project_vars,
            output_dir=output_dir,
            stack_plugin_manager=self.stack_plugin_manager,
            phase_metrics_callback=_record_phase_metrics,
        )

        if phase_durations:
            total_minutes = sum(phase_durations) / 60
            try:
                self.metrics_collector.record_prp_generation(project_name, total_minutes)
            except Exception as metrics_error:
                print(f"Warning: Could not record PRP generation time: {metrics_error}")

        # Add created directories and files to result
        result["created_directories"] = created_dirs
        result["created_files"] = created_files
        result["stack_structure_created"] = len(created_dirs) > 0

        return result

    def _create_basic_project_files(
        self, output_dir: Path, project_name: str, stack: str, stack_plugin: StackPlugin | None
    ) -> list[str]:
        """
        Create basic project files (README, .gitignore, etc.) based on stack

        Args:
            output_dir: Output directory
            project_name: Project name
            stack: Stack name
            stack_plugin: Optional StackPlugin instance

        Returns:
            List of created file paths
        """
        created_files = []
        stack_flags = {
            "is_python": stack.startswith("python"),
            "is_node": stack.startswith("node"),
            "is_vue": stack == "vue3",
            "is_go": stack.startswith("go"),
        }

        # Create README.md via template engine
        readme_context = {
            "project_name": project_name,
            "stack": stack,
            "stack_description": stack_plugin.description if stack_plugin else "",
            "stack_structure": stack_plugin.get_structure() if stack_plugin else {},
            "stack_commands": stack_plugin.commands if stack_plugin else {},
            "init_command": stack_plugin.get_init_command() if stack_plugin else "",
            "install_command": stack_plugin.get_install_command([]) if stack_plugin else "",
        }
        readme_content = self.template_engine.render("base/files/readme.md.j2", readme_context)
        readme_path = output_dir / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")
        created_files.append(str(readme_path))

        # Create .gitignore based on stack
        gitignore_content = self.template_engine.render("base/files/gitignore.j2", stack_flags)
        gitignore_path = output_dir / ".gitignore"
        gitignore_path.write_text(gitignore_content, encoding="utf-8")
        created_files.append(str(gitignore_path))

        # Create .env.example if applicable
        if stack.startswith("python") or stack.startswith("node"):
            env_example_content = self.template_engine.render(
                "base/files/env.example.j2",
                {
                    "is_python": stack.startswith("python"),
                    "is_node": stack.startswith("node"),
                    "is_vue": stack == "vue3",
                },
            )
            env_example_path = output_dir / ".env.example"
            env_example_path.write_text(env_example_content, encoding="utf-8")
            created_files.append(str(env_example_path))

        # Create LICENSE (MIT by default)
        license_content = self.template_engine.render(
            "base/files/license.md.j2",
            {"project_name": project_name, "current_year": datetime.now(UTC).year},
        )
        license_path = output_dir / "LICENSE"
        license_path.write_text(license_content, encoding="utf-8")
        created_files.append(str(license_path))

        # Stack-specific files
        if stack.startswith("python"):
            pyproject_content = self.template_engine.render(
                "base/files/pyproject.toml.j2",
                {
                    "project_slug": project_name.lower().replace(" ", "-"),
                    "stack_dependencies": stack_plugin.dependencies if stack_plugin else [],
                },
            )
            pyproject_path = output_dir / "pyproject.toml"
            pyproject_path.write_text(pyproject_content, encoding="utf-8")
            created_files.append(str(pyproject_path))
        elif stack.startswith("node") or stack == "vue3":
            scripts = []
            if stack_plugin:
                for name, command in stack_plugin.commands.items():
                    if command:
                        scripts.append({"name": name, "command": command})
            dependencies = []
            if stack_plugin:
                for dep in stack_plugin.dependencies:
                    if ">=" in dep:
                        pkg, version = dep.split(">=", 1)
                        dependencies.append({"name": pkg.strip(), "version": f">={version.strip()}"})
                    else:
                        dependencies.append({"name": dep.strip(), "version": "*"})
            package_json_content = self.template_engine.render(
                "base/files/package.json.j2",
                {
                    "project_slug": project_name.lower().replace(" ", "-"),
                    "scripts": scripts,
                    "dependencies": dependencies,
                },
            )
            package_json_path = output_dir / "package.json"
            package_json_path.write_text(package_json_content, encoding="utf-8")
            created_files.append(str(package_json_path))

        return created_files

    def generate_prd(self, _input_file: Path, output_dir: Path) -> dict:
        """
        Generate PRD from input file

        Args:
            input_file: Input file with product idea
            output_dir: Output directory for PRD files

        Returns:
            Dictionary with generation results
        """
        # This would integrate with Agente_PRD_360.md
        # For now, return structure
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        return {
            "success": True,
            "prd_file": str(output_dir / "PRD.md"),
            "prd_structured": str(output_dir / "prd_structured.json"),
        }

    def generate_prps(self, prd_file: Path, output_dir: Path, _parallel: bool = False) -> dict:
        """
        Generate PRPs from PRD

        Args:
            prd_file: Path to PRD structured JSON
            output_dir: Output directory for PRPs
            parallel: Whether to generate phases in parallel

        Returns:
            Dictionary with generation results
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load PRD
        with open(prd_file, encoding="utf-8") as f:
            json.load(f)

        # This would integrate with Agente_PRP_Orquestrador.md
        # For now, return structure
        phases = []
        for i in range(10):  # F0-F9
            phase_file = output_dir / f"0{i}_phase_{i}.md"
            phases.append(str(phase_file))

        return {"success": True, "phases": phases, "prd_used": str(prd_file)}

    def generate_tasks(self, prps_dir: Path, output_dir: Path) -> dict:
        """
        Generate Tasks from PRPs

        Args:
            prps_dir: Directory containing PRP files
            output_dir: Output directory for Tasks

        Returns:
            Dictionary with generation results
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load PRPs
        prp_files = list(prps_dir.glob("*.json")) + list(prps_dir.glob("*.md"))
        prps_data = []

        for prp_file in prp_files:
            try:
                if prp_file.suffix == ".json":
                    with open(prp_file, encoding="utf-8") as f:
                        prps_data.append(json.load(f))
                else:
                    # Parse markdown with YAML frontmatter
                    content = prp_file.read_text(encoding="utf-8")
                    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
                    if match:
                        prps_data.append(yaml.safe_load(match.group(1)))
            except Exception as e:
                print(f"Error loading PRP {prp_file}: {e}")

        # Generate tasks (this would use actual FRs from PRD)
        tasks: list[str] = []
        # Placeholder - would iterate through FRs and generate tasks

        return {"success": True, "tasks": tasks, "tasks_dir": str(output_dir)}

    def check_dependencies(self, tasks_dir: Path) -> dict:
        """
        Check dependencies between tasks

        Args:
            tasks_dir: Directory containing task files

        Returns:
            Dictionary with dependency check results
        """
        task_files = list(tasks_dir.glob("*.json"))
        errors = []

        # Load all tasks and check dependencies
        tasks = {}
        for task_file in task_files:
            try:
                with open(task_file, encoding="utf-8") as f:
                    task_data = json.load(f)
                    task_id = task_data.get("task_id")
                    if task_id:
                        tasks[task_id] = task_data
            except Exception as e:
                errors.append(f"Error loading {task_file}: {e}")

        # Check dependencies
        for task_id, task in tasks.items():
            inputs = task.get("inputs", [])
            for input_ref in inputs:
                # Check if referenced task exists
                if input_ref.startswith("TASK."):
                    ref_task_id = input_ref.replace("TASK.", "").replace(".md", "")
                    if ref_task_id not in tasks:
                        errors.append(f"Task {task_id} depends on {ref_task_id} which doesn't exist")

        return {"valid": len(errors) == 0, "errors": errors}

    def suggest_patterns(self, context: dict) -> list[dict]:
        """
        Suggest patterns based on context

        Args:
            context: Project context

        Returns:
            List of suggested patterns
        """
        return self.pattern_library.suggest_patterns(context)

    def validate_prps(self, prps_dir: Path, prd_file: Path | None = None) -> dict:
        """
        Validate all PRPs

        Args:
            prps_dir: Directory containing PRP files
            prd_file: Optional PRD file for consistency check

        Returns:
            Validation results
        """
        return self.validator.validate_all(prps_dir, prd_file)

    def record_task_completion(self, project_name: str, task_file: Path, success: bool, rework: bool = False) -> None:
        """
        Record task completion and update cache/metrics (Feedback Loop)

        This method closes the feedback loop by:
        1. Updating pattern success rate in IntelligenceCache
        2. Recording metrics in MetricsCollector
        3. Learning from successful/failed patterns

        Args:
            task_file: Path to task file (JSON or MD)
            project_name: Name of the project
            success: Whether task was successful
            rework: Whether task required rework (indicates pattern issues)
        """
        try:
            # Load task data
            if task_file.suffix == ".json":
                with open(task_file, encoding="utf-8") as f:
                    task_data = json.load(f)
            else:
                # Try to extract JSON from markdown
                content = task_file.read_text(encoding="utf-8")
                match = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
                if match:
                    task_data = json.loads(match.group(1))
                else:
                    # Try YAML frontmatter
                    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
                    if match:
                        task_data = yaml.safe_load(match.group(1))
                    else:
                        logger.warning("Could not parse task file: %s", task_file)
                        return

            task_id = task_data.get("task_id", task_file.stem)
            metadata = task_data.get("metadata", {})
            used_pattern_id = metadata.get("used_pattern_id")

            # 1. Update IntelligenceCache (Pattern Learning)
            if used_pattern_id:
                # Update success rate (negative if rework required)
                pattern_success = success and not rework
                self.cache.update_success_rate(used_pattern_id, pattern_success)
                logger.info("Cache updated: Pattern %s success=%s", used_pattern_id, pattern_success)

            # 2. Update MetricsCollector (Project Metrics)
            # Record task completion
            # Note: This requires knowing total tasks - simplified for now
            # In production, this should track incrementally

            # Calculate rework rate if applicable
            if rework:
                # Increment rework count
                metrics = self.metrics_collector.load_metrics(project_name)
                # Simple rework rate calculation (would need more sophisticated tracking)
                if hasattr(metrics, "rework_count"):
                    metrics.rework_count = getattr(metrics, "rework_count", 0) + 1
                else:
                    metrics.rework_rate = 0.1  # Initial estimate
                self.metrics_collector.save_metrics(metrics)

            # Record completion
            if success:
                metrics = self.metrics_collector.load_metrics(project_name)
                metrics.completed_tasks = getattr(metrics, "completed_tasks", 0) + 1
                if metrics.total_tasks > 0:
                    metrics.task_completion_rate = metrics.completed_tasks / metrics.total_tasks * 100
                self.metrics_collector.save_metrics(metrics)

            # Record category-specific rework for Confidence Adjustment
            task_category = metadata.get("category") or task_data.get("category", "")
            if task_category:
                self.metrics_collector.record_rework(project_name, task_category, rework)

            logger.info("Feedback Loop Closed: Task %s success=%s, rework=%s", task_id, success, rework)

        except Exception as e:
            logger.error("Error recording task completion: %s", e, exc_info=True)

    def compress_context(
        self,
        files: list[Path],
        max_tokens: int = 100000,
        preserve_core: bool = True,
        project_name: str | None = None,
    ) -> dict[str, str]:
        """
        Context Pruning: Compress context to fit within token limits

        This method implements "sanfinitização de contexto" - intelligently
        reduces context size while preserving critical information.

        Tracks ROI metrics (token savings) when project_name is provided.

        Args:
            files: List of file paths to compress
            max_tokens: Maximum token count (approximate)
            preserve_core: Whether to preserve core context (PRD, current phase)
            project_name: Optional project name for ROI tracking

        Returns:
            Dictionary mapping file paths to compressed content
        """
        compressed = {}
        total_size = 0
        original_total_tokens = 0
        compressed_total_tokens = 0

        # Core files that should always be preserved (not compressed)
        core_patterns = [
            "PRD.md",
            "prd_structured.json",
            "execution_map.md",
            "TASK.FR-",
            "TASK.US-",
        ]

        for file_path in files:
            if not file_path.exists():
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                file_size = len(content)

                # Check if it's a core file
                is_core = preserve_core and any(pattern in file_path.name for pattern in core_patterns)

                # Estimate tokens (rough: 1 token ≈ 4 characters)
                estimated_tokens = file_size // 4
                original_total_tokens += estimated_tokens

                if is_core:
                    # Preserve core files fully
                    compressed[str(file_path)] = content
                    total_size += estimated_tokens
                    compressed_total_tokens += estimated_tokens
                elif total_size + estimated_tokens > max_tokens:
                    # Need to compress this file
                    compressed_content = self._compress_file_content(content, file_path)
                    compressed_tokens = len(compressed_content) // 4
                    compressed[str(file_path)] = compressed_content
                    total_size += compressed_tokens
                    compressed_total_tokens += compressed_tokens
                else:
                    # Can include fully
                    compressed[str(file_path)] = content
                    total_size += estimated_tokens
                    compressed_total_tokens += estimated_tokens
            except TemplateNotFound:
                msg = f"Template not found while reading {file_path}"
                raise FileNotFoundError(msg)
            except Exception as exc:
                msg = f"Unable to read file {file_path}: {exc}"
                raise FileNotFoundError(msg) from exc

        # Track ROI metrics if project_name provided
        if project_name and original_total_tokens > 0:
            tokens_saved = original_total_tokens - compressed_total_tokens
            if tokens_saved > 0:
                self.metrics_collector.record_context_pruning(project_name, tokens_saved, compressed_total_tokens)

        return compressed

    def _compress_log_content(self, content: str) -> str:
        """Compress log content by keeping recent lines"""
        lines = content.split("\n")
        # Keep last 100 lines
        return "\n".join(lines[-100:]) + f"\n\n[Compressed: {len(lines)} total lines, showing last 100]"

    def _compress_json_metrics(self, content: str) -> str | None:
        """Compress JSON metrics by summarizing"""
        try:
            import json

            data = json.loads(content)
            if isinstance(data, dict):
                summary = {
                    "summary": "Compressed metrics",
                    "keys": list(data.keys())[:10],
                    "total_keys": len(data),
                }
                return json.dumps(summary, indent=2)
        except Exception:
            pass
        return None

    def _compress_markdown_content(self, content: str) -> str:
        """Compress markdown by preserving headers and structure"""
        lines = content.split("\n")
        compressed_lines = []
        in_code_block = False

        for line in lines:
            if line.startswith("#"):
                compressed_lines.append(line)
            elif line.startswith("```"):
                compressed_lines.append(line)
                in_code_block = not in_code_block
            elif in_code_block:
                if len(compressed_lines) < 500:
                    compressed_lines.append(line)
            elif any(marker in line for marker in ["##", "**", "", "", ""]):
                compressed_lines.append(line)

        if len(compressed_lines) < len(lines):
            compressed_lines.append(f"\n\n[Compressed: {len(lines)} total lines, showing key sections]")
        return "\n".join(compressed_lines[:500])

    def _compress_file_content(self, content: str, file_path: Path) -> str:
        """
        Compress a single file's content
        """
        # Strategy 1: Log files
        if "log" in file_path.name.lower() or ".log" in file_path.suffix:
            return self._compress_log_content(content)

        # Strategy 2: JSON metrics
        if file_path.suffix == ".json" and ("metric" in file_path.name.lower() or "cache" in file_path.name.lower()):
            result = self._compress_json_metrics(content)
            if result:
                return result

        # Strategy 3: Markdown
        if file_path.suffix == ".md":
            return self._compress_markdown_content(content)

        # Strategy 4: Default truncation
        if len(content) > 5000:
            return content[:5000] + f"\n\n[Compressed: {len(content)} total chars, showing first 5000]"

        return content
