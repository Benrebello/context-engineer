"""Tests for core.pattern_library module."""

import pytest

from pathlib import Path
from core.pattern_library import PatternLibrary


@pytest.fixture()
def patterns_dir(tmp_path):
    """Create a temporary patterns directory with sample patterns."""
    auth_dir = tmp_path / "authentication"
    auth_dir.mkdir()
    (auth_dir / "jwt.md").write_text(
        "---\npattern_id: jwt-auth\ncategory: authentication\nstack:\n  - python\n  - fastapi\ncomplexity: medium\ntags:\n  - security\n  - jwt\n---\n# JWT Auth Pattern\nSample content.\n",
        encoding="utf-8",
    )
    api_dir = tmp_path / "api-patterns"
    api_dir.mkdir()
    (api_dir / "crud.md").write_text(
        "---\npattern_id: restful-crud\ncategory: api\nstack:\n  - python\n  - node\ncomplexity: low\ntags:\n  - rest\n  - crud\n---\n# CRUD Pattern\nCRUD content.\n",
        encoding="utf-8",
    )
    # File without frontmatter
    (api_dir / "no_frontmatter.md").write_text("# No frontmatter\nJust text.", encoding="utf-8")
    # File with invalid YAML
    (api_dir / "bad_yaml.md").write_text("---\n: invalid: yaml: [broken\n---\nBody", encoding="utf-8")
    return tmp_path


def test_load_patterns(patterns_dir):
    lib = PatternLibrary(patterns_dir)
    assert len(lib.patterns) >= 2
    assert "jwt-auth" in lib.patterns
    assert "restful-crud" in lib.patterns


def test_load_patterns_empty_dir(tmp_path):
    lib = PatternLibrary(tmp_path / "nonexistent")
    assert lib.patterns == {}


def test_search_by_stack(patterns_dir):
    lib = PatternLibrary(patterns_dir)
    results = lib.search(stack=["python"])
    assert len(results) == 2


def test_search_by_stack_no_match(patterns_dir):
    lib = PatternLibrary(patterns_dir)
    results = lib.search(stack=["ruby"])
    assert results == []


def test_search_by_category(patterns_dir):
    lib = PatternLibrary(patterns_dir)
    results = lib.search(category="authentication")
    assert len(results) == 1
    assert results[0]["pattern_id"] == "jwt-auth"


def test_search_by_complexity(patterns_dir):
    lib = PatternLibrary(patterns_dir)
    results = lib.search(complexity="low")
    assert len(results) == 1
    assert results[0]["pattern_id"] == "restful-crud"


def test_search_by_tags(patterns_dir):
    lib = PatternLibrary(patterns_dir)
    results = lib.search(tags=["jwt"])
    assert len(results) == 1


def test_search_combined(patterns_dir):
    lib = PatternLibrary(patterns_dir)
    results = lib.search(stack=["python"], category="api")
    assert len(results) == 1


def test_get_pattern(patterns_dir):
    lib = PatternLibrary(patterns_dir)
    p = lib.get_pattern("jwt-auth")
    assert p is not None
    assert p["category"] == "authentication"


def test_get_pattern_not_found(patterns_dir):
    lib = PatternLibrary(patterns_dir)
    assert lib.get_pattern("nonexistent") is None


def test_suggest_patterns_by_stack(patterns_dir):
    lib = PatternLibrary(patterns_dir)
    suggestions = lib.suggest_patterns({"stack": ["python"]})
    assert len(suggestions) >= 1


def test_suggest_patterns_by_auth_requirement(patterns_dir):
    lib = PatternLibrary(patterns_dir)
    suggestions = lib.suggest_patterns({
        "stack": [],
        "requirements": ["User authentication with login"],
    })
    assert any(s["pattern_id"] == "jwt-auth" for s in suggestions)


def test_suggest_patterns_by_tags(patterns_dir):
    lib = PatternLibrary(patterns_dir)
    suggestions = lib.suggest_patterns({"stack": [], "tags": ["crud"]})
    assert any(s["pattern_id"] == "restful-crud" for s in suggestions)


def test_suggest_patterns_deduplication(patterns_dir):
    lib = PatternLibrary(patterns_dir)
    suggestions = lib.suggest_patterns({
        "stack": ["python"],
        "tags": ["jwt"],
        "requirements": ["auth login"],
    })
    ids = [s["pattern_id"] for s in suggestions]
    assert len(ids) == len(set(ids)), "Duplicates found in suggestions"


def test_add_pattern(patterns_dir):
    lib = PatternLibrary(patterns_dir)
    lib.add_pattern({"pattern_id": "new-pattern", "category": "test"})
    assert "new-pattern" in lib.patterns


def test_add_pattern_no_id(patterns_dir):
    lib = PatternLibrary(patterns_dir)
    with pytest.raises(ValueError, match="pattern_id"):
        lib.add_pattern({"category": "test"})


def test_list_categories(patterns_dir):
    lib = PatternLibrary(patterns_dir)
    cats = lib.list_categories()
    assert "authentication" in cats
    assert "api" in cats
    assert cats == sorted(cats)
