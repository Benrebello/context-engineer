"""Tests for core.metrics module."""

import json
from pathlib import Path

import pytest

from core.metrics import MetricsCollector, ProjectMetrics, Feedback


@pytest.fixture()
def metrics_dir(tmp_path):
    d = tmp_path / "metrics"
    d.mkdir()
    return d


@pytest.fixture()
def collector(metrics_dir):
    return MetricsCollector(metrics_dir)


class TestProjectMetrics:
    def test_defaults(self):
        m = ProjectMetrics(project_name="test")
        assert m.project_name == "test"
        assert m.rework_rate == 0.0
        assert m.task_completion_rate == 0.0
        assert m.tokens_saved == 0
        assert m.tokens_used == 0
        assert m.estimated_cost_saved_usd == 0.0
        assert m.created_at != ""
        assert m.updated_at != ""

    def test_custom_values(self):
        m = ProjectMetrics(project_name="test", rework_rate=15.0, tokens_saved=1000)
        assert m.rework_rate == 15.0
        assert m.tokens_saved == 1000


class TestFeedback:
    def test_defaults(self):
        fb = Feedback(prp_phase="F1", quality="high", clarity="good", completeness="full", actionability="yes")
        assert fb.prp_phase == "F1"
        assert fb.created_at != ""


class TestMetricsCollector:
    def test_init_creates_dir(self, tmp_path):
        d = tmp_path / "new_metrics"
        MetricsCollector(d)
        assert d.exists()

    def test_record_project_start(self, collector):
        collector.record_project_start("my-project")
        metrics = collector.load_metrics("my-project")
        assert metrics.project_name == "my-project"

    def test_load_metrics_nonexistent(self, collector):
        metrics = collector.load_metrics("nonexistent")
        assert metrics.project_name == "nonexistent"

    def test_record_prp_generation_time(self, collector):
        collector.record_project_start("proj")
        collector.record_prp_generation_time("proj", 5.5)
        metrics = collector.load_metrics("proj")
        assert metrics.prp_generation_time_minutes == 5.5

    def test_record_phase_generation_success(self, collector):
        collector.record_project_start("proj")
        collector.record_phase_generation("proj", "F1", 2.0, True, None)
        metrics = collector.load_metrics("proj")
        assert metrics.total_phase_generations == 1

    def test_record_phase_generation_failure(self, collector):
        collector.record_project_start("proj")
        collector.record_phase_generation("proj", "F1", 1.0, False, "template error")
        metrics = collector.load_metrics("proj")
        assert metrics.failed_phase_generations == 1
        assert metrics.phase_failure_rate > 0

    def test_record_task_completion_success(self, collector):
        collector.record_project_start("proj")
        # Set total_tasks first
        m = collector.load_metrics("proj")
        m.total_tasks = 10
        collector.save_metrics(m)
        collector.record_task_completion("proj", "FR-001", True)
        metrics = collector.load_metrics("proj")
        assert metrics.completed_tasks == 1

    def test_record_task_completion_failure(self, collector):
        collector.record_project_start("proj")
        m = collector.load_metrics("proj")
        m.total_tasks = 5
        collector.save_metrics(m)
        collector.record_task_completion("proj", "FR-001", False)
        metrics = collector.load_metrics("proj")
        assert metrics.completed_tasks == 0

    def test_record_test_coverage(self, collector):
        collector.record_project_start("proj")
        collector.record_test_coverage("proj", 85.5)
        metrics = collector.load_metrics("proj")
        assert metrics.test_coverage_achieved == 85.5

    def test_record_code_quality(self, collector):
        collector.record_project_start("proj")
        collector.record_code_quality("proj", 9.2)
        metrics = collector.load_metrics("proj")
        assert metrics.code_quality_score == 9.2

    def test_record_rework(self, collector):
        collector.record_project_start("proj")
        collector.record_rework("proj", "security", True)
        collector.record_rework("proj", "security", False)
        metrics = collector.load_metrics("proj")
        assert "security" in metrics.category_rework_rates
        assert metrics.category_rework_rates["security"]["total"] == 2
        assert metrics.category_rework_rates["security"]["rework"] == 1

    def test_get_category_rework_rate(self, collector):
        collector.record_project_start("proj")
        collector.record_rework("proj", "api", True)
        collector.record_rework("proj", "api", True)
        collector.record_rework("proj", "api", False)
        rate = collector.get_category_rework_rate("proj", "api")
        assert abs(rate - 2 / 3) < 0.01

    def test_get_category_rework_rate_no_data(self, collector):
        rate = collector.get_category_rework_rate("proj", "unknown")
        assert rate == 0.0

    def test_record_context_pruning(self, collector):
        collector.record_project_start("proj")
        collector.record_context_pruning("proj", tokens_saved=500, cost_saved=0.0, tokens_used=2000)
        metrics = collector.load_metrics("proj")
        assert metrics.tokens_saved == 500
        assert metrics.tokens_used == 2000
        assert metrics.context_pruning_events == 1
        assert metrics.estimated_cost_saved_usd > 0

    def test_record_traceability_status(self, collector):
        collector.record_project_start("proj")
        collector.record_traceability_status("proj", tasks_with_commits=8, total_tasks=10)
        metrics = collector.load_metrics("proj")
        assert metrics.tasks_with_commits == 8
        assert metrics.traceability_gaps == 2

    def test_get_roi_metrics(self, collector):
        collector.record_project_start("proj")
        collector.record_context_pruning("proj", tokens_saved=1000, cost_saved=0.0, tokens_used=5000)
        roi = collector.get_roi_metrics("proj")
        assert "tokens_saved" in roi
        assert "savings_percentage" in roi
        assert roi["tokens_saved"] == 1000

    def test_get_roi_metrics_no_data(self, collector):
        roi = collector.get_roi_metrics("nonexistent")
        assert roi["tokens_saved"] == 0

    def test_save_feedback(self, collector):
        fb = Feedback(prp_phase="F1", quality="high", clarity="good", completeness="full", actionability="yes", comments="Nice")
        collector.save_feedback(fb)
        # Should not raise

    def test_get_all_metrics(self, collector):
        collector.record_project_start("proj1")
        collector.record_project_start("proj2")
        all_metrics = collector.get_all_metrics()
        assert len(all_metrics) >= 2

    def test_get_average_metrics(self, collector):
        collector.record_project_start("proj1")
        collector.record_project_start("proj2")
        avg = collector.get_average_metrics()
        assert "avg_task_completion_rate" in avg
        assert avg["total_projects"] == 2

    def test_get_average_metrics_empty(self, tmp_path):
        empty_dir = tmp_path / "empty_metrics"
        empty_dir.mkdir()
        c = MetricsCollector(empty_dir)
        avg = c.get_average_metrics()
        assert avg == {}

    def test_persistence(self, metrics_dir):
        c1 = MetricsCollector(metrics_dir)
        c1.record_project_start("proj")
        c1.record_test_coverage("proj", 75.0)

        c2 = MetricsCollector(metrics_dir)
        metrics = c2.load_metrics("proj")
        assert metrics.test_coverage_achieved == 75.0
