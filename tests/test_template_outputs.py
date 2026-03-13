import json
from pathlib import Path

from core.engine import ContextEngine


def _init_project(tmp_path: Path, project_name: str, stack: str) -> Path:
    """Helper to initialize a project and return its output directory."""
    output_dir = tmp_path / project_name
    engine = ContextEngine()
    engine.init_project(template="base", project_name=project_name, stack=stack, output_dir=output_dir)
    return output_dir


def test_python_stack_templates(tmp_path):
    project_dir = _init_project(tmp_path, "AnalyticsAPI", "python-fastapi")

    readme = (project_dir / "README.md").read_text(encoding="utf-8")
    gitignore = (project_dir / ".gitignore").read_text(encoding="utf-8")
    env_example = (project_dir / ".env.example").read_text(encoding="utf-8")
    license_txt = (project_dir / "LICENSE").read_text(encoding="utf-8")
    pyproject = (project_dir / "pyproject.toml").read_text(encoding="utf-8")

    assert "# AnalyticsAPI" in readme
    assert "Project generated with Context Engineer" in readme
    assert "__pycache__/" in gitignore
    assert "DATABASE_URL" in env_example
    assert "MIT License" in license_txt
    assert 'name = "analyticsapi"' in pyproject
    assert "[project]" in pyproject


def test_node_stack_templates(tmp_path):
    project_dir = _init_project(tmp_path, "WebPortal", "node-react")

    readme = (project_dir / "README.md").read_text(encoding="utf-8")
    gitignore = (project_dir / ".gitignore").read_text(encoding="utf-8")
    env_example = (project_dir / ".env.example").read_text(encoding="utf-8")
    package_json = json.loads((project_dir / "package.json").read_text(encoding="utf-8"))

    assert "# WebPortal" in readme
    assert "node-react" in readme.lower()
    assert "node_modules/" in gitignore
    assert "VITE_API_URL" in env_example
    assert package_json["name"] == "webportal"
    assert "scripts" in package_json
    assert "dependencies" in package_json
