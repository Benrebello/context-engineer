"""Services responsible for project status and assistant flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from core.engine import ContextEngine
from core.project_analyzer import ProjectAnalyzer


class ProjectStatusService:
    """Aggregates project status information for CLI commands."""

    def __init__(self, prompt_service: Any, config_service: Any | None = None) -> None:
        self.prompt_service = prompt_service
        self.config_service = config_service
        template_dir = Path(__file__).parent.parent / "templates" / "status"
        self.template_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _build_suggestions(
        self,
        engine: ContextEngine,
        assistant_context: dict,
        pattern_context: dict,
    ) -> dict[str, list]:
        suggestions: dict[str, list] = {"patterns": [], "cache": []}
        if pattern_context:
            suggestions["patterns"] = engine.pattern_library.suggest_patterns(pattern_context)
        cache_query = {
            "stack": pattern_context.get("stack", []),
            "requirements": assistant_context.get("requirements", []),
            "tags": assistant_context.get("tags", []),
            "next_focus": assistant_context.get("next_focus"),
            "project": assistant_context.get("project_name"),
        }
        suggestions["cache"] = engine.cache.search_similar(cache_query, limit=3)
        return suggestions

    @staticmethod
    def _build_status_view(state: dict, project_name: str) -> dict:
        completion = state.get("completion_status", {})
        prp_phases = state.get("prp_phases", {})
        prp_completed = sum(1 for phase in prp_phases.values() if phase.get("exists"))
        prd_path = state.get("prd_path")
        prd_filename = Path(prd_path).name if prd_path else None
        return {
            "project_name": project_name,
            "completion_status": completion,
            "has_prd": state.get("has_prd", False),
            "prd_path": prd_path,
            "prd_filename": prd_filename,
            "has_prps": state.get("has_prps", False),
            "prp_completed": prp_completed,
            "prp_total": len(prp_phases),
            "has_tasks": state.get("has_tasks", False),
            "task_count": state.get("task_count", 0),
            "suggestions": state.get("suggestions", []),
            "total_steps": 5,
            "completed_steps": sum(1 for value in completion.values() if value),
            "phase_names": {
                "F0": "Plan",
                "F1": "Scaffold",
                "F2": "Data Model",
                "F3": "API Contracts",
                "F4": "UX Flows",
                "F5": "Implementation",
                "F6": "Quality",
                "F7": "Observability",
                "F8": "Security",
                "F9": "CI/CD",
                "F10": "Rollout",
                "F11": "Maintenance",
            },
            "prp_phases": prp_phases,
        }

    def _resolve_engine(
        self,
        engine: ContextEngine | None,
        enable_ai: bool | None,
        embedding_model: str | None,
    ) -> ContextEngine | None:
        if engine:
            return engine
        if enable_ai is None and embedding_model is None:
            return None
        return ContextEngine(use_transformers=enable_ai, embedding_model=embedding_model)

    def gather_status_data(
        self,
        project_path: Path,
        *,
        engine: ContextEngine | None = None,
        enable_ai: bool | None = None,
        embedding_model: str | None = None,
        include_suggestions: bool = True,
    ) -> dict:
        analyzer = ProjectAnalyzer(project_path)
        state = analyzer.analyze_project_state()
        assistant_context = analyzer.build_assistant_context()
        assistant_context["project_name"] = project_path.name
        metrics = analyzer.get_project_metrics()

        status_view = self._build_status_view(state, project_path.name)

        pattern_context = assistant_context.get("pattern_context", {})
        suggestions: dict[str, list[dict]] = {"patterns": [], "cache": []}
        if include_suggestions:
            try:
                resolved_engine = self._resolve_engine(engine, enable_ai, embedding_model)
                if resolved_engine:
                    suggestions = self._build_suggestions(resolved_engine, assistant_context, pattern_context)
            except Exception:
                suggestions = {"patterns": [], "cache": []}

        return {
            "project_path": project_path,
            "state": state,
            "status_view": status_view,
            "assistant_context": assistant_context,
            "metrics": metrics,
            "pattern_suggestions": suggestions["patterns"],
            "cache_suggestions": suggestions["cache"],
        }

    def format_status_text(self, data: dict) -> str:
        try:
            template = self.template_env.get_template("status_report.txt.j2")
            return template.render(
                assistant_context=data["assistant_context"],
                status_view=data["status_view"],
                metrics=data["metrics"],
            )
        except TemplateNotFound:
            msg = "Template not found: status_report.txt.j2"
            raise FileNotFoundError(msg) from None

    def format_checklist_text(self, status_view: dict) -> str:
        try:
            template = self.template_env.get_template("checklist_report.txt.j2")
            return template.render(status_view=status_view)
        except TemplateNotFound:
            msg = "Template not found: checklist_report.txt.j2"
            raise FileNotFoundError(msg) from None

    def render_assist_intro(self, data: dict, *, output_format: str = "text") -> str:
        """Render assistant intro in the requested format (text or html)."""
        template_name = "assist_intro.txt.j2"
        if output_format.lower() == "html":
            template_name = "assist_intro.html.j2"
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**data)
        except TemplateNotFound:
            msg = f"Template not found: {template_name}"
            raise FileNotFoundError(msg) from None

    def run_assistant_flow(
        self,
        project_path: Path,
        *,
        engine: ContextEngine | None = None,
        enable_ai: bool | None = None,
        embedding_model: str | None = None,
    ) -> dict:
        analyzer = ProjectAnalyzer(project_path)
        state = analyzer.analyze_project_state()
        assistant_context = analyzer.build_assistant_context()
        assistant_context["project_name"] = project_path.name
        metrics = analyzer.get_project_metrics()
        status_view = self._build_status_view(state, project_path.name)
        pattern_context = assistant_context.get("pattern_context", {})
        resolved_engine = self._resolve_engine(engine, enable_ai, embedding_model)
        suggestions: dict[str, list] = {"patterns": [], "cache": []}
        if resolved_engine:
            suggestions = self._build_suggestions(resolved_engine, assistant_context, pattern_context)
        return {
            "project_path": project_path,
            "state": state,
            "status_view": status_view,
            "assistant_context": assistant_context,
            "metrics": metrics,
            "pattern_suggestions": suggestions["patterns"],
            "cache_suggestions": suggestions["cache"],
        }
