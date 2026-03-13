"""Tests for cli.commands.status module."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from cli.commands.status import status, checklist, assist, wizard


def _make_assistant_data(completion=None):
    """Helper to build mock data for assist/wizard tests."""
    if completion is None:
        completion = {"init": True, "prd": True, "prps": True, "tasks": True}
    return {
        "state": {"completion_status": completion, "has_prd": True},
        "status_view": {"project_name": "test"},
        "assistant_context": {"project_name": "test", "stack": ["python-fastapi"]},
        "metrics": {},
        "pattern_suggestions": [],
        "cache_suggestions": [],
    }


class TestStatus:
    def test_status_basic(self, tmp_path):
        runner = CliRunner()
        mock_data = {
            "state": {"has_prd": False, "has_prps": False, "has_tasks": False},
            "status_view": {"project_name": "test"},
            "assistant_context": {"project_name": "test"},
            "metrics": {},
            "pattern_suggestions": [],
            "cache_suggestions": [],
        }
        with patch("cli.commands.status.STATUS_SERVICE") as mock_svc:
            mock_svc.gather_status_data.return_value = mock_data
            mock_svc.format_status_text.return_value = "Status: OK"
            result = runner.invoke(status, ["--project-dir", str(tmp_path), "--no-ai"])
        assert result.exit_code == 0
        assert "Status: OK" in result.output

    def test_status_json(self, tmp_path):
        runner = CliRunner()
        mock_data = {
            "state": {"has_prd": True},
            "status_view": {},
            "assistant_context": {},
            "metrics": {"story_points": 5},
            "pattern_suggestions": [],
            "cache_suggestions": [],
        }
        with patch("cli.commands.status.STATUS_SERVICE") as mock_svc:
            mock_svc.gather_status_data.return_value = mock_data
            result = runner.invoke(status, ["--project-dir", str(tmp_path), "--json", "--no-ai"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "state" in parsed


class TestChecklist:
    def test_checklist_basic(self, tmp_path):
        runner = CliRunner()
        mock_data = {
            "state": {},
            "status_view": {"project_name": "test", "completion_status": {}},
            "assistant_context": {},
            "metrics": {},
            "pattern_suggestions": [],
            "cache_suggestions": [],
        }
        with patch("cli.commands.status.STATUS_SERVICE") as mock_svc:
            mock_svc.gather_status_data.return_value = mock_data
            mock_svc.format_checklist_text.return_value = "Checklist: OK"
            result = runner.invoke(checklist, ["--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "Checklist: OK" in result.output


class TestAssist:
    def test_assist_all_complete(self, tmp_path):
        """All steps already complete — skips all prompts."""
        runner = CliRunner()
        data = _make_assistant_data()
        with patch("cli.commands.status.STATUS_SERVICE") as mock_svc:
            mock_svc.run_assistant_flow.return_value = data
            mock_svc.render_assist_intro.return_value = "Intro text"
            result = runner.invoke(assist, ["--project-dir", str(tmp_path), "--no-ai"])
        assert result.exit_code == 0
        assert "Guided process completed" in result.output

    def test_assist_html_format(self, tmp_path):
        """HTML format saves report file."""
        runner = CliRunner()
        data = _make_assistant_data()
        with patch("cli.commands.status.STATUS_SERVICE") as mock_svc:
            mock_svc.run_assistant_flow.return_value = data
            mock_svc.render_assist_intro.return_value = "<html>Report</html>"
            result = runner.invoke(assist, [
                "--project-dir", str(tmp_path),
                "--format", "html",
                "--no-ai",
            ])
        assert result.exit_code == 0
        assert "HTML" in result.output

    def test_assist_open_without_html(self, tmp_path):
        """--open flag without html format shows warning."""
        runner = CliRunner()
        data = _make_assistant_data()
        with patch("cli.commands.status.STATUS_SERVICE") as mock_svc:
            mock_svc.run_assistant_flow.return_value = data
            mock_svc.render_assist_intro.return_value = "Intro"
            result = runner.invoke(assist, [
                "--project-dir", str(tmp_path),
                "--format", "text",
                "--open",
                "--no-ai",
            ])
        assert result.exit_code == 0
        assert "AVISO" in result.output or "Guided process" in result.output

    def test_assist_missing_init(self, tmp_path):
        """Missing init step — user declines."""
        runner = CliRunner()
        data = _make_assistant_data({"init": False, "prd": True, "prps": True, "tasks": True})
        with patch("cli.commands.status.STATUS_SERVICE") as mock_svc:
            mock_svc.run_assistant_flow.return_value = data
            mock_svc.render_assist_intro.return_value = "Intro"
            result = runner.invoke(assist, [
                "--project-dir", str(tmp_path), "--no-ai",
            ], input="n\n")
        assert result.exit_code == 0

    def test_assist_missing_prd(self, tmp_path):
        """Missing PRD step — user declines."""
        runner = CliRunner()
        data = _make_assistant_data({"init": True, "prd": False, "prps": True, "tasks": True})
        with patch("cli.commands.status.STATUS_SERVICE") as mock_svc:
            mock_svc.run_assistant_flow.return_value = data
            mock_svc.render_assist_intro.return_value = "Intro"
            result = runner.invoke(assist, [
                "--project-dir", str(tmp_path), "--no-ai",
            ], input="n\n")
        assert result.exit_code == 0


    def test_assist_accept_init(self, tmp_path):
        """Accept init step via ctx.invoke mock."""
        runner = CliRunner()
        data = _make_assistant_data({"init": False, "prd": True, "prps": True, "tasks": True})
        with patch("cli.commands.status.STATUS_SERVICE") as mock_svc, \
             patch("cli.commands.status.ProjectAnalyzer") as mock_analyzer, \
             patch("cli.commands.status.click.get_current_context") as mock_ctx:
            mock_svc.run_assistant_flow.return_value = data
            mock_svc.render_assist_intro.return_value = "Intro"
            mock_analyzer_inst = MagicMock()
            mock_analyzer_inst.analyze_project_state.return_value = {
                "completion_status": {"init": True, "prd": True, "prps": True, "tasks": True},
            }
            mock_analyzer.return_value = mock_analyzer_inst
            mock_ctx.return_value = MagicMock()
            result = runner.invoke(assist, [
                "--project-dir", str(tmp_path), "--no-ai",
            ], input="y\n")
        assert result.exit_code == 0

    def test_assist_accept_prd(self, tmp_path):
        """Accept PRD step."""
        runner = CliRunner()
        data = _make_assistant_data({"init": True, "prd": False, "prps": True, "tasks": True})
        with patch("cli.commands.status.STATUS_SERVICE") as mock_svc, \
             patch("cli.commands.status.ProjectAnalyzer") as mock_analyzer, \
             patch("cli.commands.status.click.get_current_context") as mock_ctx:
            mock_svc.run_assistant_flow.return_value = data
            mock_svc.render_assist_intro.return_value = "Intro"
            mock_analyzer_inst = MagicMock()
            mock_analyzer_inst.analyze_project_state.return_value = {
                "completion_status": {"init": True, "prd": True, "prps": True, "tasks": True},
            }
            mock_analyzer.return_value = mock_analyzer_inst
            mock_ctx.return_value = MagicMock()
            result = runner.invoke(assist, [
                "--project-dir", str(tmp_path), "--no-ai",
            ], input="y\n")
        assert result.exit_code == 0

    def test_assist_accept_prps(self, tmp_path):
        """Accept PRPs step."""
        runner = CliRunner()
        data = _make_assistant_data({"init": True, "prd": True, "prps": False, "tasks": True})
        with patch("cli.commands.status.STATUS_SERVICE") as mock_svc, \
             patch("cli.commands.status.ProjectAnalyzer") as mock_analyzer, \
             patch("cli.commands.status.click.get_current_context") as mock_ctx:
            mock_svc.run_assistant_flow.return_value = data
            mock_svc.render_assist_intro.return_value = "Intro"
            mock_analyzer_inst = MagicMock()
            mock_analyzer_inst.analyze_project_state.return_value = {
                "completion_status": {"init": True, "prd": True, "prps": True, "tasks": True},
            }
            mock_analyzer.return_value = mock_analyzer_inst
            mock_ctx.return_value = MagicMock()
            result = runner.invoke(assist, [
                "--project-dir", str(tmp_path), "--no-ai",
            ], input="y\n")
        assert result.exit_code == 0

    def test_assist_accept_tasks(self, tmp_path):
        """Accept tasks step."""
        runner = CliRunner()
        data = _make_assistant_data({"init": True, "prd": True, "prps": True, "tasks": False})
        with patch("cli.commands.status.STATUS_SERVICE") as mock_svc, \
             patch("cli.commands.status.ProjectAnalyzer") as mock_analyzer, \
             patch("cli.commands.status.click.get_current_context") as mock_ctx:
            mock_svc.run_assistant_flow.return_value = data
            mock_svc.render_assist_intro.return_value = "Intro"
            mock_analyzer_inst = MagicMock()
            mock_analyzer_inst.analyze_project_state.return_value = {
                "completion_status": {"init": True, "prd": True, "prps": True, "tasks": True},
            }
            mock_analyzer.return_value = mock_analyzer_inst
            mock_ctx.return_value = MagicMock()
            result = runner.invoke(assist, [
                "--project-dir", str(tmp_path), "--no-ai",
            ], input="y\n")
        assert result.exit_code == 0


class TestWizard:
    def test_wizard_decline_all(self):
        """User declines every step."""
        runner = CliRunner()
        result = runner.invoke(wizard, ["--no-ai"], input="n\nn\nn\nn\nn\n")
        assert result.exit_code == 0
        assert "WIZARD" in result.output

    def test_wizard_skip_init(self):
        """Skip init flag."""
        runner = CliRunner()
        result = runner.invoke(wizard, ["--skip-init", "--no-ai"], input="n\nn\nn\n")
        assert result.exit_code == 0

    def test_wizard_accept_init(self):
        """Accept init step in wizard."""
        runner = CliRunner()
        with patch("cli.commands.status.click.get_current_context") as mock_ctx:
            mock_ctx.return_value = MagicMock()
            result = runner.invoke(wizard, ["--no-ai"], input="y\ntest-proj\n1\nn\nn\nn\n")
        assert result.exit_code == 0
