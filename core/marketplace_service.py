"""Marketplace helpers extracted from the CLI layer."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from click import ClickException


class MarketplaceService:
    """Handles catalog loading and resource installation for the marketplace."""

    def __init__(self, repo_root: Path, catalog_path: Path | None = None) -> None:
        self.repo_root = repo_root
        default_catalog = repo_root / "docs" / "marketplace_catalog.json"
        self.catalog_path = catalog_path or default_catalog

    def load_catalog(self) -> list[dict]:
        """Load marketplace catalog from docs folder."""
        if not self.catalog_path.exists():
            return []
        try:
            with open(self.catalog_path, encoding="utf-8") as catalog_file:
                data = json.load(catalog_file)
                if isinstance(data, dict):
                    return list(data.get("items", []))
                if isinstance(data, list):
                    return data
                return []
        except Exception:
            return []

    def find_item(self, item_id: str) -> dict | None:
        """Return marketplace entry by ID."""
        item_id = (item_id or "").lower()
        for entry in self.load_catalog():
            if entry.get("id", "").lower() == item_id:
                return entry
        return None

    def copy_resource(
        self,
        item: dict,
        project_path: Path,
        destination: str | None = None,
    ) -> Path:
        """Copy marketplace resource into project."""
        source = item.get("source")
        if not source:
            raise ClickException("Item não possui campo 'source' para download local.")
        source_path = self.repo_root / source
        if not source_path.exists():
            msg = f"Arquivo de origem {source_path} não encontrado."
            raise ClickException(msg)

        target_dir = project_path / (destination or item.get("target_dir") or "marketplace")
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / source_path.name
        shutil.copyfile(source_path, target_path)
        return target_path
