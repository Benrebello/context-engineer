"""Tests for core.planning module."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.metrics import MetricsCollector
from core.planning import EffortEstimator, TaskComplexity


@pytest.fixture()
def metrics_collector(tmp_path):
    d = tmp_path / "metrics"
    d.mkdir()
    return MetricsCollector(d)


@pytest.fixture()
def estimator(metrics_collector):
    return EffortEstimator(metrics_collector)


class TestTaskComplexity:
    def test_fields(self):
        tc = TaskComplexity(
            artifacts_count=2,
            steps_count=5,
            gherkin_scenarios_count=3,
            dependencies_count=1,
            stack_complexity=0.3,
            category_complexity=0.5,
        )
        assert tc.artifacts_count == 2
        assert tc.steps_count == 5
        assert tc.gherkin_scenarios_count == 3
        assert tc.dependencies_count == 1
        assert tc.stack_complexity == 0.3
        assert tc.category_complexity == 0.5


class TestEffortEstimator:
    def test_calculate_complexity_minimal_task(self, estimator):
        task = {"task_id": "FR-001", "objective": "Simple task"}
        complexity = estimator.calculate_complexity(task, "python-fastapi")
        assert isinstance(complexity, TaskComplexity)
        assert complexity.stack_complexity == 0.3

    def test_calculate_complexity_with_steps(self, estimator):
        task = {
            "task_id": "FR-002",
            "objective": "Complex task",
            "steps": ["step1", "step2", "step3", "step4", "step5"],
            "artifacts": ["input1", "input2"],
            "gherkin_scenarios": [{"scenario": "s1"}, {"scenario": "s2"}],
            "dependencies": ["dep1"],
        }
        complexity = estimator.calculate_complexity(task, "python-fastapi")
        assert complexity.steps_count == 5
        assert complexity.artifacts_count == 2
        assert complexity.gherkin_scenarios_count == 2
        assert complexity.dependencies_count == 1

    def test_estimate_effort_points_returns_positive(self, estimator):
        task = {
            "task_id": "FR-001",
            "objective": "Basic task",
            "steps": ["step1"],
        }
        points = estimator.estimate_effort_points(task, "python-fastapi")
        assert points > 0

    def test_estimate_effort_points_complex_task(self, estimator):
        simple_task = {"task_id": "FR-001", "steps": ["s1"]}
        complex_task = {
            "task_id": "FR-002",
            "steps": [f"s{i}" for i in range(20)],
            "artifacts": [f"a{i}" for i in range(10)],
            "gherkin_scenarios": [{"scenario": f"sc{i}"} for i in range(10)],
            "dependencies": [f"d{i}" for i in range(5)],
        }
        simple_pts = estimator.estimate_effort_points(simple_task, "python-fastapi")
        complex_pts = estimator.estimate_effort_points(complex_task, "python-fastapi")
        assert complex_pts > simple_pts

    def test_estimate_with_project_name(self, estimator, metrics_collector):
        metrics_collector.record_project_start("test-proj")
        task = {"task_id": "FR-001", "steps": ["s1"]}
        points = estimator.estimate_effort_points(task, "python-fastapi", project_name="test-proj")
        assert points > 0

    def test_estimate_with_high_rework_category(self, metrics_collector):
        metrics_collector.record_project_start("proj")
        # Record high rework for security category
        for _ in range(10):
            metrics_collector.record_rework("proj", "security", True)
        for _ in range(2):
            metrics_collector.record_rework("proj", "security", False)

        estimator = EffortEstimator(metrics_collector)
        task = {"task_id": "FR-001", "category": "security", "steps": ["s1", "s2"]}
        points = estimator.estimate_effort_points(task, "python-fastapi", project_name="proj")
        assert points > 0

    def test_estimate_batch(self, estimator):
        tasks = [
            {"task_id": "FR-001", "steps": ["s1"]},
            {"task_id": "FR-002", "steps": ["s1", "s2", "s3"]},
        ]
        results = estimator.estimate_batch(tasks, "python-fastapi")
        assert len(results) == 2
        assert all(v > 0 for v in results.values())

    def test_get_complexity_breakdown(self, estimator):
        task = {
            "task_id": "FR-001",
            "steps": ["s1", "s2"],
            "artifacts": ["a1"],
            "gherkin_scenarios": [{"scenario": "sc1"}],
        }
        breakdown = estimator.get_complexity_breakdown(task, "python-fastapi")
        assert "complexity_metrics" in breakdown
        assert "steps" in breakdown["complexity_metrics"]

    def test_stack_complexity_multipliers(self, estimator):
        task = {"task_id": "FR-001", "steps": ["s1"]}
        python_pts = estimator.estimate_effort_points(task, "python-fastapi")
        go_pts = estimator.estimate_effort_points(task, "go-gin")
        assert python_pts > 0
        assert go_pts > 0

    def test_max_points_cap(self, estimator):
        huge_task = {
            "task_id": "FR-001",
            "steps": [f"s{i}" for i in range(100)],
            "artifacts": [f"a{i}" for i in range(100)],
            "gherkin_scenarios": [{"scenario": f"sc{i}"} for i in range(100)],
            "dependencies": [f"d{i}" for i in range(100)],
        }
        points = estimator.estimate_effort_points(huge_task, "python-fastapi")
        assert points <= 13  # Max cap

    def test_min_points_floor(self, estimator):
        tiny_task = {"task_id": "FR-001"}
        points = estimator.estimate_effort_points(tiny_task, "python-fastapi")
        assert points >= 1  # Min floor


class TestCategoryAdjustment:
    def test_high_rework(self):
        mock_metrics = MagicMock()
        mock_metrics.get_category_rework_rate.return_value = 0.35
        estimator = EffortEstimator(mock_metrics)
        assert estimator._get_category_confidence_adjustment("proj", "security") == 1.3

    def test_medium_rework(self):
        mock_metrics = MagicMock()
        mock_metrics.get_category_rework_rate.return_value = 0.25
        estimator = EffortEstimator(mock_metrics)
        assert estimator._get_category_confidence_adjustment("proj", "auth") == 1.2

    def test_low_rework(self):
        mock_metrics = MagicMock()
        mock_metrics.get_category_rework_rate.return_value = 0.15
        estimator = EffortEstimator(mock_metrics)
        assert estimator._get_category_confidence_adjustment("proj", "api") == 1.1

    def test_very_low_rework(self):
        mock_metrics = MagicMock()
        mock_metrics.get_category_rework_rate.return_value = 0.03
        estimator = EffortEstimator(mock_metrics)
        assert estimator._get_category_confidence_adjustment("proj", "ui") == 0.95

    def test_zero_rework(self):
        mock_metrics = MagicMock()
        mock_metrics.get_category_rework_rate.return_value = 0.0
        estimator = EffortEstimator(mock_metrics)
        assert estimator._get_category_confidence_adjustment("proj", "misc") == 1.0

    def test_exception_fallback(self):
        mock_metrics = MagicMock()
        mock_metrics.get_category_rework_rate.side_effect = Exception("fail")
        estimator = EffortEstimator(mock_metrics)
        assert estimator._get_category_confidence_adjustment("proj", "x") == 1.0


class TestHistoricalAdjustment:
    def test_high_rework(self):
        mock_metrics = MagicMock()
        mock_pm = MagicMock()
        mock_pm.rework_rate = 0.3
        mock_pm.task_completion_rate = 50
        mock_pm.prp_generation_time_minutes = 10
        mock_metrics.load_metrics.return_value = mock_pm
        estimator = EffortEstimator(mock_metrics)
        assert estimator._get_historical_adjustment("proj") == 1.2

    def test_high_completion(self):
        mock_metrics = MagicMock()
        mock_pm = MagicMock()
        mock_pm.rework_rate = 0.1
        mock_pm.task_completion_rate = 95
        mock_pm.prp_generation_time_minutes = 10
        mock_metrics.load_metrics.return_value = mock_pm
        estimator = EffortEstimator(mock_metrics)
        assert estimator._get_historical_adjustment("proj") == 0.9

    def test_high_gen_time(self):
        mock_metrics = MagicMock()
        mock_pm = MagicMock()
        mock_pm.rework_rate = 0.1
        mock_pm.task_completion_rate = 70
        mock_pm.prp_generation_time_minutes = 40
        mock_metrics.load_metrics.return_value = mock_pm
        estimator = EffortEstimator(mock_metrics)
        assert estimator._get_historical_adjustment("proj") == 1.1

    def test_normal(self):
        mock_metrics = MagicMock()
        mock_pm = MagicMock()
        mock_pm.rework_rate = 0.1
        mock_pm.task_completion_rate = 70
        mock_pm.prp_generation_time_minutes = 10
        mock_metrics.load_metrics.return_value = mock_pm
        estimator = EffortEstimator(mock_metrics)
        assert estimator._get_historical_adjustment("proj") == 1.0

    def test_exception_fallback(self):
        mock_metrics = MagicMock()
        mock_metrics.load_metrics.side_effect = Exception("fail")
        estimator = EffortEstimator(mock_metrics)
        assert estimator._get_historical_adjustment("proj") == 1.0
