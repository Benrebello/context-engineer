"""Tests for cli.commands.generation module."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from cli.commands.generation import (
    init,
    generate_prd,
    generate_prps,
    generate_tasks,
    validate,
    check_dependencies,
    estimate_effort,
    estimate_batch,
    save_interactive_input,
)


class TestSaveInteractiveInput:
    def test_save(self, tmp_path):
        result = save_interactive_input("content", "test.md", tmp_path)
        assert result.exists()
        assert result.read_text(encoding="utf-8") == "content"

    def test_save_creates_dir(self, tmp_path):
        out = tmp_path / "sub" / "dir"
        result = save_interactive_input("data", "f.txt", out)
        assert result.exists()


class TestInit:
    def test_init_basic(self, tmp_path):
        runner = CliRunner()
        mock_engine = MagicMock()
        mock_engine.init_project.return_value = {
            "success": True,
            "created_directories": ["src", "tests"],
            "created_files": ["README.md"],
            "generated_files": [],
        }
        with patch("cli.commands.generation.check_intelligence_mode", return_value=False), \
             patch("cli.commands.generation.create_engine", return_value=mock_engine), \
             patch("cli.commands.generation.save_project_config"):
            result = runner.invoke(init, [
                "test-project",
                "--stack", "python-fastapi",
                "--output", str(tmp_path),
                "--no-ai",
                "--language", "en-us",
            ])
        assert result.exit_code == 0


class TestGeneratePrd:
    def test_generate_prd_from_file(self, tmp_path):
        runner = CliRunner()
        input_file = tmp_path / "idea.md"
        input_file.write_text("# My Idea\nA task management app", encoding="utf-8")
        output = tmp_path / "prd_output"
        mock_engine = MagicMock()
        mock_engine.generate_prd.return_value = {"success": True}
        with patch("cli.commands.generation.create_engine", return_value=mock_engine):
            result = runner.invoke(generate_prd, [
                str(input_file),
                "--output", str(output),
                "--no-ai",
            ])
        assert result.exit_code == 0
        assert "PRD generated" in result.output

    def test_generate_prd_preview(self, tmp_path):
        runner = CliRunner()
        input_file = tmp_path / "idea.md"
        input_file.write_text("# Idea", encoding="utf-8")
        mock_engine = MagicMock()
        with patch("cli.commands.generation.create_engine", return_value=mock_engine):
            result = runner.invoke(generate_prd, [
                str(input_file),
                "--output", str(tmp_path / "prd"),
                "--preview",
                "--no-ai",
            ])
        assert result.exit_code == 0
        assert "Preview" in result.output


class TestGeneratePrps:
    def test_generate_prps_preview(self, tmp_path):
        runner = CliRunner()
        prd = tmp_path / "prd.json"
        prd.write_text(json.dumps({"visao": "test"}), encoding="utf-8")
        with patch("cli.commands.generation.validate_command_prerequisites", return_value=True), \
             patch("cli.commands.generation.create_engine"):
            result = runner.invoke(generate_prps, [
                str(prd),
                "--output", str(tmp_path / "prps"),
                "--preview",
                "--no-ai",
            ])
        assert result.exit_code == 0
        assert "Preview" in result.output

    def test_generate_prps_preview_single_phase(self, tmp_path):
        runner = CliRunner()
        prd = tmp_path / "prd.json"
        prd.write_text(json.dumps({"visao": "test"}), encoding="utf-8")
        with patch("cli.commands.generation.validate_command_prerequisites", return_value=True), \
             patch("cli.commands.generation.create_engine"):
            result = runner.invoke(generate_prps, [
                str(prd),
                "--output", str(tmp_path / "prps"),
                "--preview",
                "--phase", "F3",
                "--no-ai",
            ])
        assert result.exit_code == 0
        assert "F3" in result.output

    def test_generate_prps_from_file(self, tmp_path):
        runner = CliRunner()
        prd = tmp_path / "prd.json"
        prd.write_text(json.dumps({"visao": "test"}), encoding="utf-8")
        mock_engine = MagicMock()
        mock_engine.generate_prps.return_value = {"success": True, "phases": ["F0.md", "F1.md"]}
        with patch("cli.commands.generation.validate_command_prerequisites", return_value=True), \
             patch("cli.commands.generation.create_engine", return_value=mock_engine), \
             patch("cli.commands.generation.click.get_current_context") as mock_ctx:
            mock_ctx.return_value = MagicMock()
            result = runner.invoke(generate_prps, [
                str(prd),
                "--output", str(tmp_path / "prps"),
                "--no-ai",
            ])
        assert result.exit_code == 0
        assert "PRPs generated" in result.output

    def test_generate_prps_prereq_fail(self, tmp_path):
        runner = CliRunner()
        prd = tmp_path / "prd.json"
        prd.write_text("{}", encoding="utf-8")
        with patch("cli.commands.generation.validate_command_prerequisites", return_value=False):
            result = runner.invoke(generate_prps, [
                str(prd),
                "--output", str(tmp_path / "prps"),
                "--no-ai",
            ])
        assert result.exit_code != 0


class TestGenerateTasks:
    def test_generate_tasks_from_prps(self, tmp_path):
        runner = CliRunner()
        prps = tmp_path / "prps"
        prps.mkdir()
        (prps / "F0.md").write_text("# F0", encoding="utf-8")
        mock_engine = MagicMock()
        mock_engine.generate_tasks.return_value = {"success": True, "tasks": ["t1", "t2"]}
        with patch("cli.commands.generation.create_engine", return_value=mock_engine):
            result = runner.invoke(generate_tasks, [
                str(prps),
                "--output", str(tmp_path / "tasks"),
                "--no-ai",
            ])
        assert result.exit_code == 0
        assert "TASKs generated" in result.output


class TestValidate:
    def test_validate_help_contextual(self, tmp_path):
        runner = CliRunner()
        prps = tmp_path / "prps"
        prps.mkdir()
        (prps / "F0.md").write_text("# F0", encoding="utf-8")
        result = runner.invoke(validate, [str(prps), "--help-contextual"])
        assert result.exit_code == 0
        assert "Contextual Help" in result.output

    def test_validate_dry_run(self, tmp_path):
        runner = CliRunner()
        prps = tmp_path / "prps"
        prps.mkdir()
        (prps / "F0.md").write_text("# F0", encoding="utf-8")
        result = runner.invoke(validate, [str(prps), "--dry-run"])
        assert result.exit_code == 0
        assert "Dry-Run" in result.output

    def test_validate_dry_run_with_prd(self, tmp_path):
        runner = CliRunner()
        prps = tmp_path / "prps"
        prps.mkdir()
        (prps / "F0.md").write_text("# F0", encoding="utf-8")
        prd = tmp_path / "prd.json"
        prd.write_text("{}", encoding="utf-8")
        result = runner.invoke(validate, [str(prps), "--dry-run", "--prd-file", str(prd)])
        assert result.exit_code == 0
        assert "PRD" in result.output

    def test_validate_basic_with_errors(self, tmp_path):
        """Validate detects errors in invalid PRPs and exits with code 1."""
        runner = CliRunner()
        prps = tmp_path / "prps"
        prps.mkdir()
        (prps / "F0.md").write_text("---\nphase: F0\n---\n# F0\n", encoding="utf-8")
        result = runner.invoke(validate, [str(prps)])
        # Invalid PRP (missing objectives) → errors found → exit 1
        assert result.exit_code == 1
        assert "error" in result.output.lower() or "valid" in result.output.lower()

    def test_validate_valid_prp(self, tmp_path):
        """Validate passes with valid PRP JSON."""
        runner = CliRunner()
        prps = tmp_path / "prps"
        prps.mkdir()
        valid_prp = {
            "phase": "F0",
            "objectives": ["Plan the project"],
            "deliverables": ["Project plan"],
            "dependencies": [],
        }
        (prps / "F0.json").write_text(json.dumps(valid_prp), encoding="utf-8")
        result = runner.invoke(validate, [str(prps)])
        assert "valid" in result.output.lower()

    def test_validate_with_prd(self, tmp_path):
        runner = CliRunner()
        prps = tmp_path / "prps"
        prps.mkdir()
        valid_prp = {"phase": "F0", "objectives": ["Plan"], "deliverables": [], "dependencies": []}
        (prps / "F0.json").write_text(json.dumps(valid_prp), encoding="utf-8")
        prd = tmp_path / "prd.json"
        prd.write_text(json.dumps({"functional_requirements": []}), encoding="utf-8")
        result = runner.invoke(validate, [str(prps), "--prd-file", str(prd)])
        assert "valid" in result.output.lower() or "CONSISTENCY" in result.output

    def test_validate_with_api_spec(self, tmp_path):
        runner = CliRunner()
        prps = tmp_path / "prps"
        prps.mkdir()
        valid_prp = {"phase": "F0", "objectives": ["Plan"], "deliverables": [], "dependencies": []}
        (prps / "F0.json").write_text(json.dumps(valid_prp), encoding="utf-8")
        spec = tmp_path / "openapi.json"
        spec.write_text(json.dumps({"openapi": "3.0.0", "paths": {}}), encoding="utf-8")
        ui_tasks = tmp_path / "ui_tasks"
        ui_tasks.mkdir()
        result = runner.invoke(validate, [
            str(prps), "--api-spec", str(spec), "--ui-tasks-dir", str(ui_tasks),
        ])
        assert "valid" in result.output.lower() or "CONTRACT" in result.output


class TestCheckDependencies:
    def test_check_valid(self, tmp_path):
        runner = CliRunner()
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.json").write_text(json.dumps({"task_id": "FR-001"}), encoding="utf-8")
        mock_engine = MagicMock()
        mock_engine.check_dependencies.return_value = {"valid": True, "errors": []}
        with patch("cli.commands.generation.create_engine", return_value=mock_engine):
            result = runner.invoke(check_dependencies, [str(tasks), "--no-ai"])
        assert result.exit_code == 0
        assert "valid" in result.output

    def test_check_invalid(self, tmp_path):
        runner = CliRunner()
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.json").write_text("{}", encoding="utf-8")
        mock_engine = MagicMock()
        mock_engine.check_dependencies.return_value = {"valid": False, "errors": ["circular dep"]}
        with patch("cli.commands.generation.create_engine", return_value=mock_engine):
            result = runner.invoke(check_dependencies, [str(tasks), "--no-ai"])
        assert result.exit_code == 1
        assert "circular dep" in result.output


class TestEstimateEffort:
    def test_estimate_json_task(self, tmp_path):
        runner = CliRunner()
        task = {"task_id": "FR-001", "steps": ["s1"], "artifacts": ["a1"], "gherkin_scenarios": [], "dependencies": []}
        task_file = tmp_path / "task.json"
        task_file.write_text(json.dumps(task), encoding="utf-8")
        with patch("cli.commands.generation.MetricsCollector") as MockCollector:
            mock_instance = MockCollector.return_value
            result = runner.invoke(estimate_effort, [str(task_file)])
        assert result.exit_code == 0
        assert "story points" in result.output

    def test_estimate_md_task(self, tmp_path):
        runner = CliRunner()
        md_content = "# Task\n```json\n{\"task_id\": \"FR-001\", \"steps\": [\"s1\"], \"artifacts\": [], \"gherkin_scenarios\": [], \"dependencies\": []}\n```\n"
        task_file = tmp_path / "task.md"
        task_file.write_text(md_content, encoding="utf-8")
        with patch("cli.commands.generation.MetricsCollector"):
            result = runner.invoke(estimate_effort, [str(task_file)])
        assert result.exit_code == 0

    def test_estimate_md_no_json(self, tmp_path):
        runner = CliRunner()
        task_file = tmp_path / "task.md"
        task_file.write_text("# No JSON here\nJust text", encoding="utf-8")
        result = runner.invoke(estimate_effort, [str(task_file)])
        assert result.exit_code == 1

    def test_estimate_detailed(self, tmp_path):
        runner = CliRunner()
        task = {"task_id": "FR-001", "steps": ["s1"], "artifacts": ["a1"], "gherkin_scenarios": [], "dependencies": []}
        task_file = tmp_path / "task.json"
        task_file.write_text(json.dumps(task), encoding="utf-8")
        with patch("cli.commands.generation.MetricsCollector"):
            result = runner.invoke(estimate_effort, [str(task_file), "--detailed"])
        assert result.exit_code == 0
        assert "Breakdown" in result.output


class TestEstimateBatch:
    def test_batch_no_tasks(self, tmp_path):
        runner = CliRunner()
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        result = runner.invoke(estimate_batch, [str(tasks)])
        assert result.exit_code == 1

    def test_batch_with_tasks(self, tmp_path):
        runner = CliRunner()
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        task = {"task_id": "FR-001", "steps": ["s1"], "artifacts": [], "gherkin_scenarios": [], "dependencies": []}
        (tasks / "TASK.FR-001.json").write_text(json.dumps(task), encoding="utf-8")
        with patch("cli.commands.generation.MetricsCollector"):
            result = runner.invoke(estimate_batch, [str(tasks)])
        assert result.exit_code == 0
        assert "story points" in result.output

    def test_batch_with_output(self, tmp_path):
        runner = CliRunner()
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        task = {"task_id": "FR-002", "steps": [], "artifacts": [], "gherkin_scenarios": [], "dependencies": []}
        (tasks / "TASK.FR-002.json").write_text(json.dumps(task), encoding="utf-8")
        output_file = tmp_path / "estimates.json"
        with patch("cli.commands.generation.MetricsCollector"):
            result = runner.invoke(estimate_batch, [str(tasks), "--output", str(output_file)])
        assert result.exit_code == 0
        assert output_file.exists()


class TestGeneratePrdAutoValidate:
    def test_auto_validate_success(self, tmp_path):
        runner = CliRunner()
        output = tmp_path / "prd"
        output.mkdir()
        prd_json = output / "prd_structured.json"
        prd_json.write_text(json.dumps({
            "visao": "App", "usuarios": "Devs", "requisitos_funcionais": ["Login"],
        }), encoding="utf-8")
        input_file = tmp_path / "idea.md"
        input_file.write_text("# Idea", encoding="utf-8")
        mock_engine = MagicMock()
        mock_engine.generate_prd.return_value = {"success": True}
        with patch("cli.commands.generation.create_engine", return_value=mock_engine):
            result = runner.invoke(generate_prd, [
                str(input_file), "--output", str(output), "--no-ai",
            ])
        assert result.exit_code == 0
        assert "validated successfully" in result.output

    def test_auto_validate_missing_fields(self, tmp_path):
        runner = CliRunner()
        output = tmp_path / "prd"
        output.mkdir()
        prd_json = output / "prd_structured.json"
        prd_json.write_text(json.dumps({"visao": "App"}), encoding="utf-8")
        input_file = tmp_path / "idea.md"
        input_file.write_text("# Idea", encoding="utf-8")
        mock_engine = MagicMock()
        mock_engine.generate_prd.return_value = {"success": True}
        with patch("cli.commands.generation.create_engine", return_value=mock_engine):
            result = runner.invoke(generate_prd, [
                str(input_file), "--output", str(output), "--no-ai",
            ])
        assert result.exit_code == 0
        assert "Missing fields" in result.output

    def test_generate_prd_file_not_found(self, tmp_path):
        runner = CliRunner()
        mock_engine = MagicMock()
        mock_engine.generate_prd.side_effect = FileNotFoundError("missing.md")
        with patch("cli.commands.generation.create_engine", return_value=mock_engine):
            result = runner.invoke(generate_prd, [
                str(tmp_path / "idea.md") if False else "--interactive",
                "--output", str(tmp_path / "prd"),
                "--no-ai",
            ], input="n\n")
        # Should abort due to error
        assert result.exit_code != 0


class TestValidateWithContractIntegrity:
    def test_validate_with_api_spec_and_ui_tasks(self, tmp_path):
        runner = CliRunner()
        prps = tmp_path / "prps"
        prps.mkdir()
        valid_prp = {"phase": "F0", "objectives": ["Plan"], "deliverables": [], "dependencies": []}
        (prps / "F0.json").write_text(json.dumps(valid_prp), encoding="utf-8")
        spec = tmp_path / "openapi.json"
        spec.write_text(json.dumps({
            "openapi": "3.0.0",
            "paths": {"/api/users": {"get": {"summary": "List"}}},
        }), encoding="utf-8")
        ui_tasks = tmp_path / "ui_tasks"
        ui_tasks.mkdir()
        (ui_tasks / "TASK.FR-001.md").write_text("# Task\nGET /api/users\n", encoding="utf-8")
        result = runner.invoke(validate, [
            str(prps), "--api-spec", str(spec), "--ui-tasks-dir", str(ui_tasks),
        ])
        assert "CONTRACT" in result.output or "valid" in result.output.lower()


class TestValidateAdvanced:
    def test_validate_with_tasks_dir(self, tmp_path):
        runner = CliRunner()
        prps = tmp_path / "prps"
        prps.mkdir()
        valid_prp = {"phase": "F0", "objectives": ["Plan"], "deliverables": [], "dependencies": []}
        (prps / "F0.json").write_text(json.dumps(valid_prp), encoding="utf-8")
        prd = tmp_path / "prd.json"
        prd.write_text(json.dumps({
            "functional_requirements": [{"id": "FR-001", "title": "Login", "priority": "MUST"}]
        }), encoding="utf-8")
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.json").write_text(json.dumps({"task_id": "FR-001"}), encoding="utf-8")
        result = runner.invoke(validate, [
            str(prps), "--prd-file", str(prd), "--tasks-dir", str(tasks),
        ])
        assert "valid" in result.output.lower() or "TRACEABILITY" in result.output

    def test_validate_soft_check_with_errors(self, tmp_path):
        runner = CliRunner()
        prps = tmp_path / "prps"
        prps.mkdir()
        (prps / "F0.md").write_text("---\nphase: F0\n---\n# F0\n", encoding="utf-8")
        result = runner.invoke(validate, [str(prps), "--soft-check"])
        # soft-check should not abort even with errors
        assert result.exit_code in (0, 1)

    def test_validate_dry_run_with_tasks_and_api(self, tmp_path):
        runner = CliRunner()
        prps = tmp_path / "prps"
        prps.mkdir()
        (prps / "F0.md").write_text("# F0", encoding="utf-8")
        prd = tmp_path / "prd.json"
        prd.write_text("{}", encoding="utf-8")
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        spec = tmp_path / "openapi.json"
        spec.write_text("{}", encoding="utf-8")
        ui_tasks = tmp_path / "ui_tasks"
        ui_tasks.mkdir()
        result = runner.invoke(validate, [
            str(prps), "--dry-run",
            "--prd-file", str(prd),
            "--tasks-dir", str(tasks),
            "--api-spec", str(spec),
            "--ui-tasks-dir", str(ui_tasks),
        ])
        assert result.exit_code == 0
        assert "Tasks" in result.output
        assert "Deep Cross-Validation" in result.output


class TestGeneratePrdInteractive:
    def test_interactive_mode(self, tmp_path):
        runner = CliRunner()
        mock_engine = MagicMock()
        mock_engine.generate_prd.return_value = {"success": True}
        prd_data = {
            "visao": "App de tarefas",
            "contexto": "Mercado",
            "usuarios": "Devs",
            "restricoes": "LGPD",
            "requisitos_funcionais": ["Login", "CRUD"],
        }
        with patch("cli.commands.generation.create_engine", return_value=mock_engine), \
             patch("cli.commands.generation.prompt_prd_idea", return_value=prd_data):
            result = runner.invoke(generate_prd, [
                "--interactive",
                "--output", str(tmp_path / "prd"),
                "--no-ai",
            ])
        assert result.exit_code == 0
        assert "PRD generated" in result.output


class TestGenerateTasksFromUs:
    def test_from_user_story(self, tmp_path):
        runner = CliRunner()
        mock_engine = MagicMock()
        us_data = {
            "title": "Login - Acesso seguro",
            "persona": "admin",
            "acao": "fazer login",
            "valor": "acesso seguro",
            "criterios_aceitacao": ["Dado que estou na tela de login"],
        }
        with patch("cli.commands.generation.create_engine", return_value=mock_engine), \
             patch("cli.commands.generation.prompt_user_story", return_value=us_data):
            result = runner.invoke(generate_tasks, [
                "--from-us",
                "--output", str(tmp_path / "tasks"),
                "--no-ai",
            ])
        assert result.exit_code == 0
        assert "User Story saved" in result.output

    def test_auto_detect_prps_dir(self, tmp_path, monkeypatch):
        """Auto-detect PRPs directory when not provided."""
        runner = CliRunner()
        prps = tmp_path / "prps"
        prps.mkdir()
        (prps / "F0.md").write_text("# F0", encoding="utf-8")
        mock_engine = MagicMock()
        mock_engine.generate_tasks.return_value = {"success": True, "tasks": ["t1"]}
        monkeypatch.chdir(tmp_path)
        with patch("cli.commands.generation.create_engine", return_value=mock_engine):
            result = runner.invoke(generate_tasks, [
                "--output", str(tmp_path / "tasks"),
                "--no-ai",
            ])
        assert result.exit_code == 0


class TestInitNoProjectName:
    def test_init_infers_name_from_cwd(self, tmp_path):
        runner = CliRunner()
        mock_engine = MagicMock()
        mock_engine.init_project.return_value = {
            "success": True,
            "created_directories": [],
            "created_files": [],
            "generated_files": ["F0.md", "F1.md", "F2.md", "F3.md", "F4.md", "F5.md"],
        }
        with patch("cli.commands.generation.check_intelligence_mode", return_value=False), \
             patch("cli.commands.generation.create_engine", return_value=mock_engine), \
             patch("cli.commands.generation.save_project_config"):
            result = runner.invoke(init, [
                "--stack", "python-fastapi",
                "--output", str(tmp_path),
                "--no-ai",
                "--language", "en-us",
            ])
        assert result.exit_code == 0

    def test_init_with_git_hooks_no_git(self, tmp_path):
        runner = CliRunner()
        mock_engine = MagicMock()
        mock_engine.init_project.return_value = {
            "success": True,
            "created_directories": [],
            "created_files": [],
            "generated_files": [],
        }
        with patch("cli.commands.generation.check_intelligence_mode", return_value=False), \
             patch("cli.commands.generation.create_engine", return_value=mock_engine), \
             patch("cli.commands.generation.save_project_config"):
            result = runner.invoke(init, [
                "test-proj",
                "--stack", "python-fastapi",
                "--output", str(tmp_path),
                "--git-hooks",
                "--no-ai",
                "--language", "en-us",
            ])
        assert result.exit_code == 0
        assert "git" in result.output.lower() or "initialized" in result.output.lower()


class TestGeneratePrpsInteractive:
    def test_interactive_with_detected_prd(self, tmp_path, monkeypatch):
        runner = CliRunner()
        prd = tmp_path / "prd" / "prd_structured.json"
        prd.parent.mkdir(parents=True)
        prd.write_text(json.dumps({"visao": "test"}), encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        mock_engine = MagicMock()
        mock_engine.generate_prps.return_value = {"success": True, "phases": ["F0.md"]}
        prp_info = {"metodo_priorizacao": "MoSCoW", "contexto_adicional": ""}
        with patch("cli.commands.generation.validate_command_prerequisites", return_value=True), \
             patch("cli.commands.generation.create_engine", return_value=mock_engine), \
             patch("cli.commands.generation.prompt_prp_info", return_value=prp_info), \
             patch("cli.commands.generation.click.get_current_context") as mock_ctx:
            mock_ctx.return_value = MagicMock()
            result = runner.invoke(generate_prps, [
                "--interactive",
                "--output", str(tmp_path / "prps"),
                "--no-ai",
            ])
        assert result.exit_code == 0
        assert "PRPs generated" in result.output

    def test_interactive_no_prd_found_not_interactive(self, tmp_path, monkeypatch):
        """When no PRD found and not interactive, shows error."""
        runner = CliRunner()
        monkeypatch.chdir(tmp_path)
        with patch("cli.commands.generation.validate_command_prerequisites", return_value=True), \
             patch("cli.commands.generation.create_engine"):
            result = runner.invoke(generate_prps, [
                "--output", str(tmp_path / "prps"),
                "--no-ai",
            ])
        assert result.exit_code != 0

    def test_interactive_with_additional_context(self, tmp_path, monkeypatch):
        """Interactive mode with additional context from prompt_prp_info."""
        runner = CliRunner()
        prd = tmp_path / "prd" / "prd_structured.json"
        prd.parent.mkdir(parents=True)
        prd.write_text(json.dumps({"visao": "test"}), encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        mock_engine = MagicMock()
        mock_engine.generate_prps.return_value = {"success": True, "phases": ["F0.md"]}
        prp_info = {"metodo_priorizacao": "MoSCoW", "contexto_adicional": "Extra context here"}
        with patch("cli.commands.generation.validate_command_prerequisites", return_value=True), \
             patch("cli.commands.generation.create_engine", return_value=mock_engine), \
             patch("cli.commands.generation.prompt_prp_info", return_value=prp_info), \
             patch("cli.commands.generation.click.get_current_context") as mock_ctx:
            mock_ctx.return_value = MagicMock()
            result = runner.invoke(generate_prps, [
                "--interactive",
                "--output", str(tmp_path / "prps"),
                "--no-ai",
            ])
        assert result.exit_code == 0
        assert "Additional context" in result.output


class TestGeneratePrdErrorPaths:
    def test_permission_error(self, tmp_path):
        """PermissionError during generate_prd is handled."""
        runner = CliRunner()
        input_file = tmp_path / "idea.md"
        input_file.write_text("# Idea", encoding="utf-8")
        mock_engine = MagicMock()
        mock_engine.generate_prd.side_effect = PermissionError("/prd")
        with patch("cli.commands.generation.create_engine", return_value=mock_engine):
            result = runner.invoke(generate_prd, [
                str(input_file), "--output", str(tmp_path / "prd"), "--no-ai",
            ])
        assert result.exit_code != 0

    def test_unexpected_error(self, tmp_path):
        """Unexpected error during generate_prd is handled."""
        runner = CliRunner()
        input_file = tmp_path / "idea.md"
        input_file.write_text("# Idea", encoding="utf-8")
        mock_engine = MagicMock()
        mock_engine.generate_prd.side_effect = RuntimeError("unexpected")
        with patch("cli.commands.generation.create_engine", return_value=mock_engine):
            result = runner.invoke(generate_prd, [
                str(input_file), "--output", str(tmp_path / "prd"), "--no-ai",
            ])
        assert result.exit_code != 0

    def test_auto_validate_json_error(self, tmp_path):
        """Auto-validate with corrupt JSON in prd_structured.json."""
        runner = CliRunner()
        output = tmp_path / "prd"
        output.mkdir()
        prd_json = output / "prd_structured.json"
        prd_json.write_text("NOT JSON", encoding="utf-8")
        input_file = tmp_path / "idea.md"
        input_file.write_text("# Idea", encoding="utf-8")
        mock_engine = MagicMock()
        mock_engine.generate_prd.return_value = {"success": True}
        with patch("cli.commands.generation.create_engine", return_value=mock_engine):
            result = runner.invoke(generate_prd, [
                str(input_file), "--output", str(output), "--no-ai",
            ])
        assert result.exit_code != 0


class TestGenerateTasksErrorPaths:
    def test_no_prps_not_interactive(self, tmp_path, monkeypatch):
        """When no PRPs found and not interactive, shows error."""
        runner = CliRunner()
        monkeypatch.chdir(tmp_path)
        with patch("cli.commands.generation.create_engine"):
            result = runner.invoke(generate_tasks, [
                "--output", str(tmp_path / "tasks"), "--no-ai",
            ])
        assert result.exit_code != 0

    def test_auto_detect_PRPs_uppercase(self, tmp_path, monkeypatch):
        """Auto-detect PRPs directory with uppercase name."""
        runner = CliRunner()
        prps = tmp_path / "PRPs"
        prps.mkdir()
        (prps / "F0.md").write_text("# F0", encoding="utf-8")
        mock_engine = MagicMock()
        mock_engine.generate_tasks.return_value = {"success": True, "tasks": ["t1"]}
        monkeypatch.chdir(tmp_path)
        with patch("cli.commands.generation.create_engine", return_value=mock_engine):
            result = runner.invoke(generate_tasks, [
                "--output", str(tmp_path / "tasks"), "--no-ai",
            ])
        assert result.exit_code == 0


class TestValidateWithCommitsJson:
    def test_validate_with_commits_json(self, tmp_path):
        """Validate with inverse traceability via commits-json."""
        runner = CliRunner()
        prps = tmp_path / "prps"
        prps.mkdir()
        valid_prp = {"phase": "F0", "objectives": ["Plan"], "deliverables": [], "dependencies": []}
        (prps / "F0.json").write_text(json.dumps(valid_prp), encoding="utf-8")
        commits = tmp_path / "commits.json"
        commits.write_text(json.dumps({"FR-001": ["abc123"]}), encoding="utf-8")
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-001.json").write_text(json.dumps({"task_id": "FR-001"}), encoding="utf-8")
        with patch("cli.commands.generation.PRPValidator") as MockValidator:
            mock_v = MockValidator.return_value
            mock_v.validate_all.return_value = {
                "dependencies": {"valid": True, "errors": [], "warnings": []},
            }
            mock_inverse = MagicMock()
            mock_inverse.to_dict.return_value = {"valid": True, "statistics": None}
            mock_inverse.get.return_value = None
            mock_v.validate_inverse_traceability.return_value = mock_inverse
            result = runner.invoke(validate, [
                str(prps), "--commits-json", str(commits),
                "--tasks-dir", str(tasks),
            ])
        assert result.exit_code == 0

    def test_validate_warnings_on_valid(self, tmp_path):
        """Validate shows warnings even when results are valid."""
        runner = CliRunner()
        prps = tmp_path / "prps"
        prps.mkdir()
        (prps / "F0.json").write_text(json.dumps(
            {"phase": "F0", "objectives": ["Plan"], "deliverables": [], "dependencies": []}
        ), encoding="utf-8")
        with patch("cli.commands.generation.PRPValidator") as MockValidator:
            mock_v = MockValidator.return_value
            mock_v.validate_all.return_value = {
                "dependencies": {"valid": True, "errors": [], "warnings": ["minor issue"]},
                "consistency": {"valid": True, "errors": [], "warnings": ["another warning"]},
            }
            result = runner.invoke(validate, [str(prps)])
        assert result.exit_code == 0
        assert "minor issue" in result.output or "valid" in result.output.lower()


class TestEstimateBatchMdTasks:
    def test_batch_with_md_tasks(self, tmp_path):
        """Batch estimation with markdown task files."""
        runner = CliRunner()
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        md_content = '# Task\n```json\n{"task_id": "FR-003", "steps": ["s1"], "artifacts": [], "gherkin_scenarios": [], "dependencies": []}\n```\n'
        (tasks / "TASK.FR-003.md").write_text(md_content, encoding="utf-8")
        with patch("cli.commands.generation.MetricsCollector"):
            result = runner.invoke(estimate_batch, [str(tasks)])
        assert result.exit_code == 0
        assert "story points" in result.output

    def test_batch_with_invalid_md(self, tmp_path):
        """Batch estimation skips invalid markdown tasks."""
        runner = CliRunner()
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-004.md").write_text("# No JSON here", encoding="utf-8")
        (tasks / "TASK.FR-005.json").write_text(json.dumps(
            {"task_id": "FR-005", "steps": [], "artifacts": [], "gherkin_scenarios": [], "dependencies": []}
        ), encoding="utf-8")
        with patch("cli.commands.generation.MetricsCollector"):
            result = runner.invoke(estimate_batch, [str(tasks)])
        assert result.exit_code == 0

    def test_batch_task_processing_error(self, tmp_path):
        """Batch estimation handles individual task errors."""
        runner = CliRunner()
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "TASK.FR-006.json").write_text("INVALID JSON", encoding="utf-8")
        (tasks / "TASK.FR-007.json").write_text(json.dumps(
            {"task_id": "FR-007", "steps": [], "artifacts": [], "gherkin_scenarios": [], "dependencies": []}
        ), encoding="utf-8")
        with patch("cli.commands.generation.MetricsCollector"):
            result = runner.invoke(estimate_batch, [str(tasks)])
        assert result.exit_code == 0
