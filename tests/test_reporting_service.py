"""
Tests for ReportingService aggregation and rendering logic.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from jinja2 import Environment

from core.metrics import ProjectMetrics
from core.reporting_service import ReportingService


class DummyTemplate:
    def __init__(self, marker: str):
        self.marker = marker

    def render(self, **context):
        payload = {**context}
        payload["__marker__"] = self.marker
        return str(payload)


class DummyTemplateEnv(Environment):
    def __init__(self):
        super().__init__()
        self.templates: dict[str, DummyTemplate] = {}

    def register(self, name: str) -> None:
        self.templates[name] = DummyTemplate(marker=name)

    def get_template(self, name: str | Any, parent: str | None = None, globals: dict[str, Any] | None = None) -> Any:
        # We only support string names in this dummy
        if not isinstance(name, str):
             raise TypeError("DummyTemplateEnv only supports string template names")
        if name not in self.templates:
            msg = f"Template not found: {name}"
            raise FileNotFoundError(msg)
        return self.templates[name]


@pytest.fixture
def metrics_collector():
    return MagicMock()


def _build_reporting_service(metrics_collector):
    service = ReportingService(metrics_collector=metrics_collector)
    dummy_env = DummyTemplateEnv()
    dummy_env.register("project_dashboard.html.j2")
    dummy_env.register("global_dashboard.html.j2")
    service.template_env = dummy_env
    return service, dummy_env


def _make_metrics(**overrides: Any) -> ProjectMetrics:
    # Explicitly constructing to satisfy mypy
    data = {
        "project_name": "alpha",
        "prp_generation_time_minutes": 25.0,
        "task_completion_rate": 80.0,
        "test_coverage_achieved": 85.0,
        "code_quality_score": 8.5,
        "completed_tasks": 10,
        "total_tasks": 12,
        "phase_generation_stats": {},
        "category_rework_rates": {}
    }
    data.update(overrides)
    # We cheat a bit here by using Any for unpacking if needed, 
    # but better to be explicit or use a helper that returns correct type
    return ProjectMetrics(**data) # type: ignore


def test_analyze_efficiency_risks_and_scores(metrics_collector) -> None:
    service, _ = _build_reporting_service(metrics_collector)

    metrics = _make_metrics(rework_rate=35.0, task_completion_rate=40.0)
    analysis = service.analyze_efficiency(metrics)

    assert analysis["rework_risk"] == "high"
    assert analysis["completion_risk"] == "high"
    assert analysis["overall_score"] > 0  # score calculation executed


def test_load_project_metrics_combines_data(metrics_collector) -> None:
    project_metrics = _make_metrics()
    roi = {"tokens_saved": 100}

    metrics_collector.load_metrics.return_value = project_metrics
    metrics_collector.get_roi_metrics.return_value = roi

    service, _ = _build_reporting_service(metrics_collector)

    result_metrics, result_analysis, result_roi = service.load_project_metrics("alpha")

    assert result_metrics is project_metrics
    assert result_analysis["completion_risk"] == "low"
    assert result_roi == roi
    metrics_collector.load_metrics.assert_called_once_with("alpha")
    metrics_collector.get_roi_metrics.assert_called_once_with("alpha")


def test_render_project_dashboard_uses_template(metrics_collector) -> None:
    service, env = _build_reporting_service(metrics_collector)
    metrics = _make_metrics()
    analysis = {"rework_risk": "low"}
    roi = {"tokens_saved": 50}

    rendered = service.render_project_dashboard_html(
        project_name="alpha", metrics=metrics, analysis=analysis, roi_metrics=roi
    )

    assert "project_dashboard.html.j2" in rendered
    assert "'project_name': 'alpha'" in rendered


def test_render_global_dashboard_uses_template(metrics_collector) -> None:
    service, env = _build_reporting_service(metrics_collector)
    all_metrics = [_make_metrics(project_name="beta")]
    avg_metrics = {"avg_prp_generation_time": 10}

    rendered = service.render_global_dashboard_html(
        all_metrics=all_metrics, avg_metrics=avg_metrics, stack_filter="python-fastapi"
    )

    assert "global_dashboard.html.j2" in rendered
    assert "python-fastapi" in rendered


def test_load_global_metrics_applies_filter(metrics_collector) -> None:
    metrics_python = _make_metrics(project_name="py", task_completion_rate=90)
    metrics_node = _make_metrics(project_name="node", task_completion_rate=60)

    # Simulate stored metrics with stack attributes via dynamic assignment (mock behavior)
    # Since ProjectMetrics might not have 'stack', we use setattr or type ignore
    setattr(metrics_python, "stack", "python-fastapi")
    setattr(metrics_node, "stack", "node-react")
    
    metrics_collector.get_all_metrics.return_value = [metrics_python, metrics_node]
    metrics_collector.get_average_metrics.return_value = {"avg_task_completion_rate": 75}

    service, _ = _build_reporting_service(metrics_collector)
    filtered, avg = service.load_global_metrics(stack_filter="python-fastapi")

    assert filtered == [metrics_python]
    assert avg["avg_task_completion_rate"] == 75
