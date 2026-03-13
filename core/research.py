"""
Research Phase Engine
Generates technical research documentation before planning.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ResearchEngine:
    """
    Generates research documentation for a project phase.

    Analyzes requirements, identifies technical areas that need investigation,
    and produces a structured RESEARCH.md for each phase.
    """

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = Path(project_dir)
        self.output_dir = self.project_dir / ".planning" / "research"

    def generate_research(self, phase_id: str, prp_data: dict[str, Any]) -> Path:
        """
        Generate a RESEARCH.md for a specific phase.

        Args:
            phase_id: The phase identifier (e.g., "01", "02").
            prp_data: The PRP dictionary containing requirements.

        Returns:
            Path to the generated research file.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir / f"{phase_id}-RESEARCH.md"

        # Extract research areas from PRP
        areas = self._identify_research_areas(prp_data)
        risks = self._identify_risks(prp_data)
        stack_analysis = self._analyze_stack(prp_data)

        content = self._render_research(phase_id, areas, risks, stack_analysis, prp_data)
        output_file.write_text(content, encoding="utf-8")

        logger.info("Research generated: %s", output_file)
        return output_file

    def _identify_research_areas(self, prp_data: dict[str, Any]) -> list[dict[str, str]]:
        """Identify areas requiring technical investigation."""
        areas: list[dict[str, str]] = []

        # Analyze functional requirements for technical complexity
        requirements = prp_data.get("functional_requirements", [])
        for req in requirements:
            title = req if isinstance(req, str) else req.get("title", "")
            description = "" if isinstance(req, str) else req.get("description", "")

            # Flag areas with integration, security, or performance concerns
            keywords_map = {
                "integration": ["API", "integração", "webhook", "REST", "GraphQL", "gRPC"],
                "security": ["autenticação", "auth", "LGPD", "criptografia", "token", "JWT"],
                "performance": ["cache", "otimização", "batch", "async", "paralelo"],
                "data": ["migração", "schema", "banco", "database", "SQL", "ORM"],
            }

            for category, keywords in keywords_map.items():
                if any(kw.lower() in f"{title} {description}".lower() for kw in keywords):
                    areas.append({
                        "category": category,
                        "topic": title,
                        "reason": f"Detected {category}-related concern in requirement.",
                    })

        return areas

    def _identify_risks(self, prp_data: dict[str, Any]) -> list[dict[str, str]]:
        """Identify potential risks from PRP data."""
        risks: list[dict[str, str]] = []

        # Check for known risk patterns
        deps = prp_data.get("dependencies", [])
        if len(deps) > 5:
            risks.append({
                "risk": "High dependency count",
                "impact": "Integration complexity increases exponentially",
                "mitigation": "Consider dependency isolation and interface contracts",
            })

        non_functional = prp_data.get("non_functional_requirements", [])
        for nfr in non_functional:
            nfr_text = nfr if isinstance(nfr, str) else str(nfr)
            if any(kw in nfr_text.lower() for kw in ["scalability", "escalabilidade", "load"]):
                risks.append({
                    "risk": "Scalability requirement detected",
                    "impact": "Architecture must support horizontal scaling",
                    "mitigation": "Research load balancing and caching strategies",
                })

        return risks

    def _analyze_stack(self, prp_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze technology stack requirements."""
        stack = prp_data.get("stack", prp_data.get("technology_stack", ""))
        return {
            "stack": stack,
            "recommendation": f"Verify compatibility of {stack} with project constraints.",
        }

    def _render_research(
        self,
        phase_id: str,
        areas: list[dict[str, str]],
        risks: list[dict[str, str]],
        stack_analysis: dict[str, Any],
        prp_data: dict[str, Any],
    ) -> str:
        """Render the research document as Markdown."""
        timestamp = datetime.now().isoformat()
        phase_name = prp_data.get("title", prp_data.get("phase_name", f"Phase {phase_id}"))

        lines = [
            f"# Research: {phase_name}",
            f"\n*Generated at: {timestamp}*\n",
            "## Stack Analysis\n",
            f"- **Stack**: {stack_analysis.get('stack', 'Not specified')}",
            f"- **Recommendation**: {stack_analysis.get('recommendation', 'N/A')}\n",
        ]

        if areas:
            lines.append("## Research Areas\n")
            for area in areas:
                lines.append(f"### {area['category'].title()}: {area['topic']}")
                lines.append(f"\n- **Reason**: {area['reason']}\n")

        if risks:
            lines.append("## Risk Assessment\n")
            for risk in risks:
                lines.append(f"### ⚠️ {risk['risk']}")
                lines.append(f"\n- **Impact**: {risk['impact']}")
                lines.append(f"- **Mitigation**: {risk['mitigation']}\n")

        if not areas and not risks:
            lines.append("\n> No significant research areas or risks identified for this phase.\n")

        return "\n".join(lines)
