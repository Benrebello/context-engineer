"""
Verification & UAT Engine
Automated verification and user acceptance testing.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class VerificationEngine:
    """
    Extracts testable deliverables from phases and runs verification.

    Produces UAT.md with an interactive checklist for user validation.
    """

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = Path(project_dir)
        self.output_dir = self.project_dir / ".planning"

    def extract_deliverables(self, phase_id: str, prp_data: dict[str, Any]) -> list[dict[str, str]]:
        """
        Extract testable deliverables from a PRP.

        Returns:
            List of deliverables with name, description, and verification command.
        """
        deliverables: list[dict[str, str]] = []

        # Extract from acceptance criteria
        for req in prp_data.get("functional_requirements", []):
            if isinstance(req, dict):
                criteria = req.get("acceptance_criteria", [])
                for criterion in criteria:
                    deliverables.append({
                        "name": req.get("title", "Unnamed"),
                        "criterion": criterion if isinstance(criterion, str) else str(criterion),
                        "status": "pending",
                    })

        # Extract from validation commands
        tasks = prp_data.get("tasks", [])
        for task in tasks:
            if isinstance(task, dict):
                validation = task.get("validation", [])
                for v in validation:
                    cmd = v.get("command", "") if isinstance(v, dict) else str(v)
                    if cmd:
                        deliverables.append({
                            "name": task.get("objective", "Unnamed task"),
                            "criterion": f"Command passes: `{cmd}`",
                            "status": "pending",
                        })

        return deliverables

    def generate_uat(self, phase_id: str, prp_data: dict[str, Any]) -> Path:
        """
        Generate a UAT.md for a specific phase.

        Args:
            phase_id: Phase identifier.
            prp_data: PRP data dictionary.

        Returns:
            Path to the generated UAT file.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir / f"{phase_id}-UAT.md"

        deliverables = self.extract_deliverables(phase_id, prp_data)
        content = self._render_uat(phase_id, prp_data, deliverables)
        output_file.write_text(content, encoding="utf-8")

        logger.info("UAT generated: %s", output_file)
        return output_file

    def update_uat_status(
        self, phase_id: str, deliverable_index: int, status: str, notes: str = ""
    ) -> None:
        """Update the status of a specific deliverable in the UAT."""
        uat_file = self.output_dir / f"{phase_id}-UAT.md"
        if not uat_file.exists():
            logger.warning("UAT file not found: %s", uat_file)
            return

        content = uat_file.read_text(encoding="utf-8")
        # Simple status replacement in markdown checkboxes
        lines = content.split("\n")
        checkbox_count = 0
        for i, line in enumerate(lines):
            if "- [ ]" in line or "- [x]" in line:
                if checkbox_count == deliverable_index:
                    if status == "passed":
                        lines[i] = line.replace("- [ ]", "- [x]")
                    if notes:
                        lines[i] += f" _{notes}_"
                    break
                checkbox_count += 1

        uat_file.write_text("\n".join(lines), encoding="utf-8")

    def _render_uat(
        self,
        phase_id: str,
        prp_data: dict[str, Any],
        deliverables: list[dict[str, str]],
    ) -> str:
        """Render the UAT document."""
        timestamp = datetime.now().isoformat()
        phase_name = prp_data.get("title", f"Phase {phase_id}")

        lines = [
            f"# UAT: {phase_name}",
            f"\n*Generated at: {timestamp}*\n",
            "## Verification Checklist\n",
        ]

        if not deliverables:
            lines.append("> No testable deliverables extracted for this phase.\n")
        else:
            for d in deliverables:
                lines.append(f"- [ ] **{d['name']}**: {d['criterion']}")

        lines.extend([
            "\n## Results\n",
            "| # | Deliverable | Status | Notes |",
            "|---|------------|--------|-------|",
        ])

        for idx, d in enumerate(deliverables):
            lines.append(f"| {idx + 1} | {d['name']} | ⬜ pending | |")

        lines.append(f"\n*Last verified: {timestamp}*")
        return "\n".join(lines)
