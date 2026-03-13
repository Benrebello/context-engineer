"""
Tests for the MarketplaceService helper.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click import ClickException

from core.marketplace_service import MarketplaceService


def _write_catalog(repo_root: Path, items: list[dict]) -> Path:
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = docs_dir / "marketplace_catalog.json"
    catalog_path.write_text(json.dumps(items), encoding="utf-8")
    return catalog_path


def _write_resource(repo_root: Path, relative_path: str, content: str) -> Path:
    resource_path = repo_root / relative_path
    resource_path.parent.mkdir(parents=True, exist_ok=True)
    resource_path.write_text(content, encoding="utf-8")
    return resource_path


def test_load_catalog_and_find_item(tmp_path: Path) -> None:
    """Ensure catalogs are loaded and searchable by ID."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_catalog(
        repo_root,
        [
            {"id": "starter-kit", "name": "Starter Kit", "description": "Base templates"},
        ],
    )

    service = MarketplaceService(repo_root=repo_root)

    catalog = service.load_catalog()
    assert len(catalog) == 1
    assert catalog[0]["id"] == "starter-kit"

    found = service.find_item("starter-kit")
    assert found is not None
    assert found["name"] == "Starter Kit"
    assert service.find_item("missing") is None


def test_copy_resource_creates_target_file(tmp_path: Path) -> None:
    """Copy resource files into a destination project folder."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    relative_path = "templates/resources/example.txt"
    _write_resource(repo_root, relative_path, "hello marketplace")

    service = MarketplaceService(repo_root=repo_root)
    item = {"id": "sample", "source": relative_path, "target_dir": "extras"}

    project_path = tmp_path / "project"
    result_path = service.copy_resource(item, project_path=project_path)

    assert result_path.read_text(encoding="utf-8") == "hello marketplace"
    assert result_path.parent == project_path / "extras"


def test_copy_resource_without_source_raises(tmp_path: Path) -> None:
    """Validate ClickException when source metadata is absent."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    service = MarketplaceService(repo_root=repo_root)

    with pytest.raises(ClickException):
        service.copy_resource({}, project_path=tmp_path / "project")


def test_copy_resource_with_missing_file_raises(tmp_path: Path) -> None:
    """Validate ClickException when referenced source file is missing."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    service = MarketplaceService(repo_root=repo_root)
    missing_path = "templates/missing.txt"
    item = {"source": missing_path}

    with pytest.raises(ClickException):
        service.copy_resource(item, project_path=tmp_path / "project")
