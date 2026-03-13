"""Tests for cli.commands.reporting module."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from cli.commands.reporting import report, metrics_summary, ai_status


class TestReport:
    def test_report_global_no_metrics(self):
        runner = CliRunner()
        mock_reporting = MagicMock()
        mock_reporting.load_global_metrics.return_value = ([], {})
        with patch("cli.commands.reporting.MetricsCollector"), \
             patch("cli.commands.reporting.ReportingService", return_value=mock_reporting):
            result = runner.invoke(report, ["--format", "table"])
        assert result.exit_code == 0
        assert "No metrics found" in result.output

    def test_report_global_json(self):
        runner = CliRunner()
        mock_metrics_obj = MagicMock()
        mock_metrics_obj.project_name = "proj1"
        mock_metrics_obj.rework_rate = 5.0
        mock_metrics_obj.task_completion_rate = 80.0
        mock_reporting = MagicMock()
        mock_reporting.load_global_metrics.return_value = ([mock_metrics_obj], {"avg_rework": 5.0})
        with patch("cli.commands.reporting.MetricsCollector"), \
             patch("cli.commands.reporting.ReportingService", return_value=mock_reporting):
            result = runner.invoke(report, ["--format", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["total_projects"] == 1

    def test_report_project_json(self):
        runner = CliRunner()
        mock_metrics = MagicMock()
        mock_metrics.prp_generation_time_minutes = 5.0
        mock_metrics.task_completion_rate = 80.0
        mock_metrics.test_coverage_achieved = 90.0
        mock_metrics.code_quality_score = 8.5
        mock_metrics.rework_rate = 10.0
        mock_metrics.total_tasks = 10
        mock_metrics.completed_tasks = 8
        mock_reporting = MagicMock()
        mock_reporting.load_project_metrics.return_value = (mock_metrics, {"status": "good"}, {"tokens_saved": 100})
        with patch("cli.commands.reporting.MetricsCollector"), \
             patch("cli.commands.reporting.ReportingService", return_value=mock_reporting):
            result = runner.invoke(report, ["--project-name", "test", "--format", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["project"] == "test"


class TestMetricsSummary:
    def test_metrics_summary(self):
        runner = CliRunner()
        mock_collector = MagicMock()
        mock_metrics = MagicMock()
        mock_metrics.prp_generation_time_minutes = 5.0
        mock_metrics.task_completion_rate = 80.0
        mock_metrics.test_coverage_achieved = 75.0
        mock_metrics.code_quality_score = 8.0
        mock_metrics.rework_rate = 10.0
        mock_metrics.total_tasks = 10
        mock_metrics.completed_tasks = 8
        mock_collector.load_metrics.return_value = mock_metrics
        mock_collector.get_roi_metrics.return_value = {"tokens_saved": 0, "tokens_used": 0, "savings_percentage": 0, "estimated_cost_saved_usd": 0, "context_pruning_events": 0}
        with patch("cli.commands.reporting.MetricsCollector", return_value=mock_collector):
            result = runner.invoke(metrics_summary, ["--project-name", "test"])
        assert result.exit_code == 0


class TestMetricsSummaryWithTasks:
    def test_metrics_summary_with_tasks_dir(self, tmp_path):
        runner = CliRunner()
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        task = {"task_id": "FR-001", "steps": ["s1"], "artifacts": [], "gherkin_scenarios": [], "dependencies": []}
        (tasks / "TASK.FR-001.json").write_text(json.dumps(task), encoding="utf-8")
        mock_collector = MagicMock()
        mock_metrics = MagicMock()
        mock_metrics.rework_rate = 5.0
        mock_metrics.task_completion_rate = 80.0
        mock_metrics.completed_tasks = 8
        mock_metrics.total_tasks = 10
        mock_collector.load_metrics.return_value = mock_metrics
        with patch("cli.commands.reporting.MetricsCollector", return_value=mock_collector):
            result = runner.invoke(metrics_summary, [
                "--project-name", "test",
                "--tasks-dir", str(tasks),
            ])
        assert result.exit_code == 0
        assert "METRICS SUMMARY" in result.output

    def test_metrics_summary_high_rework(self):
        runner = CliRunner()
        mock_collector = MagicMock()
        mock_metrics = MagicMock()
        mock_metrics.rework_rate = 35.0
        mock_metrics.task_completion_rate = 50.0
        mock_metrics.completed_tasks = 5
        mock_metrics.total_tasks = 10
        mock_collector.load_metrics.return_value = mock_metrics
        with patch("cli.commands.reporting.MetricsCollector", return_value=mock_collector):
            result = runner.invoke(metrics_summary, ["--project-name", "test"])
        assert result.exit_code == 0
        assert "HIGH RISK" in result.output

    def test_metrics_summary_medium_rework(self):
        runner = CliRunner()
        mock_collector = MagicMock()
        mock_metrics = MagicMock()
        mock_metrics.rework_rate = 20.0
        mock_metrics.task_completion_rate = 70.0
        mock_metrics.completed_tasks = 7
        mock_metrics.total_tasks = 10
        mock_collector.load_metrics.return_value = mock_metrics
        with patch("cli.commands.reporting.MetricsCollector", return_value=mock_collector):
            result = runner.invoke(metrics_summary, ["--project-name", "test"])
        assert result.exit_code == 0
        assert "MODERATE RISK" in result.output


class TestReportHtml:
    def test_report_project_html(self, tmp_path):
        runner = CliRunner()
        mock_metrics = MagicMock()
        mock_reporting = MagicMock()
        mock_reporting.load_project_metrics.return_value = (mock_metrics, {}, {})
        mock_reporting.render_project_dashboard_html.return_value = "<html>Dashboard</html>"
        with patch("cli.commands.reporting.MetricsCollector"), \
             patch("cli.commands.reporting.ReportingService", return_value=mock_reporting):
            result = runner.invoke(report, [
                "--project-name", "test",
                "--format", "html",
                "--output", str(tmp_path / "dash.html"),
            ])
        assert result.exit_code == 0
        assert "Dashboard saved" in result.output

    def test_report_global_html(self, tmp_path):
        runner = CliRunner()
        mock_metrics_obj = MagicMock()
        mock_reporting = MagicMock()
        mock_reporting.load_global_metrics.return_value = ([mock_metrics_obj], {})
        mock_reporting.render_global_dashboard_html.return_value = "<html>Global</html>"
        with patch("cli.commands.reporting.MetricsCollector"), \
             patch("cli.commands.reporting.ReportingService", return_value=mock_reporting):
            result = runner.invoke(report, [
                "--format", "html",
                "--output", str(tmp_path / "global.html"),
            ])
        assert result.exit_code == 0
        assert "Global dashboard saved" in result.output


class TestAiStatus:
    def test_ai_status(self, tmp_path):
        runner = CliRunner()
        with patch("cli.commands.reporting.STATUS_SERVICE") as mock_svc, \
             patch("cli.commands.reporting.create_engine") as mock_engine:
            mock_svc.config_service.load_project_config.return_value = (tmp_path, {"use_transformers": False})
            mock_cache = MagicMock()
            mock_cache.use_transformers = False
            mock_cache.selected_model = "all-MiniLM-L6-v2"
            mock_engine.return_value.cache = mock_cache
            result = runner.invoke(ai_status, ["--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "AI Mode Diagnostic" in result.output
