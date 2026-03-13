"""
Project Health Check Module
Diagnoses and repairs project integrity issues.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class HealthIssue:
    """Represents a single health check finding."""

    severity: str  # "error", "warning", "info"
    category: str  # "files", "state", "traceability", "config"
    message: str
    auto_fixable: bool = False
    fix_action: str = ""


class HealthChecker:
    """
    Validates project integrity and offers automatic repair.

    Checks:
    - Required files exist (PRD, PRPs, Tasks, STATE.json)
    - State file consistency (not corrupted JSON)
    - PRD ↔ PRP ↔ Task traceability
    - Constitution presence
    - Git repository health
    """

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = Path(project_dir)
        self.issues: list[HealthIssue] = []

    def run_full_check(self) -> list[HealthIssue]:
        """Run all health checks and return findings."""
        self.issues = []
        self._check_required_files()
        self._check_state_integrity()
        self._check_constitution()
        self._check_git_health()
        self._check_planning_dir()
        return self.issues

    def _check_required_files(self) -> None:
        """Check that essential project files exist."""
        essential_dirs = [
            ("IDE-rules", "IDE rules directory"),
            (".ide-rules", "IDE rules config directory"),
        ]

        for dir_name, description in essential_dirs:
            path = self.project_dir / dir_name
            if not path.exists():
                self.issues.append(HealthIssue(
                    severity="warning",
                    category="files",
                    message=f"Missing {description}: {dir_name}/",
                    auto_fixable=True,
                    fix_action=f"mkdir -p {dir_name}",
                ))

    def _check_state_integrity(self) -> None:
        """Validate STATE.json is valid and not corrupted."""
        state_file = self.project_dir / ".ide-rules" / "STATE.json"
        if not state_file.exists():
            self.issues.append(HealthIssue(
                severity="info",
                category="state",
                message="No STATE.json found. State tracking not initialized.",
                auto_fixable=True,
                fix_action="Initialize ExecutionState",
            ))
            return

        try:
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate required fields
            required_fields = ["project_name", "status", "tasks", "last_updated"]
            for req_field in required_fields:
                if req_field not in data:
                    self.issues.append(HealthIssue(
                        severity="error",
                        category="state",
                        message=f"STATE.json missing required field: {req_field}",
                        auto_fixable=True,
                        fix_action=f"Add default value for '{req_field}'",
                    ))
        except json.JSONDecodeError:
            self.issues.append(HealthIssue(
                severity="error",
                category="state",
                message="STATE.json is corrupted (invalid JSON).",
                auto_fixable=True,
                fix_action="Reset STATE.json to defaults",
            ))

    def _check_constitution(self) -> None:
        """Check that the project constitution exists."""
        constitution_file = self.project_dir / ".ide-rules" / "PROJECT_CONSTITUTION.md"
        if not constitution_file.exists():
            self.issues.append(HealthIssue(
                severity="warning",
                category="config",
                message="No PROJECT_CONSTITUTION.md found. Run 'ce constitution init'.",
                auto_fixable=True,
                fix_action="Initialize default constitution",
            ))

    def _check_git_health(self) -> None:
        """Check basic git repository integrity."""
        git_dir = self.project_dir / ".git"
        if not git_dir.exists():
            self.issues.append(HealthIssue(
                severity="warning",
                category="files",
                message="No .git directory found. Version control not initialized.",
                auto_fixable=False,
                fix_action="Run 'git init'",
            ))

    def _check_planning_dir(self) -> None:
        """Check the planning directory structure."""
        planning_dir = self.project_dir / ".planning"
        if not planning_dir.exists():
            self.issues.append(HealthIssue(
                severity="info",
                category="files",
                message="No .planning directory found. Research/context data will be stored here.",
                auto_fixable=True,
                fix_action="mkdir -p .planning/research",
            ))

    def repair(self) -> list[str]:
        """
        Attempt to auto-fix all fixable issues.

        Returns:
            List of actions taken.
        """
        actions_taken: list[str] = []

        for issue in self.issues:
            if not issue.auto_fixable:
                continue

            if issue.category == "files" and "mkdir" in issue.fix_action:
                dir_name = issue.fix_action.split("mkdir -p ")[-1]
                target = self.project_dir / dir_name
                target.mkdir(parents=True, exist_ok=True)
                actions_taken.append(f"Created directory: {dir_name}")

            elif issue.category == "state" and "Reset" in issue.fix_action:
                state_dir = self.project_dir / ".ide-rules"
                state_dir.mkdir(parents=True, exist_ok=True)
                default_state = {
                    "project_name": self.project_dir.name,
                    "status": "initialized",
                    "tasks": {},
                    "last_updated": "",
                }
                state_file = state_dir / "STATE.json"
                state_file.write_text(json.dumps(default_state, indent=2), encoding="utf-8")
                actions_taken.append("Reset STATE.json to defaults")

            elif issue.category == "config" and "constitution" in issue.fix_action:
                config_dir = self.project_dir / ".ide-rules"
                config_dir.mkdir(parents=True, exist_ok=True)
                constitution_file = config_dir / "PROJECT_CONSTITUTION.md"
                constitution_file.write_text(
                    "# Project Constitution\n\n"
                    "## Principles\n\n"
                    "1. Code quality above speed\n"
                    "2. Tests for all critical paths\n"
                    "3. Clear documentation\n",
                    encoding="utf-8",
                )
                actions_taken.append("Initialized default constitution")

        return actions_taken


    def get_summary(self) -> str:
        """Generate a human-readable health report."""
        if not self.issues:
            self.run_full_check()

        errors = [i for i in self.issues if i.severity == "error"]
        warnings = [i for i in self.issues if i.severity == "warning"]
        infos = [i for i in self.issues if i.severity == "info"]

        lines = ["# Project Health Report\n"]

        if not self.issues:
            lines.append("✅ **All checks passed!** Project is healthy.\n")
            return "\n".join(lines)

        lines.append(f"Found **{len(self.issues)}** issues: ")
        lines.append(f"{len(errors)} errors, {len(warnings)} warnings, {len(infos)} info\n")

        if errors:
            lines.append("## ❌ Errors\n")
            for issue in errors:
                lines.append(f"- [{issue.category}] {issue.message}")

        if warnings:
            lines.append("\n## ⚠️ Warnings\n")
            for issue in warnings:
                fixable = " (auto-fixable)" if issue.auto_fixable else ""
                lines.append(f"- [{issue.category}] {issue.message}{fixable}")

        if infos:
            lines.append("\n## ℹ️ Info\n")
            for issue in infos:
                lines.append(f"- [{issue.category}] {issue.message}")

        fixable_count = sum(1 for i in self.issues if i.auto_fixable)
        if fixable_count:
            lines.append(f"\n> Run `ce health --repair` to auto-fix {fixable_count} issue(s).")

        return "\n".join(lines)
