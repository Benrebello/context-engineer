"""Tests for core.template_engine module."""

from pathlib import Path

import pytest

from core.template_engine import TemplateEngine


@pytest.fixture()
def templates_dir():
    return Path(__file__).parent.parent / "templates"


@pytest.fixture()
def engine(templates_dir):
    return TemplateEngine(templates_dir)


class TestTemplateEngine:
    def test_init(self, templates_dir):
        eng = TemplateEngine(templates_dir)
        assert eng is not None

    def test_render_readme(self, engine):
        context = {
            "project_name": "test-project",
            "stack": "python-fastapi",
            "stack_description": "Python with FastAPI",
            "stack_structure": {},
            "stack_commands": {},
            "init_command": "pip install",
            "install_command": "pip install -r requirements.txt",
        }
        result = engine.render("base/files/readme.md.j2", context)
        assert "test-project" in result

    def test_render_gitignore(self, engine):
        context = {"stack": "python-fastapi"}
        result = engine.render("base/files/gitignore.j2", context)
        assert isinstance(result, str)

    def test_render_nonexistent_template(self, engine):
        with pytest.raises(FileNotFoundError):
            engine.render("nonexistent/template.j2", {})

    def test_load_template_config(self, engine, templates_dir):
        config_path = templates_dir / "base" / "template.yaml"
        if config_path.exists():
            config = engine.load_template_config(config_path)
            assert isinstance(config, dict)

    def test_load_template_config_custom(self, tmp_path):
        eng = TemplateEngine(tmp_path)
        config_file = tmp_path / "template.yaml"
        config_file.write_text("variables:\n  name:\n    default: test\n  stack:\n    default: python\n", encoding="utf-8")
        config = eng.load_template_config(config_file)
        assert "variables" in config

    def test_get_available_variables(self, engine):
        config = {"variables": {"name": {"default": "test"}, "stack": {"default": "python"}}}
        variables = engine.get_available_variables(config)
        assert "name" in variables
        assert "stack" in variables

    def test_get_available_variables_empty(self, engine):
        variables = engine.get_available_variables({})
        assert variables == []

    def test_generate_phase(self, engine, tmp_path):
        # Create a simple template
        tmpl_dir = tmp_path / "templates"
        tmpl_dir.mkdir()
        (tmpl_dir / "phase.md.j2").write_text("# {{ phase_name }}\n{{ content }}", encoding="utf-8")
        eng = TemplateEngine(tmpl_dir)
        phase_config = {"id": "F0", "template": "phase.md.j2"}
        result = eng.generate_phase(phase_config, {"phase_name": "Plan", "content": "Planning phase"})
        assert "Plan" in result
        assert "Planning phase" in result

    def test_generate_phase_no_template(self, engine):
        with pytest.raises(ValueError, match="no template"):
            engine.generate_phase({"id": "F0"}, {})

    def test_generate_phase_missing_template(self, engine):
        with pytest.raises(FileNotFoundError):
            engine.generate_phase({"id": "F0", "template": "nonexistent.j2"}, {})

    def test_generate_phase_with_variables(self, tmp_path):
        tmpl_dir = tmp_path / "templates"
        tmpl_dir.mkdir()
        (tmpl_dir / "phase.md.j2").write_text("# {{ title }}", encoding="utf-8")
        eng = TemplateEngine(tmpl_dir)
        phase_config = {
            "id": "F0",
            "template": "phase.md.j2",
            "variables": {"title": {"default": "Default Title"}},
        }
        result = eng.generate_phase(phase_config, {})
        assert "Default Title" in result

    def test_generate_project(self, tmp_path):
        tmpl_dir = tmp_path / "templates"
        base_dir = tmpl_dir / "test-template"
        base_dir.mkdir(parents=True)
        (base_dir / "phase.md.j2").write_text("# {{ project_name }} - Phase", encoding="utf-8")
        config = {
            "phases": [
                {"id": "F0", "template": "phase.md.j2"},
            ]
        }
        import yaml
        (base_dir / "template.yaml").write_text(yaml.dump(config), encoding="utf-8")
        eng = TemplateEngine(tmpl_dir)
        output = tmp_path / "output"
        result = eng.generate_project("test-template", {"project_name": "MyProject"}, output)
        assert result["success"] is True
        assert len(result["generated_files"]) == 1

    def test_generate_project_missing_config(self, tmp_path):
        eng = TemplateEngine(tmp_path)
        with pytest.raises(FileNotFoundError):
            eng.generate_project("nonexistent", {}, tmp_path / "output")
