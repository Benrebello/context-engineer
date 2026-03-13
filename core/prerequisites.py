"""
Prerequisites validation system for Context Engineer commands.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from core.exceptions import (
    DependencyMissingError,
    GitNotInitializedError,
    PRDNotFoundError,
    PRPsNotFoundError,
)


class PrerequisiteChecker:
    """Check prerequisites before running commands."""

    def __init__(self, project_dir: Path):
        """
        Initialize prerequisite checker.

        Args:
            project_dir: Project directory to check
        """
        self.project_dir = Path(project_dir).resolve()

    def check_prd_exists(self, raise_error: bool = True) -> bool:
        """
        Check if PRD file exists.

        Args:
            raise_error: Whether to raise error if not found

        Returns:
            True if PRD exists

        Raises:
            PRDNotFoundError: If PRD not found and raise_error=True
        """
        prd_locations = [
            self.project_dir / "prd" / "PRD.md",
            self.project_dir / "prd" / "prd_structured.json",
            self.project_dir / "PRD.md",
            self.project_dir / "prd_structured.json",
        ]

        for prd_path in prd_locations:
            if prd_path.exists():
                return True

        if raise_error:
            searched = [str(p) for p in prd_locations]
            raise PRDNotFoundError(searched_paths=searched)

        return False

    def check_prps_exist(self, raise_error: bool = True) -> bool:
        """
        Check if PRP files exist.

        Args:
            raise_error: Whether to raise error if not found

        Returns:
            True if PRPs exist

        Raises:
            PRPsNotFoundError: If PRPs not found and raise_error=True
        """
        prps_locations = [
            self.project_dir / "prps",
            self.project_dir / "PRPs",
        ]

        for prps_dir in prps_locations:
            if prps_dir.exists() and prps_dir.is_dir():
                # Check if there are any PRP files
                prp_files = list(prps_dir.glob("*.md")) + list(prps_dir.glob("*.json"))
                if prp_files:
                    return True

        if raise_error:
            searched = [str(p) for p in prps_locations]
            raise PRPsNotFoundError(searched_paths=searched)

        return False

    def check_git_initialized(self, raise_error: bool = True) -> bool:
        """
        Check if Git repository is initialized.

        Args:
            raise_error: Whether to raise error if not initialized

        Returns:
            True if Git is initialized

        Raises:
            GitNotInitializedError: If Git not initialized and raise_error=True
        """
        git_dir = self.project_dir / ".git"

        if git_dir.exists() and git_dir.is_dir():
            return True

        if raise_error:
            raise GitNotInitializedError(str(self.project_dir))

        return False

    def check_command_available(self, command: str, raise_error: bool = True) -> bool:
        """
        Check if a command is available in PATH.

        Args:
            command: Command name to check
            raise_error: Whether to raise error if not found

        Returns:
            True if command is available

        Raises:
            DependencyMissingError: If command not found and raise_error=True
        """
        if shutil.which(command):
            return True

        if raise_error:
            raise DependencyMissingError(
                dependency=command,
                install_command=f"Install {command} following its official documentation",
            )

        return False

    def check_python_package(self, package: str, raise_error: bool = True) -> bool:
        """
        Check if a Python package is installed.

        Args:
            package: Package name to check
            raise_error: Whether to raise error if not found

        Returns:
            True if package is installed

        Raises:
            DependencyMissingError: If package not found and raise_error=True
        """
        try:
            __import__(package.replace("-", "_"))
            return True
        except ImportError:
            if raise_error:
                raise DependencyMissingError(
                    dependency=package,
                    install_command=f"pip install {package}",
                )
            return False

    def check_disk_space(self, required_mb: int = 100, raise_error: bool = True) -> bool:
        """
        Check if sufficient disk space is available.

        Args:
            required_mb: Required space in megabytes
            raise_error: Whether to raise error if insufficient

        Returns:
            True if sufficient space available

        Raises:
            ContextEngineerError: If insufficient space and raise_error=True
        """
        try:
            import shutil

            stat = shutil.disk_usage(self.project_dir)
            available_mb = stat.free / (1024 * 1024)

            if available_mb >= required_mb:
                return True

            if raise_error:
                from core.exceptions import ContextEngineerError

                raise ContextEngineerError(
                    message=f"Insufficient disk space: {available_mb:.0f}MB available, {required_mb}MB required",
                    tip="Free up some disk space and try again",
                )

            return False
        except Exception:
            # If we can't check, assume it's OK
            return True

    def check_write_permissions(self, raise_error: bool = True) -> bool:
        """
        Check if we have write permissions in project directory.

        Args:
            raise_error: Whether to raise error if no permissions

        Returns:
            True if we have write permissions

        Raises:
            InsufficientPermissionsError: If no permissions and raise_error=True
        """
        test_file = self.project_dir / ".ce_write_test"

        try:
            test_file.touch()
            test_file.unlink()
            return True
        except (PermissionError, OSError):
            if raise_error:
                from core.exceptions import InsufficientPermissionsError

                raise InsufficientPermissionsError(
                    path=str(self.project_dir),
                    operation="write to",
                )
            return False

    def check_all_for_command(self, command_name: str) -> dict[str, Any]:
        """
        Check all prerequisites for a specific command.

        Args:
            command_name: Name of the command to check prerequisites for

        Returns:
            Dictionary with check results

        Raises:
            Various exceptions if prerequisites not met
        """
        results = {
            "command": command_name,
            "checks_passed": [],
            "checks_failed": [],
            "warnings": [],
        }

        # Define prerequisites per command
        prerequisites = {
            "generate-prps": [
                ("prd_exists", "PRD file must exist"),
                ("write_permissions", "Write permissions required"),
                ("disk_space", "Sufficient disk space required"),
            ],
            "generate-tasks": [
                ("prps_exist", "PRP files must exist"),
                ("write_permissions", "Write permissions required"),
                ("disk_space", "Sufficient disk space required"),
            ],
            "validate": [
                ("prd_exists", "PRD file must exist"),
            ],
            "install-hooks": [
                ("git_initialized", "Git repository must be initialized"),
                ("write_permissions", "Write permissions required"),
            ],
            "ci-bootstrap": [
                ("git_initialized", "Git repository must be initialized"),
                ("write_permissions", "Write permissions required"),
            ],
        }

        checks = prerequisites.get(command_name, [])

        for check_name, description in checks:
            try:
                if check_name == "prd_exists":
                    self.check_prd_exists(raise_error=True)
                elif check_name == "prps_exist":
                    self.check_prps_exist(raise_error=True)
                elif check_name == "git_initialized":
                    self.check_git_initialized(raise_error=True)
                elif check_name == "write_permissions":
                    self.check_write_permissions(raise_error=True)
                elif check_name == "disk_space":
                    self.check_disk_space(raise_error=True)

                results["checks_passed"].append(check_name)
            except Exception as e:
                results["checks_failed"].append(
                    {
                        "check": check_name,
                        "description": description,
                        "error": str(e),
                    }
                )
                # Re-raise the first failure
                raise

        return results


def validate_prerequisites(command_name: str, project_dir: Path | None = None) -> bool:
    """
    Validate prerequisites for a command.

    Args:
        command_name: Name of the command
        project_dir: Project directory (defaults to current directory)

    Returns:
        True if all prerequisites are met

    Raises:
        Various exceptions if prerequisites not met
    """
    if project_dir is None:
        project_dir = Path.cwd()

    checker = PrerequisiteChecker(project_dir)
    results = checker.check_all_for_command(command_name)

    return len(results["checks_failed"]) == 0


__all__ = [
    "PrerequisiteChecker",
    "validate_prerequisites",
]
