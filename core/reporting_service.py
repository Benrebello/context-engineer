"""Reporting helpers extracted from the CLI."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from .metrics import MetricsCollector, ProjectMetrics


class ReportingService:
    """Provides metrics aggregation and dashboard rendering utilities."""

    def __init__(self, metrics_collector: MetricsCollector) -> None:
        """
        Initialize the reporting service.

        Args:
            metrics_collector: Collector used to load metrics and ROI information.
        """
        self.metrics_collector = metrics_collector
        template_dir = Path(__file__).parent.parent / "templates" / "reporting"
        self.template_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def analyze_efficiency(self, metrics: ProjectMetrics) -> dict:
        """
        Analyze project efficiency based on collected metrics.

        Returns:
            Dictionary containing risk assessments and overall score.
        """
        rework_risk = "low"
        if metrics.rework_rate > 30:
            rework_risk = "high"
        elif metrics.rework_rate > 15:
            rework_risk = "medium"

        completion_risk = "low"
        if metrics.task_completion_rate < 50:
            completion_risk = "high"
        elif metrics.task_completion_rate < 70:
            completion_risk = "medium"

        overall_score = (
            (100 - metrics.rework_rate * 2)
            + metrics.task_completion_rate
            + metrics.test_coverage_achieved / 10
            + metrics.code_quality_score * 10
        ) / 4

        return {
            "rework_risk": rework_risk,
            "completion_risk": completion_risk,
            "overall_score": overall_score,
        }

    def load_project_metrics(self, project_name: str) -> tuple[ProjectMetrics, dict, dict]:
        """
        Load metrics, analysis and ROI information for a project.

        Returns:
            Tuple with (ProjectMetrics, analysis dict, ROI dict).
        """
        metrics = self.metrics_collector.load_metrics(project_name)
        analysis = self.analyze_efficiency(metrics)
        roi_metrics = self.metrics_collector.get_roi_metrics(project_name)
        return metrics, analysis, roi_metrics

    def load_global_metrics(
        self, stack_filter: str | None = None
    ) -> tuple[list[ProjectMetrics], dict]:
        """
        Load aggregated metrics across projects.

        Args:
            stack_filter: Optional stack identifier to filter projects.

        Returns:
            Tuple with the list of project metrics and average metrics dictionary.
        """
        all_metrics = self.metrics_collector.get_all_metrics()
        if stack_filter:
            all_metrics = [
                m for m in all_metrics if hasattr(m, "stack") and m.stack == stack_filter
            ]
        avg_metrics = self.metrics_collector.get_average_metrics()
        return all_metrics, avg_metrics

    def render_project_dashboard_html(
        self,
        project_name: str,
        metrics: ProjectMetrics,
        analysis: dict,
        roi_metrics: dict,
    ) -> str:
        """
        Render an HTML dashboard for a single project.
        """
        try:
            template = self.template_env.get_template("project_dashboard.html.j2")
            return template.render(
                project_name=project_name,
                metrics=metrics,
                analysis=analysis,
                roi_metrics=roi_metrics,
            )
        except TemplateNotFound:
            msg = "Template not found: project_dashboard.html.j2"
            raise FileNotFoundError(msg) from None

    def render_global_dashboard_html(
        self,
        all_metrics: list[ProjectMetrics],
        avg_metrics: dict,
        stack_filter: str | None = None,
    ) -> str:
        """
        Render an HTML dashboard aggregating multiple projects.
        """
        filter_text = f"Stack filtrada: {stack_filter}" if stack_filter else "Todas as stacks"
        try:
            template = self.template_env.get_template("global_dashboard.html.j2")
            return template.render(
                filter_text=filter_text,
                avg_metrics=avg_metrics,
                all_metrics=all_metrics,
            )
        except TemplateNotFound:
            msg = "Template not found: global_dashboard.html.j2"
            raise FileNotFoundError(msg) from None
