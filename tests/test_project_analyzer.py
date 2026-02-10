"""Tests for core.project_analyzer module."""

import json
from pathlib import Path

import pytest

from core.project_analyzer import ProjectAnalyzer


@pytest.fixture()
def empty_project(tmp_path):
    """Create an empty project directory."""
    return tmp_path


@pytest.fixture()
def full_project(tmp_path):
    """Create a project with PRD, PRPs, and Tasks."""
    # PRD
    prd = tmp_path / "PRD.md"
    prd.write_text(
        "# PRD\n\n## Product Vision\nTask manager\n\n"
        "## Functional Requirements\n\n"
        "### FR-001 (MUST)\nUser registration\n\n"
        "### FR-002 (SHOULD)\nUser login\n",
        encoding="utf-8",
    )

    # PRPs
    prps = tmp_path / "PRPs"
    prps.mkdir()
    for phase in ["F0", "F1", "F2", "F3", "F4"]:
        (prps / f"{phase}_phase.md").write_text(
            f"# {phase}\n\n## Objectives\n- Objective for {phase}\n",
            encoding="utf-8",
        )

    # Tasks
    tasks = tmp_path / "TASKs"
    tasks.mkdir()
    for i in range(3):
        task_data = {
            "task_id": f"FR-{i+1:03d}",
            "objective": f"Task {i+1}",
            "steps": ["step1", "step2"],
        }
        (tasks / f"TASK.FR-{i+1:03d}.json").write_text(
            json.dumps(task_data, indent=2), encoding="utf-8"
        )

    # Config
    config = {"project_name": "test-project", "stack": "python-fastapi"}
    (tmp_path / ".ce-config.json").write_text(json.dumps(config), encoding="utf-8")

    return tmp_path


class TestProjectAnalyzer:
    def test_init(self, empty_project):
        analyzer = ProjectAnalyzer(empty_project)
        assert analyzer is not None

    def test_analyze_empty_project(self, empty_project):
        analyzer = ProjectAnalyzer(empty_project)
        state = analyzer.analyze_project_state()
        assert isinstance(state, dict)
        assert state.get("has_prd") is False
        assert state.get("has_prps") is False
        assert state.get("has_tasks") is False

    def test_analyze_full_project(self, full_project):
        analyzer = ProjectAnalyzer(full_project)
        state = analyzer.analyze_project_state()
        assert state["has_prd"] is True
        assert state["has_prps"] is True
        assert state["has_tasks"] is True
        assert state["task_count"] == 3

    def test_completion_status(self, full_project):
        analyzer = ProjectAnalyzer(full_project)
        state = analyzer.analyze_project_state()
        completion = state.get("completion_status", {})
        assert isinstance(completion, dict)

    def test_prp_phases(self, full_project):
        analyzer = ProjectAnalyzer(full_project)
        state = analyzer.analyze_project_state()
        phases = state.get("prp_phases", {})
        assert len(phases) >= 1

    def test_build_assistant_context_empty(self, empty_project):
        analyzer = ProjectAnalyzer(empty_project)
        ctx = analyzer.build_assistant_context()
        assert isinstance(ctx, dict)

    def test_build_assistant_context_full(self, full_project):
        analyzer = ProjectAnalyzer(full_project)
        ctx = analyzer.build_assistant_context()
        assert isinstance(ctx, dict)
        assert "requirements" in ctx or "tags" in ctx or "next_focus" in ctx

    def test_detect_stack_python(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.stack == "python-fastapi"

    def test_detect_stack_node(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name": "test"}', encoding="utf-8")
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.stack == "node-react"

    def test_detect_stack_go(self, tmp_path):
        (tmp_path / "go.mod").write_text("module test\n", encoding="utf-8")
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.stack == "go-gin"

    def test_detect_stack_unknown(self, empty_project):
        analyzer = ProjectAnalyzer(empty_project)
        assert analyzer.stack is None

    def test_detect_stack_from_config(self, tmp_path):
        config = {"stack": "vue3"}
        (tmp_path / ".ce-config.json").write_text(json.dumps(config), encoding="utf-8")
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.stack == "vue3"

    def test_get_suggestions_empty(self, empty_project):
        analyzer = ProjectAnalyzer(empty_project)
        state = analyzer.analyze_project_state()
        suggestions = state.get("suggestions", [])
        assert isinstance(suggestions, list)

    def test_get_suggestions_with_prd(self, tmp_path):
        (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
        (tmp_path / "PRD.md").write_text("# PRD\nContent", encoding="utf-8")
        analyzer = ProjectAnalyzer(tmp_path)
        state = analyzer.analyze_project_state()
        suggestions = state.get("suggestions", [])
        assert isinstance(suggestions, list)
        assert len(suggestions) >= 1

    def test_get_project_metrics(self, full_project):
        analyzer = ProjectAnalyzer(full_project)
        metrics = analyzer.get_project_metrics()
        assert isinstance(metrics, dict)
        assert "story_points" in metrics

    def test_detect_stack_vue3(self, tmp_path):
        (tmp_path / "vite.config.ts").write_text("export default {}", encoding="utf-8")
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.stack == "vue3"

    def test_completion_with_src(self, full_project):
        """Implementation detected when src/ has code files."""
        src = full_project / "src"
        src.mkdir()
        (src / "main.py").write_text("print('hello')", encoding="utf-8")
        (full_project / "README.md").write_text("# Project", encoding="utf-8")
        analyzer = ProjectAnalyzer(full_project)
        state = analyzer.analyze_project_state()
        assert state["completion_status"]["implementation"] is True

    def test_load_prd_summary(self, tmp_path):
        prd_dir = tmp_path / "prd"
        prd_dir.mkdir()
        prd_data = {
            "functional_requirements": [
                {"title": "User login", "description": "Authentication via email"},
                {"title": "Payment checkout", "description": "Process payments"},
            ]
        }
        (prd_dir / "prd_structured.json").write_text(json.dumps(prd_data), encoding="utf-8")
        analyzer = ProjectAnalyzer(tmp_path)
        summary = analyzer._load_prd_summary()
        assert len(summary["requirements"]) == 2
        assert "authentication" in summary["tags"]
        assert "payments" in summary["tags"]

    def test_load_prd_summary_missing(self, tmp_path):
        analyzer = ProjectAnalyzer(tmp_path)
        summary = analyzer._load_prd_summary()
        assert summary["requirements"] == []
        assert summary["tags"] == []

    def test_infer_tags(self, tmp_path):
        analyzer = ProjectAnalyzer(tmp_path)
        reqs = [
            {"title": "Dashboard analytics", "description": ""},
            {"title": "Email notification", "description": "Send alerts"},
        ]
        tags = analyzer._infer_tags_from_requirements(reqs)
        assert "analytics" in tags
        assert "notifications" in tags
        assert "communications" in tags

    def test_suggestions_with_prps_no_tasks(self, tmp_path):
        """Has PRD and PRPs but no tasks — should suggest generate-tasks."""
        (tmp_path / "README.md").write_text("# P", encoding="utf-8")
        (tmp_path / "PRD.md").write_text("# PRD\nContent", encoding="utf-8")
        prps = tmp_path / "PRPs"
        prps.mkdir()
        for phase in ["F0", "F1", "F2", "F3", "F4"]:
            (prps / f"{phase}_phase.md").write_text(
                f"# {phase}\n" + "x" * 200, encoding="utf-8"
            )
        analyzer = ProjectAnalyzer(tmp_path)
        state = analyzer.analyze_project_state()
        suggestions = state.get("suggestions", [])
        assert any("generate-tasks" in s for s in suggestions)

    def test_estimate_story_points_with_tasks(self, full_project):
        analyzer = ProjectAnalyzer(full_project)
        tasks_dir = full_project / "TASKs"
        points = analyzer._estimate_story_points(tasks_dir)
        assert isinstance(points, int)
        assert points >= 0
