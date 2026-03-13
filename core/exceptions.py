"""
Custom exceptions with contextual help and suggestions for Context Engineer.
"""

from __future__ import annotations


class ContextEngineerError(Exception):
    """Base exception for Context Engineer with contextual help."""

    def __init__(self, message: str, tip: str | None = None, docs_url: str | None = None):
        """
        Initialize error with helpful context.

        Args:
            message: Error message
            tip: Helpful tip for resolving the error
            docs_url: URL to relevant documentation
        """
        self.message = message
        self.tip = tip
        self.docs_url = docs_url
        super().__init__(message)

    def format_error(self) -> str:
        """Format error with tips and documentation links."""
        lines = [f"Error: {self.message}"]

        if self.tip:
            lines.append(f"\nTip: {self.tip}")

        if self.docs_url:
            lines.append(f"\nLearn more: {self.docs_url}")

        return "\n".join(lines)


class PRDNotFoundError(ContextEngineerError):
    """Raised when PRD file is not found."""

    def __init__(self, searched_paths: list[str] | None = None):
        paths_msg = ""
        if searched_paths:
            paths_msg = f"\n   Searched in: {', '.join(searched_paths)}"

        super().__init__(
            message=f"PRD file not found{paths_msg}",
            tip="Generate a PRD first with:\n   ce generate-prd --interactive",
            docs_url="https://github.com/context-engineer/docs/prd-guide",
        )


class PRPsNotFoundError(ContextEngineerError):
    """Raised when PRP files are not found."""

    def __init__(self, searched_paths: list[str] | None = None):
        paths_msg = ""
        if searched_paths:
            paths_msg = f"\n   Searched in: {', '.join(searched_paths)}"

        super().__init__(
            message=f"PRP files not found{paths_msg}",
            tip="Generate PRPs first with:\n   ce generate-prps",
            docs_url="https://github.com/context-engineer/docs/prp-guide",
        )


class TasksNotFoundError(ContextEngineerError):
    """Raised when task files are not found."""

    def __init__(self, searched_paths: list[str] | None = None):
        paths_msg = ""
        if searched_paths:
            paths_msg = f"\n   Searched in: {', '.join(searched_paths)}"

        super().__init__(
            message=f"Task files not found{paths_msg}",
            tip="Generate tasks first with:\n   ce generate-tasks",
            docs_url="https://github.com/context-engineer/docs/tasks-guide",
        )


class DependencyMissingError(ContextEngineerError):
    """Raised when required dependency is missing."""

    def __init__(self, dependency: str, install_command: str | None = None):
        install_msg = install_command or f"pip install {dependency}"
        super().__init__(
            message=f"Required dependency '{dependency}' is not installed",
            tip=f"Install it with:\n   {install_msg}",
            docs_url="https://github.com/context-engineer/docs/installation",
        )


class GitNotInitializedError(ContextEngineerError):
    """Raised when Git repository is not initialized."""

    def __init__(self, project_dir: str):
        super().__init__(
            message=f"Git repository not initialized in {project_dir}",
            tip="Initialize Git with:\n   git init\n   ce install-hooks",
            docs_url="https://github.com/context-engineer/docs/git-setup",
        )


class ValidationFailedError(ContextEngineerError):
    """Raised when validation fails."""

    def __init__(self, validation_type: str, errors: list[str]):
        error_list = "\n   • ".join(errors[:5])  # Show first 5 errors
        more_msg = f"\n   ... and {len(errors) - 5} more errors" if len(errors) > 5 else ""

        super().__init__(
            message=f"{validation_type} validation failed:\n   • {error_list}{more_msg}",
            tip="Fix the errors above and run validation again:\n   ce validate",
            docs_url="https://github.com/context-engineer/docs/validation",
        )


class StackNotSupportedError(ContextEngineerError):
    """Raised when stack is not supported."""

    def __init__(self, stack: str, available_stacks: list[str]):
        stacks_list = ", ".join(available_stacks)
        super().__init__(
            message=f"Stack '{stack}' is not supported",
            tip=f"Available stacks: {stacks_list}\n   Use one of them with:\n   ce init --stack <stack-name>",
            docs_url="https://github.com/context-engineer/docs/stacks",
        )


class ConfigurationError(ContextEngineerError):
    """Raised when configuration is invalid."""

    def __init__(self, config_file: str, issue: str):
        super().__init__(
            message=f"Configuration error in {config_file}: {issue}",
            tip="Check your configuration file and fix the issue",
            docs_url="https://github.com/context-engineer/docs/configuration",
        )


class AIModelNotAvailableError(ContextEngineerError):
    """Raised when AI model is not available."""

    def __init__(self, model_name: str):
        super().__init__(
            message=f"AI model '{model_name}' is not available",
            tip="Install AI dependencies with:\n   pip install 'context-engineer[ai]'\n   Or use --no-ai flag for lightweight mode",
            docs_url="https://github.com/context-engineer/docs/ai-setup",
        )


class InsufficientPermissionsError(ContextEngineerError):
    """Raised when user lacks permissions."""

    def __init__(self, path: str, operation: str):
        super().__init__(
            message=f"Insufficient permissions to {operation} {path}",
            tip="Check file/directory permissions:\n   ls -la {path}",
            docs_url="https://github.com/context-engineer/docs/troubleshooting",
        )


class TraceabilityGapError(ContextEngineerError):
    """Raised when traceability validation finds gaps."""

    def __init__(self, missing_items: list[str]):
        items_list = "\n   • ".join(missing_items[:5])
        more_msg = f"\n   ... and {len(missing_items) - 5} more" if len(missing_items) > 5 else ""

        super().__init__(
            message=f"Traceability gaps detected:\n   • {items_list}{more_msg}",
            tip="Ensure all FRs are covered by tasks:\n   ce validate --check-traceability --fix",
            docs_url="https://github.com/context-engineer/docs/traceability",
        )


__all__ = [
    "ContextEngineerError",
    "PRDNotFoundError",
    "PRPsNotFoundError",
    "TasksNotFoundError",
    "DependencyMissingError",
    "GitNotInitializedError",
    "ValidationFailedError",
    "StackNotSupportedError",
    "ConfigurationError",
    "AIModelNotAvailableError",
    "InsufficientPermissionsError",
    "TraceabilityGapError",
]
