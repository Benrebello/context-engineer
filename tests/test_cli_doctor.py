"""Tests for cli.commands.doctor module."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from cli.commands.doctor import doctor, DoctorReportBuilder


class TestDoctorReportBuilder:
    def test_init(self, tmp_path):
        with patch("cli.commands.doctor.CONFIG_SERVICE") as mock_cfg:
            mock_cfg.load_project_config.return_value = (tmp_path, {"use_transformers": False})
            builder = DoctorReportBuilder(tmp_path)
        assert builder.project_root == tmp_path
        assert builder.config == {"use_transformers": False}

    def test_init_no_config(self, tmp_path):
        with patch("cli.commands.doctor.CONFIG_SERVICE") as mock_cfg:
            mock_cfg.load_project_config.return_value = (None, {})
            builder = DoctorReportBuilder(tmp_path)
        assert builder.project_root is None
        assert builder.config == {}

    def test_add_config_section(self, tmp_path):
        with patch("cli.commands.doctor.CONFIG_SERVICE") as mock_cfg:
            mock_cfg.load_project_config.return_value = (tmp_path, {
                "use_transformers": True,
                "embedding_model": "all-MiniLM-L6-v2",
                "ai_profile": "balanced",
            })
            builder = DoctorReportBuilder(tmp_path)
            builder.add_config_section()
        assert builder.summary["config"]["use_transformers"] is True
        assert builder.summary["config"]["embedding_model"] == "all-MiniLM-L6-v2"

    def test_add_ai_governance_section(self, tmp_path):
        with patch("cli.commands.doctor.CONFIG_SERVICE") as mock_cfg, \
             patch("cli.commands.doctor.AI_GOVERNANCE_SERVICE") as mock_gov:
            mock_cfg.load_project_config.return_value = (tmp_path, {})
            mock_gov.resolve_preferences.return_value = (False, "all-MiniLM-L6-v2", tmp_path, {})
            mock_gov.dependencies_ready.return_value = False
            mock_gov.requires_installation.return_value = True
            builder = DoctorReportBuilder(tmp_path)
            builder.add_ai_governance_section(None, None)
        assert builder.summary["ai_governance"] is not None
        assert "resolved" in builder.summary["ai_governance"]

    def test_add_roi_section_no_data(self, tmp_path):
        with patch("cli.commands.doctor.CONFIG_SERVICE") as mock_cfg, \
             patch("cli.commands.doctor.get_roi_snapshot", return_value=None):
            mock_cfg.load_project_config.return_value = (None, {})
            builder = DoctorReportBuilder(tmp_path)
            builder.add_roi_section()
        assert builder.summary["roi"] is None

    def test_add_git_hooks_section(self, tmp_path):
        with patch("cli.commands.doctor.CONFIG_SERVICE") as mock_cfg, \
             patch("cli.commands.doctor.detect_git_hook_status") as mock_hooks:
            mock_cfg.load_project_config.return_value = (tmp_path, {})
            mock_hooks.return_value = {
                "pre_push": {"installed": True, "mode": "soft"},
                "pre_commit": {"installed": False, "mode": None},
            }
            builder = DoctorReportBuilder(tmp_path)
            builder.add_git_hooks_section()
        assert builder.summary["git_hooks"]["pre_push"]["installed"] is True

    def test_build(self, tmp_path):
        with patch("cli.commands.doctor.CONFIG_SERVICE") as mock_cfg:
            mock_cfg.load_project_config.return_value = (None, {})
            builder = DoctorReportBuilder(tmp_path)
            result = builder.build()
        assert "config" in result
        assert "ai_governance" in result


class TestDoctorCommand:
    def test_doctor_table(self, tmp_path):
        runner = CliRunner()
        with patch("cli.commands.doctor.CONFIG_SERVICE") as mock_cfg, \
             patch("cli.commands.doctor.AI_GOVERNANCE_SERVICE") as mock_gov, \
             patch("cli.commands.doctor.get_roi_snapshot", return_value=None), \
             patch("cli.commands.doctor.detect_git_hook_status", return_value={
                 "pre_push": {"installed": False, "mode": None},
                 "pre_commit": {"installed": False, "mode": None},
             }):
            mock_cfg.load_project_config.return_value = (tmp_path, {})
            mock_gov.resolve_preferences.return_value = (False, None, tmp_path, {})
            mock_gov.dependencies_ready.return_value = False
            mock_gov.requires_installation.return_value = False
            result = runner.invoke(doctor, ["--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "Doctor Report" in result.output

    def test_doctor_json(self, tmp_path):
        runner = CliRunner()
        with patch("cli.commands.doctor.CONFIG_SERVICE") as mock_cfg, \
             patch("cli.commands.doctor.AI_GOVERNANCE_SERVICE") as mock_gov, \
             patch("cli.commands.doctor.get_roi_snapshot", return_value=None), \
             patch("cli.commands.doctor.detect_git_hook_status", return_value={
                 "pre_push": {"installed": False, "mode": None},
                 "pre_commit": {"installed": False, "mode": None},
             }):
            mock_cfg.load_project_config.return_value = (tmp_path, {})
            mock_gov.resolve_preferences.return_value = (False, None, tmp_path, {})
            mock_gov.dependencies_ready.return_value = False
            mock_gov.requires_installation.return_value = False
            result = runner.invoke(doctor, ["--project-dir", str(tmp_path), "--format", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "config" in parsed

    def test_doctor_with_ai_profile_preview(self, tmp_path):
        runner = CliRunner()
        with patch("cli.commands.doctor.CONFIG_SERVICE") as mock_cfg, \
             patch("cli.commands.doctor.AI_GOVERNANCE_SERVICE") as mock_gov, \
             patch("cli.commands.doctor.get_roi_snapshot", return_value=None), \
             patch("cli.commands.doctor.detect_git_hook_status", return_value={
                 "pre_push": {"installed": False, "mode": None},
                 "pre_commit": {"installed": False, "mode": None},
             }):
            mock_cfg.load_project_config.return_value = (tmp_path, {})
            mock_gov.resolve_preferences.return_value = (False, None, tmp_path, {})
            mock_gov.dependencies_ready.return_value = False
            mock_gov.requires_installation.return_value = False
            result = runner.invoke(doctor, [
                "--project-dir", str(tmp_path),
                "--ai-profile", "local",
            ])
        assert result.exit_code == 0
        assert "Preview" in result.output or "local" in result.output

    def test_doctor_with_roi(self, tmp_path):
        runner = CliRunner()
        roi_data = {
            "tokens_saved": 500,
            "tokens_used": 1000,
            "savings_percentage": 33.3,
            "estimated_cost_saved_usd": 0.05,
            "context_pruning_events": 3,
        }
        with patch("cli.commands.doctor.CONFIG_SERVICE") as mock_cfg, \
             patch("cli.commands.doctor.AI_GOVERNANCE_SERVICE") as mock_gov, \
             patch("cli.commands.doctor.get_roi_snapshot", return_value=roi_data), \
             patch("cli.commands.doctor.detect_git_hook_status", return_value={
                 "pre_push": {"installed": False, "mode": None},
                 "pre_commit": {"installed": False, "mode": None},
             }):
            mock_cfg.load_project_config.return_value = (tmp_path, {})
            mock_gov.resolve_preferences.return_value = (False, None, tmp_path, {})
            mock_gov.dependencies_ready.return_value = False
            mock_gov.requires_installation.return_value = False
            result = runner.invoke(doctor, ["--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "500" in result.output
