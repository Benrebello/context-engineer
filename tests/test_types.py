"""Tests for core.types module — ensures TypedDicts are importable and usable."""

from core.types import (
    AIGovernanceStatus,
    ConfigDict,
    MetricsDict,
    PRDGenerationResult,
    PRPGenerationResult,
    ProjectInitResult,
    TaskGenerationResult,
    ValidationResult,
)


def test_project_init_result():
    r: ProjectInitResult = {
        "success": True,
        "created_directories": ["src"],
        "created_files": ["README.md"],
        "generated_files": [],
        "stack_structure_created": True,
    }
    assert r["success"] is True


def test_prd_generation_result():
    r: PRDGenerationResult = {
        "success": True,
        "prd_file": "PRD.md",
        "prd_structured": "prd_structured.json",
    }
    assert r["prd_file"] == "PRD.md"


def test_prp_generation_result():
    r: PRPGenerationResult = {
        "success": True,
        "phases": ["F0", "F1"],
        "prd_used": "prd.json",
    }
    assert len(r["phases"]) == 2


def test_task_generation_result():
    r: TaskGenerationResult = {
        "success": True,
        "tasks": ["t1"],
        "tasks_dir": "/tmp/tasks",
    }
    assert r["tasks_dir"] == "/tmp/tasks"


def test_validation_result():
    r: ValidationResult = {
        "valid": True,
        "errors": [],
        "warnings": ["w1"],
        "error_count": 0,
        "warning_count": 1,
    }
    assert r["valid"] is True


def test_metrics_dict():
    r: MetricsDict = {
        "story_points": 5,
        "rework_rate": 0.1,
        "test_coverage": 85.0,
        "task_completion_rate": 90.0,
    }
    assert r["story_points"] == 5


def test_config_dict():
    r: ConfigDict = {
        "project_name": "test",
        "stack": "python-fastapi",
        "language": "en-us",
    }
    assert r["stack"] == "python-fastapi"


def test_ai_governance_status():
    r: AIGovernanceStatus = {
        "governance_enabled": True,
        "soft_gate_mode": True,
        "hooks_installed": False,
        "auto_install_policy": "prompt",
    }
    assert r["governance_enabled"] is True
