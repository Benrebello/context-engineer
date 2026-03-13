"""Project configuration helpers extracted from the CLI."""

from __future__ import annotations

import json
from pathlib import Path


class ProjectConfigService:
    """Handles reading and writing project-level configuration files."""

    def __init__(self, config_filename: str = ".ce-config.json") -> None:
        self.config_filename = config_filename

    @staticmethod
    def _normalize_dir(path: Path) -> Path:
        """Ensure the given path points to a directory."""
        resolved = path.resolve()
        return resolved if resolved.is_dir() else resolved.parent

    def _find_project_root(self, start_dir: Path) -> Path | None:
        """Walk upwards to locate the directory containing the config file."""
        current = self._normalize_dir(start_dir)
        for candidate in [current, *current.parents]:
            if (candidate / self.config_filename).exists():
                return candidate
        return None

    def load_project_config(self, start_dir: Path | None = None) -> tuple[Path | None, dict]:
        """Load project configuration from the nearest config file."""
        start_dir = start_dir or Path.cwd()
        project_root = self._find_project_root(start_dir)
        if not project_root:
            return None, {}
        config_path = project_root / self.config_filename
        try:
            data = config_path.read_text(encoding="utf-8")
            return project_root, json.loads(data)
        except Exception:
            return project_root, {}

    def save_project_config(self, project_dir: Path, overrides: dict) -> Path:
        """Persist project configuration merging with existing values."""
        project_dir = project_dir.resolve()
        config_path = project_dir / self.config_filename
        existing: dict = {}
        if config_path.exists():
            try:
                existing = json.loads(config_path.read_text(encoding="utf-8"))
            except Exception:
                existing = {}
        existing.update(overrides)
        config_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
        return config_path
