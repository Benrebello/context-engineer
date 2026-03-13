"""Tests for core.exceptions module."""

from core.exceptions import (
    AIModelNotAvailableError,
    ConfigurationError,
    ContextEngineerError,
    DependencyMissingError,
    GitNotInitializedError,
    InsufficientPermissionsError,
    PRDNotFoundError,
    PRPsNotFoundError,
    StackNotSupportedError,
    TasksNotFoundError,
    TraceabilityGapError,
    ValidationFailedError,
)


def test_base_error_format():
    err = ContextEngineerError("something broke", tip="try this", docs_url="https://example.com")
    formatted = err.format_error()
    assert "something broke" in formatted
    assert "try this" in formatted
    assert "https://example.com" in formatted


def test_base_error_no_tip():
    err = ContextEngineerError("oops")
    formatted = err.format_error()
    assert "oops" in formatted
    assert "Tip" not in formatted
    assert "Learn more" not in formatted


def test_prd_not_found():
    err = PRDNotFoundError(searched_paths=["/a", "/b"])
    assert "/a" in err.message
    assert "ce generate-prd" in err.tip


def test_prd_not_found_no_paths():
    err = PRDNotFoundError()
    assert "not found" in err.message


def test_prps_not_found():
    err = PRPsNotFoundError(searched_paths=["/prps"])
    assert "/prps" in err.message
    assert "ce generate-prps" in err.tip


def test_tasks_not_found():
    err = TasksNotFoundError(searched_paths=["/tasks"])
    assert "/tasks" in err.message


def test_dependency_missing_default():
    err = DependencyMissingError("numpy")
    assert "numpy" in err.message
    assert "pip install numpy" in err.tip


def test_dependency_missing_custom_cmd():
    err = DependencyMissingError("torch", install_command="conda install torch")
    assert "conda install torch" in err.tip


def test_git_not_initialized():
    err = GitNotInitializedError("/my/project")
    assert "/my/project" in err.message
    assert "git init" in err.tip


def test_validation_failed():
    errors = ["err1", "err2", "err3"]
    err = ValidationFailedError("PRP", errors)
    assert "PRP" in err.message
    assert "err1" in err.message


def test_validation_failed_many_errors():
    errors = [f"err{i}" for i in range(10)]
    err = ValidationFailedError("Task", errors)
    assert "5 more" in err.message


def test_stack_not_supported():
    err = StackNotSupportedError("ruby", ["python-fastapi", "node-react"])
    assert "ruby" in err.message
    assert "python-fastapi" in err.tip


def test_configuration_error():
    err = ConfigurationError(".ce-config.json", "invalid JSON")
    assert ".ce-config.json" in err.message
    assert "invalid JSON" in err.message


def test_ai_model_not_available():
    err = AIModelNotAvailableError("gpt-5")
    assert "gpt-5" in err.message
    assert "--no-ai" in err.tip


def test_insufficient_permissions():
    err = InsufficientPermissionsError("/etc/secret", "write")
    assert "/etc/secret" in err.message
    assert "write" in err.message


def test_traceability_gap():
    err = TraceabilityGapError(["FR-001", "FR-002"])
    assert "FR-001" in err.message


def test_traceability_gap_many():
    items = [f"FR-{i:03d}" for i in range(10)]
    err = TraceabilityGapError(items)
    assert "5 more" in err.message
