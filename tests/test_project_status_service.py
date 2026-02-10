"""Tests for core.project_status_service module."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.project_status_service import ProjectStatusService


@pytest.fixture()
def prompt_service():
    return MagicMock()


@pytest.fixture()
def service(prompt_service):
    return ProjectStatusService(prompt_service)


@pytest.fixture()
def full_project(tmp_path):
    """Create a project with PRD, PRPs, and Tasks."""
    (tmp_path / "README.md").write_text("# Project", encoding="utf-8")
    (tmp_path / "PRD.md").write_text("# PRD\n## Requirements\n- FR-001", encoding="utf-8")
    prps = tmp_path / "PRPs"
    prps.mkdir()
    for phase in ["F0", "F1", "F2", "F3", "F4"]:
        (prps / f"{phase}_phase.md").write_text(
            f"# {phase}\n\n## Objectives\n- Objective\n" + "x" * 200,
            encoding="utf-8",
        )
    tasks = tmp_path / "TASKs"
    tasks.mkdir()
    (tasks / "TASK.FR-001.json").write_text(
        json.dumps({"task_id": "FR-001", "objective": "Test"}), encoding="utf-8"
    )
    return tmp_path


class TestBuildStatusView:
    def test_basic(self):
        state = {
            "completion_status": {"init": True, "prd": True, "prps": False, "tasks": False, "implementation": False},
            "prp_phases": {"F0": {"exists": True}, "F1": {"exists": False}},
            "has_prd": True,
            "prd_path": "/tmp/PRD.md",
            "has_prps": True,
            "has_tasks": False,
            "task_count": 0,
            "suggestions": ["Run ce generate-prps"],
        }
        view = ProjectStatusService._build_status_view(state, "test-project")
        assert view["project_name"] == "test-project"
        assert view["has_prd"] is True
        assert view["prp_completed"] == 1
        assert view["prp_total"] == 2
        assert view["prd_filename"] == "PRD.md"
        assert view["completed_steps"] == 2

    def test_no_prd_path(self):
        state = {
            "completion_status": {},
            "prp_phases": {},
            "has_prd": False,
            "prd_path": None,
            "has_prps": False,
            "has_tasks": False,
            "task_count": 0,
            "suggestions": [],
        }
        view = ProjectStatusService._build_status_view(state, "proj")
        assert view["prd_filename"] is None


class TestResolveEngine:
    def test_returns_provided_engine(self, service):
        engine = MagicMock()
        assert service._resolve_engine(engine, None, None) is engine

    def test_returns_none_when_no_args(self, service):
        assert service._resolve_engine(None, None, None) is None

    def test_creates_engine_with_ai(self, service):
        result = service._resolve_engine(None, False, None)
        assert result is not None


class TestGatherStatusData:
    def test_gather_empty_project(self, service, tmp_path):
        data = service.gather_status_data(tmp_path, include_suggestions=False)
        assert "state" in data
        assert "status_view" in data
        assert "assistant_context" in data
        assert "metrics" in data

    def test_gather_full_project(self, service, full_project):
        data = service.gather_status_data(full_project, include_suggestions=False)
        assert data["status_view"]["has_prd"] is True
        assert data["status_view"]["has_prps"] is True
        assert data["status_view"]["has_tasks"] is True

    def test_gather_with_suggestions_no_engine(self, service, full_project):
        data = service.gather_status_data(full_project, include_suggestions=True)
        assert "pattern_suggestions" in data
        assert "cache_suggestions" in data


class TestFormatStatusText:
    def test_format_status(self, service, full_project):
        data = service.gather_status_data(full_project, include_suggestions=False)
        try:
            text = service.format_status_text(data)
            assert isinstance(text, str)
        except FileNotFoundError:
            pytest.skip("Template not found")


class TestFormatChecklistText:
    def test_format_checklist(self, service, full_project):
        data = service.gather_status_data(full_project, include_suggestions=False)
        try:
            text = service.format_checklist_text(data["status_view"])
            assert isinstance(text, str)
        except FileNotFoundError:
            pytest.skip("Template not found")


class TestRenderAssistIntro:
    def test_render_text(self, service, full_project):
        data = service.gather_status_data(full_project, include_suggestions=False)
        try:
            text = service.render_assist_intro(data, output_format="text")
            assert isinstance(text, str)
        except FileNotFoundError:
            pytest.skip("Template not found")


class TestBuildSuggestions:
    def test_build_suggestions_with_engine(self, service):
        mock_engine = MagicMock()
        mock_engine.pattern_library.suggest_patterns.return_value = [{"name": "auth"}]
        mock_engine.cache.search_similar.return_value = []
        result = service._build_suggestions(
            mock_engine,
            {"requirements": [], "tags": [], "next_focus": None, "project_name": "test"},
            {"stack": ["python-fastapi"]},
        )
        assert "patterns" in result
        assert len(result["patterns"]) == 1

    def test_build_suggestions_empty_context(self, service):
        mock_engine = MagicMock()
        mock_engine.pattern_library.suggest_patterns.return_value = []
        mock_engine.cache.search_similar.return_value = []
        result = service._build_suggestions(mock_engine, {}, {})
        assert result["patterns"] == []
        assert result["cache"] == []


class TestRenderAssistIntroHtml:
    def test_render_html(self, service, full_project):
        data = service.gather_status_data(full_project, include_suggestions=False)
        try:
            html = service.render_assist_intro(data, output_format="html")
            assert isinstance(html, str)
        except FileNotFoundError:
            pytest.skip("HTML template not found")


class TestGatherWithEngine:
    def test_gather_with_engine(self, service, full_project):
        mock_engine = MagicMock()
        mock_engine.pattern_library.suggest_patterns.return_value = []
        mock_engine.cache.search_similar.return_value = []
        data = service.gather_status_data(
            full_project, engine=mock_engine, include_suggestions=True
        )
        assert "pattern_suggestions" in data


class TestRunAssistantFlow:
    def test_run_flow(self, service, full_project):
        data = service.run_assistant_flow(full_project)
        assert "state" in data
        assert "status_view" in data
        assert "assistant_context" in data

    def test_run_flow_with_engine(self, service, full_project):
        mock_engine = MagicMock()
        mock_engine.pattern_library.suggest_patterns.return_value = []
        mock_engine.cache.search_similar.return_value = []
        data = service.run_assistant_flow(full_project, engine=mock_engine)
        assert "pattern_suggestions" in data
