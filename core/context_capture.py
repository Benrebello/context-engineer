"""
Context Capture Module
Captures user decisions and preferences before technical planning.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ContextCapture:
    """
    Identifies gray areas in a phase and captures user decisions.

    Produces a CONTEXT.md that feeds into both the Research Engine
    and the Planner, ensuring that user preferences are respected.
    """

    # Categories of questions based on feature type
    QUESTION_TEMPLATES: dict[str, list[str]] = {
        "visual": [
            "Preferred layout style (grid, list, cards)?",
            "Density preference (compact, comfortable, spacious)?",
            "Desired interaction patterns (hover, click, drag-drop)?",
            "Empty state behavior (placeholder, illustration, CTA)?",
            "Responsive breakpoints priority (mobile-first, desktop-first)?",
        ],
        "api": [
            "Response format preference (JSON, XML, Protocol Buffers)?",
            "Error handling strategy (HTTP codes, error objects, both)?",
            "Pagination style (offset, cursor, keyset)?",
            "Versioning strategy (URL path, header, query param)?",
            "Rate limiting requirements?",
        ],
        "data": [
            "Data model approach (normalized, denormalized, hybrid)?",
            "Migration strategy (incremental, big-bang)?",
            "Backup and recovery requirements?",
            "Data retention policy?",
        ],
        "content": [
            "Content structure (hierarchical, flat, tagged)?",
            "Tone and voice guidelines?",
            "Localization requirements?",
        ],
    }

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = Path(project_dir)
        self.output_dir = self.project_dir / ".planning"

    def analyze_phase(self, phase_id: str, prp_data: dict[str, Any]) -> dict[str, list[str]]:
        """
        Analyze a phase and identify relevant question categories.

        Returns:
            Dict mapping category names to lists of relevant questions.
        """
        detected: dict[str, list[str]] = {}

        # Detect feature types from PRP content
        prp_text = str(prp_data).lower()

        category_keywords = {
            "visual": ["ui", "interface", "tela", "layout", "componente", "front", "view", "page"],
            "api": ["api", "endpoint", "rest", "graphql", "route", "controller", "service"],
            "data": ["database", "modelo", "schema", "migration", "sql", "orm", "entity"],
            "content": ["conteúdo", "content", "cms", "blog", "documentation", "i18n"],
        }

        for category, keywords in category_keywords.items():
            if any(kw in prp_text for kw in keywords):
                detected[category] = self.QUESTION_TEMPLATES.get(category, [])

        return detected

    def generate_context(
        self,
        phase_id: str,
        prp_data: dict[str, Any],
        answers: dict[str, str] | None = None,
    ) -> Path:
        """
        Generate a CONTEXT.md for a phase.

        Args:
            phase_id: Phase identifier.
            prp_data: PRP data dictionary.
            answers: Optional pre-filled answers (key=question, value=answer).

        Returns:
            Path to the generated context file.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir / f"{phase_id}-CONTEXT.md"

        questions = self.analyze_phase(phase_id, prp_data)
        content = self._render_context(phase_id, prp_data, questions, answers)
        output_file.write_text(content, encoding="utf-8")

        logger.info("Context captured: %s", output_file)
        return output_file

    def _render_context(
        self,
        phase_id: str,
        prp_data: dict[str, Any],
        questions: dict[str, list[str]],
        answers: dict[str, str] | None = None,
    ) -> str:
        """Render the context document."""
        timestamp = datetime.now().isoformat()
        phase_name = prp_data.get("title", f"Phase {phase_id}")
        answers = answers or {}

        lines = [
            f"# Context: {phase_name}",
            f"\n*Captured at: {timestamp}*\n",
            "## Decisions & Preferences\n",
        ]

        if not questions:
            lines.append("> No specific gray areas detected for this phase.\n")
        else:
            for category, category_questions in questions.items():
                lines.append(f"### {category.title()}\n")
                for q in category_questions:
                    answer = answers.get(q, "_Not yet decided_")
                    lines.append(f"- **Q**: {q}")
                    lines.append(f"  - **A**: {answer}\n")

        return "\n".join(lines)
