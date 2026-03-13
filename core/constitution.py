"""
Project Constitution Module
Manages project principles and development guidelines
"""

from pathlib import Path
import json
from typing import Any, Dict, List

class Constitution:
    """Project Constitution to enforce development principles"""

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.constitution_file = self.project_dir / ".ide-rules" / "PROJECT_CONSTITUTION.md"
        self.principles: List[str] = []

    def initialize(self, principles: List[str] | None = None):
        """Initialize the constitution with base principles"""
        if principles is None:
            principles = [
                "Prioritize Clean Architecture layers (Domain > Application > Infrastructure > Interfaces).",
                "Ensure at least 80% unit test coverage for all new logic.",
                "Follow SOLID principles and design patterns defined in the pattern library.",
                "Use standardized XML task definitions for all AI-assisted implementation.",
                "Maintain atomic Git commits per task.",
                "Strictly follow LGPD and security standards defined in 08_security.md."
            ]
        
        self.principles = principles
        self._save()

    def _save(self):
        """Save constitution to markdown file"""
        content = "# Project Constitution\n\n## Development Principles\n\n"
        for p in self.principles:
            content += f"- {p}\n"
        
        self.constitution_file.parent.mkdir(parents=True, exist_ok=True)
        self.constitution_file.write_text(content, encoding="utf-8")

    def load(self) -> List[str]:
        """Load principles from file"""
        if not self.constitution_file.exists():
            return []
        
        content = self.constitution_file.read_text(encoding="utf-8")
        # Simple parser for list items
        self.principles = [line.strip("- ").strip() for line in content.split("\n") if line.startswith("- ")]
        return self.principles

    def add_principle(self, principle: str):
        """Add a new principle to the constitution"""
        self.load()
        if principle not in self.principles:
            self.principles.append(principle)
            self._save()
