"""
Project Analyzer - Analyzes project state and provides intelligent suggestions
"""

import json
from pathlib import Path
from typing import Any


class ProjectAnalyzer:
    """Analyzes project state and provides insights"""

    def __init__(self, project_dir: Path):
        """
        Initialize project analyzer

        Args:
            project_dir: Project directory to analyze
        """
        self.project_dir = Path(project_dir).resolve()
        self.config_path = self.project_dir / ".ce-config.json"
        self.project_config = self._load_project_config()
        self.stack = self._detect_stack()

    def analyze_project_state(self) -> dict[str, Any]:
        """
        Analyze current project state

        Returns:
            Dictionary with project state analysis
        """
        state: dict[str, Any] = {
            "has_prd": False,
            "has_prps": False,
            "has_tasks": False,
            "prd_path": None,
            "prps_dir": None,
            "tasks_dir": None,
            "prp_phases": {},
            "task_count": 0,
            "completion_status": {},
            "suggestions": [],
            "stack": None,
        }

        # Check for PRD
        prd_locations = [
            self.project_dir / "prd" / "PRD.md",
            self.project_dir / "prd" / "prd_structured.json",
            self.project_dir / "PRD.md",
            self.project_dir / "prd_structured.json",
        ]

        for prd_path in prd_locations:
            if prd_path.exists():
                state["has_prd"] = True
                state["prd_path"] = str(prd_path)
                break

        # Check for PRPs
        prps_locations = [
            self.project_dir / "prps",
            self.project_dir / "PRPs",
        ]

        for prps_dir in prps_locations:
            if prps_dir.exists() and prps_dir.is_dir():
                state["has_prps"] = True
                state["prps_dir"] = str(prps_dir)
                state["prp_phases"] = self._analyze_prp_phases(prps_dir)
                break

        # Check for Tasks
        tasks_locations = [
            self.project_dir / "tasks",
            self.project_dir / "TASKs",
        ]

        for tasks_dir in tasks_locations:
            if tasks_dir.exists() and tasks_dir.is_dir():
                state["has_tasks"] = True
                state["tasks_dir"] = str(tasks_dir)
                state["task_count"] = len(list(tasks_dir.glob("TASK.*")))
                break

        # Calculate completion status
        state["completion_status"] = self._calculate_completion_status(state)
        state["stack"] = self.stack

        # Generate suggestions
        state["suggestions"] = self._generate_suggestions(state)

        return state

    def build_assistant_context(self) -> dict[str, Any]:
        """
        Build contextual data for the conversational assistant.

        Returns:
            Dictionary containing stack, requirements, tags and actionable insights
        """
        prd_summary = self._load_prd_summary()
        stack = self.stack
        suggestions = []
        state = self.analyze_project_state()
        suggestions.extend(state.get("suggestions", []))

        incomplete_phases = [
            phase_id
            for phase_id, phase in state.get("prp_phases", {}).items()
            if not phase.get("exists")
        ]
        next_focus = incomplete_phases[0] if incomplete_phases else None

        pattern_context = {
            "stack": [stack] if stack else [],
            "requirements": [req.get("title", "") for req in prd_summary["requirements"]],
            "tags": prd_summary["tags"],
            "metadata": {
                "project": self.project_dir.name,
                "priority_requirements": [
                    req["id"] for req in prd_summary["requirements"] if req.get("priority") == "MUST"
                ],
            },
        }

        return {
            "stack": stack,
            "requirements": prd_summary["requirements"],
            "tags": prd_summary["tags"],
            "next_focus": next_focus,
            "suggestions": suggestions,
            "pattern_context": pattern_context,
            "task_count": state.get("task_count", 0),
            "has_tasks": state.get("has_tasks", False),
        }

    def _detect_stack(self) -> str | None:
        """
        Detect stack name based on configuration or project hints.

        Returns:
            Stack identifier if available
        """
        if self.project_config.get("stack"):
            return self.project_config["stack"]

        # Heuristics based on project files
        if (self.project_dir / "pyproject.toml").exists():
            return "python-fastapi"
        if (self.project_dir / "package.json").exists():
            return "node-react"
        if (self.project_dir / "vite.config.ts").exists() or (
            self.project_dir / "vite.config.js"
        ).exists():
            return "vue3"
        if (self.project_dir / "go.mod").exists():
            return "go-gin"
        return None

    def _analyze_prp_phases(self, prps_dir: Path) -> dict[str, dict[str, Any]]:
        """Analyze PRP phases"""
        phases = {}
        expected_phases = [
            "F0",
            "F1",
            "F2",
            "F3",
            "F4",
            "F5",
            "F6",
            "F7",
            "F8",
            "F9",
            "F10",
            "F11",
        ]

        for phase_id in expected_phases:
            phase_files = list(prps_dir.glob(f"{phase_id}_*"))
            if phase_files:
                phases[phase_id] = {
                    "exists": True,
                    "files": [str(f) for f in phase_files],
                    "valid": self._validate_prp_phase(phase_files[0]),
                }
            else:
                phases[phase_id] = {"exists": False, "files": [], "valid": False}

        return phases

    def _validate_prp_phase(self, phase_file: Path) -> bool:
        """Quick validation of PRP phase file"""
        try:
            content = phase_file.read_text(encoding="utf-8")
            # Basic validation - file should have content
            return len(content.strip()) > 100
        except Exception:
            return False

    def _calculate_completion_status(self, state: dict[str, Any]) -> dict[str, bool]:
        """Calculate completion status"""
        status = {
            "init": False,
            "prd": False,
            "prps": False,
            "tasks": False,
            "implementation": False,
        }

        # Check if project is initialized (has basic structure)
        if (self.project_dir / "README.md").exists():
            status["init"] = True

        status["prd"] = state["has_prd"]

        # PRPs are complete if we have at least F0-F4
        if state["has_prps"]:
            prp_phases = state["prp_phases"]
            completed_phases = sum(1 for p in prp_phases.values() if p.get("exists"))
            status["prps"] = completed_phases >= 5  # At least F0-F4

        status["tasks"] = state["has_tasks"] and state["task_count"] > 0

        # Implementation is started if there's code in src/
        if (self.project_dir / "src").exists():
            src_files = list((self.project_dir / "src").rglob("*.py")) + list(
                (self.project_dir / "src").rglob("*.ts")
            ) + list((self.project_dir / "src").rglob("*.tsx"))
            status["implementation"] = len(src_files) > 0

        return status

    def _generate_suggestions(self, state: dict[str, Any]) -> list[str]:
        """Generate intelligent suggestions based on state"""
        suggestions = []

        if not state["completion_status"]["init"]:
            suggestions.append(
                "Execute 'ce init' para inicializar o projeto com estrutura completa"
            )
            return suggestions

        if not state["has_prd"]:
            suggestions.append(
                "Execute 'ce generate-prd --interactive' para criar o PRD do projeto"
            )
            return suggestions

        if not state["has_prps"]:
            suggestions.append(
                "Execute 'ce generate-prps' para gerar os PRPs a partir do PRD"
            )
            return suggestions

        # Check PRP completion
        prp_phases = state["prp_phases"]
        incomplete_phases = [
            phase_id
            for phase_id, phase_info in prp_phases.items()
            if not phase_info.get("exists")
        ]

        if incomplete_phases:
            next_phase = incomplete_phases[0]
            suggestions.append(
                f"Complete a fase {next_phase}. Execute 'ce generate-prps --phase {next_phase}'"
            )

        if not state["has_tasks"]:
            suggestions.append(
                "Execute 'ce generate-tasks' para gerar tasks executáveis a partir dos PRPs"
            )
        elif state["task_count"] == 0:
            suggestions.append(
                "Execute 'ce generate-tasks' para gerar tasks executáveis"
            )

        # Check for validation
        if state["has_prps"]:
            suggestions.append(
                "Execute 'ce validate' para validar rastreabilidade dos PRPs"
            )

        return suggestions

    def get_project_metrics(self) -> dict[str, Any]:
        """Get project metrics"""
        metrics = {
            "story_points": 0,
            "rework_rate": 0.0,
            "test_coverage": 0.0,
            "task_completion_rate": 0.0,
        }

        try:
            from .metrics import MetricsCollector

            project_name = self.project_dir.name
            metrics_collector = MetricsCollector(self.project_dir / ".cache" / "metrics")

            try:
                project_metrics = metrics_collector.load_metrics(project_name)
                metrics["rework_rate"] = getattr(project_metrics, "rework_rate", 0.0)
                metrics["test_coverage"] = getattr(
                    project_metrics, "test_coverage_achieved", 0.0
                )
                metrics["task_completion_rate"] = getattr(
                    project_metrics, "task_completion_rate", 0.0
                )
            except Exception:
                pass  # Metrics not available yet

            # Calculate story points if tasks exist
            tasks_dir = None
            if (self.project_dir / "tasks").exists():
                tasks_dir = self.project_dir / "tasks"
            elif (self.project_dir / "TASKs").exists():
                tasks_dir = self.project_dir / "TASKs"

            if tasks_dir:
                metrics["story_points"] = self._estimate_story_points(tasks_dir)

        except Exception:
            pass

        return metrics

    def _load_project_config(self) -> dict[str, Any]:
        """Load .ce-config.json if available."""
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as config_file:
                    return json.load(config_file)
            except Exception:
                return {}
        return {}

    def _load_prd_summary(self) -> dict[str, Any]:
        """
        Load PRD structured data and extract requirements metadata.

        Returns:
            Dictionary containing requirement summary and inferred tags
        """
        prd_file = self.project_dir / "prd" / "prd_structured.json"
        if not prd_file.exists():
            prd_file = self.project_dir / "prd_structured.json"

        requirements: list[dict[str, Any]] = []
        tags: list[str] = []

        if prd_file.exists():
            try:
                with open(prd_file, encoding="utf-8") as f:
                    prd_data = json.load(f)
                    requirements = prd_data.get("functional_requirements", [])
                    tags = self._infer_tags_from_requirements(requirements)
            except Exception:
                requirements = []
                tags = []

        return {"requirements": requirements, "tags": tags}

    def _infer_tags_from_requirements(self, requirements: list[dict[str, Any]]) -> list[str]:
        """Infer simple tags from requirement titles/descriptions."""
        keywords = {
            "auth": "authentication",
            "login": "authentication",
            "payment": "payments",
            "checkout": "payments",
            "report": "analytics",
            "dashboard": "analytics",
            "notification": "notifications",
            "email": "communications",
        }
        detected = set()
        for req in requirements:
            target = (
                f"{req.get('title', '')} {req.get('description', '')}".lower()
            )
            for needle, tag in keywords.items():
                if needle in target:
                    detected.add(tag)
        return sorted(detected)

    def _estimate_story_points(self, tasks_dir: Path) -> int:
        """Estimate total story points from tasks"""
        try:
            from .metrics import MetricsCollector
            from .planning import EffortEstimator

            metrics_collector = MetricsCollector(self.project_dir / ".cache" / "metrics")
            estimator = EffortEstimator(metrics_collector)

            task_files = list(tasks_dir.glob("TASK.*.json")) + list(
                tasks_dir.glob("TASK.*.md")
            )

            total_points = 0
            for task_file in task_files[:10]:  # Limit to avoid performance issues
                try:
                    if task_file.suffix == ".json":
                        with open(task_file, encoding="utf-8") as f:
                            task = json.load(f)
                    else:
                        content = task_file.read_text(encoding="utf-8")
                        import re

                        match = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
                        if match:
                            task = json.loads(match.group(1))
                        else:
                            continue

                    points = estimator.estimate_effort_points(
                        task, "python-fastapi", self.project_dir.name
                    )
                    total_points += points
                except Exception:
                    continue

            return total_points
        except Exception:
            return 0
