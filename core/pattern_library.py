"""
Pattern Library for reusable code patterns
"""

import re
from pathlib import Path
from typing import Any

import yaml


class PatternLibrary:
    """Library for managing and searching reusable code patterns"""

    def __init__(self, patterns_dir: Path):
        """
        Initialize pattern library

        Args:
            patterns_dir: Directory containing pattern files
        """
        self.patterns_dir = patterns_dir
        self.patterns: dict[str, Any] = {}
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load all patterns from patterns directory"""
        if not self.patterns_dir.exists():
            self.patterns_dir.mkdir(parents=True, exist_ok=True)
            return

        for pattern_file in self.patterns_dir.rglob("*.md"):
            try:
                pattern = self._parse_pattern(pattern_file)
                if pattern:
                    self.patterns[pattern["pattern_id"]] = pattern
            except Exception as e:
                print(f"Error loading pattern {pattern_file}: {e}")

    def _parse_pattern(self, file_path: Path) -> dict | None:
        """
        Parse pattern file with YAML frontmatter

        Args:
            file_path: Path to pattern markdown file

        Returns:
            Pattern dictionary or None if parsing fails
        """
        content = file_path.read_text(encoding="utf-8")

        # Extract YAML frontmatter
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        if not match:
            return None

        yaml_content = match.group(1)
        markdown_content = match.group(2)

        try:
            metadata = yaml.safe_load(yaml_content) or {}
            metadata["content"] = markdown_content
            metadata["file_path"] = str(file_path)
            return metadata
        except yaml.YAMLError:
            return None

    def search(
        self,
        stack: list[str] | None = None,
        category: str | None = None,
        complexity: str | None = None,
        tags: list[str] | None = None,
    ) -> list[dict]:
        """
        Search patterns by criteria

        Args:
            stack: List of stack technologies (e.g., ["python", "fastapi"])
            category: Pattern category (e.g., "authentication")
            complexity: Complexity level ("low", "medium", "high")
            tags: List of tags to match

        Returns:
            List of matching patterns
        """
        results = []

        for pattern_id, pattern in self.patterns.items():
            # Filter by stack
            if stack:
                pattern_stack = pattern.get("stack", [])
                if not any(s in pattern_stack for s in stack):
                    continue

            # Filter by category
            if category and pattern.get("category") != category:
                continue

            # Filter by complexity
            if complexity and pattern.get("complexity") != complexity:
                continue

            # Filter by tags
            if tags:
                pattern_tags = pattern.get("tags", [])
                if not any(tag in pattern_tags for tag in tags):
                    continue

            results.append(pattern)

        return results

    def get_pattern(self, pattern_id: str) -> dict | None:
        """
        Get pattern by ID

        Args:
            pattern_id: Pattern identifier

        Returns:
            Pattern dictionary or None if not found
        """
        return self.patterns.get(pattern_id)

    def suggest_patterns(self, context: dict) -> list[dict]:
        """
        Suggest patterns based on project context

        Args:
            context: Project context dictionary

        Returns:
            List of suggested patterns ordered by relevance
        """
        suggestions = []
        seen = set()

        # Search by stack
        stack = context.get("stack", [])
        if stack:
            stack_patterns = self.search(stack=stack)
            for pattern in stack_patterns:
                if pattern["pattern_id"] not in seen:
                    seen.add(pattern["pattern_id"])
                    suggestions.append(pattern)

        # Search by requirements
        requirements = context.get("requirements", [])
        for req in requirements:
            if "auth" in req.lower() or "login" in req.lower():
                auth_patterns = self.search(category="authentication")
                for pattern in auth_patterns:
                    if pattern["pattern_id"] not in seen:
                        seen.add(pattern["pattern_id"])
                        suggestions.append(pattern)

        # Search by tags
        tags = context.get("tags", [])
        if tags:
            tag_patterns = self.search(tags=tags)
            for pattern in tag_patterns:
                if pattern["pattern_id"] not in seen:
                    seen.add(pattern["pattern_id"])
                    suggestions.append(pattern)

        return suggestions

    def add_pattern(self, pattern: dict) -> None:
        """
        Add or update a pattern

        Args:
            pattern: Pattern dictionary
        """
        pattern_id = pattern.get("pattern_id")
        if not pattern_id:
            msg = "Pattern must have pattern_id"
            raise ValueError(msg)

        self.patterns[pattern_id] = pattern

    def list_categories(self) -> list[str]:
        """Get list of all categories"""
        categories = set()
        for pattern in self.patterns.values():
            category = pattern.get("category")
            if category:
                categories.add(category)
        return sorted(categories)
