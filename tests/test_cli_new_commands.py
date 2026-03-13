import json
from pathlib import Path

from click.testing import CliRunner

from cli.commands.doctor import DoctorReportBuilder
from cli.main import cli
from core.metrics import MetricsCollector


def test_autopilot_runs_full_flow(monkeypatch):
    calls = {"init": 0, "generate_prd": 0, "generate_prps": 0, "generate_tasks": 0, "validate": 0}

    def _touch(path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")

    def fake_init(**kwargs):
        calls["init"] += 1
        output = Path(kwargs["output"])
        output.mkdir(parents=True, exist_ok=True)
        _touch(output / ".ce-config.json")

    def fake_generate_prd(**kwargs):
        calls["generate_prd"] += 1
        output = Path(kwargs["output"])
        output.mkdir(parents=True, exist_ok=True)
        _touch(output / "prd_structured.json")

    def fake_generate_prps(**kwargs):
        calls["generate_prps"] += 1
        output = Path(kwargs["output"])
        output.mkdir(parents=True, exist_ok=True)

    def fake_generate_tasks(**kwargs):
        calls["generate_tasks"] += 1
        output = Path(kwargs["output"])
        output.mkdir(parents=True, exist_ok=True)

    def fake_validate(**kwargs):
        calls["validate"] += 1

    monkeypatch.setattr("cli.main.init", fake_init, raising=False)
    monkeypatch.setattr("cli.main.generate_prd", fake_generate_prd, raising=False)
    monkeypatch.setattr("cli.main.generate_prps", fake_generate_prps, raising=False)
    monkeypatch.setattr("cli.main.generate_tasks", fake_generate_tasks, raising=False)
    monkeypatch.setattr("cli.main.validate", fake_validate, raising=False)

    runner = CliRunner()
    with runner.isolated_filesystem():
        idea_file = Path("idea.md")
        idea_file.write_text("Nova feature com IA", encoding="utf-8")

        result = runner.invoke(
            cli,
            [
                "autopilot",
                "--project-dir",
                "./workspace",
                "--idea-file",
                str(idea_file),
            ],
        )

    assert result.exit_code == 0, result.output
    assert calls == dict.fromkeys(calls, 1), f"Fluxo incompleto: {calls}"


def test_marketplace_commands(tmp_path):
    runner = CliRunner()

    list_result = runner.invoke(cli, ["marketplace", "list"])
    assert list_result.exit_code == 0
    assert "pattern_api_gateway" in list_result.output

    install_result = runner.invoke(
        cli,
        [
            "marketplace",
            "install",
            "pattern_api_gateway",
            "--project-dir",
            str(tmp_path),
        ],
    )

    assert install_result.exit_code == 0
    expected_file = tmp_path / "marketplace" / "patterns" / "restful-crud.md"
    assert expected_file.exists()


def test_ci_bootstrap_generates_workflow(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "ci-bootstrap",
            "--project-dir",
            str(tmp_path),
            "--workflow-file",
            "workflow.yml",
        ],
    )

    assert result.exit_code == 0, result.output
    generated = tmp_path / "workflow.yml"
    assert generated.exists()
    assert "Context Engineer CI Bootstrap" in generated.read_text(encoding="utf-8")


def test_ai_status_reports_configuration(monkeypatch, tmp_path):
    def fake_load_project_config(_):
        return tmp_path, {"use_transformers": False, "embedding_model": "all-minilm-l6-v2"}

    class DummyCache:
        use_transformers = True
        selected_model = "bge-small-en-v1.5"

    class DummyEngine:
        def __init__(self):
            self.cache = DummyCache()

    monkeypatch.setattr("cli.main.load_project_config", fake_load_project_config, raising=False)
    monkeypatch.setattr("cli.main.create_engine", lambda **_: DummyEngine(), raising=False)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "ai-status",
            "--project-dir",
            str(tmp_path),
            "--embedding-model",
            "bge-small-en-v1.5",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Modo resolvido" in result.output
    assert "bge-small-en-v1.5" in result.output


def test_cli_accepts_verbose_flag(monkeypatch):
    captured = {}

    def fake_configure_logging(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("cli.main.configure_logging", fake_configure_logging, raising=False)

    runner = CliRunner()
    result = runner.invoke(cli, ["--verbose", "marketplace", "list"])

    assert result.exit_code == 0
    assert captured == {"verbose": True, "quiet": False, "level": None}


def test_cli_accepts_quiet_flag(monkeypatch):
    captured = {}

    def fake_configure_logging(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("cli.main.configure_logging", fake_configure_logging, raising=False)

    runner = CliRunner()
    result = runner.invoke(cli, ["--quiet", "marketplace", "list"])

    assert result.exit_code == 0
    assert captured == {"verbose": False, "quiet": True, "level": None}


def test_cli_accepts_explicit_log_level(monkeypatch):
    captured = {}

    def fake_configure_logging(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("cli.main.configure_logging", fake_configure_logging, raising=False)

    runner = CliRunner()
    result = runner.invoke(cli, ["--log-level", "ERROR", "marketplace", "list"])

    assert result.exit_code == 0
    assert captured == {"verbose": False, "quiet": False, "level": "ERROR"}


def test_ide_sync_copies_prompts(tmp_path):
    runner = CliRunner()
    source_dir = tmp_path / "seed"
    source_dir.mkdir()
    (source_dir / "prompts").mkdir()
    (source_dir / "prompts" / "Agente_PRD_360.md").write_text("# prompt", encoding="utf-8")
    (source_dir / "workflows").mkdir()
    (source_dir / "workflows" / "flow.json").write_text("{}", encoding="utf-8")

    project_dir = tmp_path / "project"
    project_dir.mkdir()

    result = runner.invoke(
        cli,
        [
            "ide",
            "sync",
            "--project-dir",
            str(project_dir),
            "--source-dir",
            str(source_dir),
            "--target-dir",
            ".ide-rules",
            "--ide-name",
            "windsurf",
        ],
    )

    assert result.exit_code == 0, result.output
    target_dir = project_dir / ".ide-rules"
    assert (target_dir / "prompts" / "Agente_PRD_360.md").exists()
    assert (target_dir / "workflows" / "flow.json").exists()


def test_doctor_outputs_json(tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / ".ce-config.json").write_text(
        json.dumps({"use_transformers": False, "embedding_model": "all-minilm-l6-v2"}), encoding="utf-8"
    )
    metrics = MetricsCollector(project_dir / ".cache" / "metrics")
    metrics.record_project_start(project_dir.name)
    metrics.record_context_pruning(project_dir.name, tokens_saved=1200, cost_saved=0.036, tokens_used=4000)
    hooks_dir = project_dir / ".git" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / "pre-push").write_text("# Soft-Gate", encoding="utf-8")

    result = runner.invoke(
        cli,
        [
            "doctor",
            "--project-dir",
            str(project_dir),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["config"]["embedding_model"] == "all-minilm-l6-v2"
    assert payload["git_hooks"]["pre_push"]["installed"] is True


def test_doctor_applies_ai_profile(tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / ".ce-config.json").write_text("{}", encoding="utf-8")

    result = runner.invoke(
        cli,
        [
            "doctor",
            "--project-dir",
            str(project_dir),
            "--ai-profile",
            "balanced",
            "--apply-profile",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    config = json.loads((project_dir / ".ce-config.json").read_text(encoding="utf-8"))
    assert config["ai_profile"] == "balanced"
    assert config["use_transformers"] is True


def test_doctor_report_builder_handles_missing_config(tmp_path, monkeypatch):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    builder = DoctorReportBuilder(project_dir)

    # Force resolve_preferences return controlled values
    monkeypatch.setattr(
        "cli.commands.doctor.AI_GOVERNANCE_SERVICE.resolve_preferences",
        lambda **kwargs: (True, "all-MiniLM-L6-v2", project_dir, {"use_transformers": True}),
    )
    monkeypatch.setattr(
        "cli.commands.doctor.AI_GOVERNANCE_SERVICE.dependencies_ready",
        lambda: True,
    )
    monkeypatch.setattr(
        "cli.commands.doctor.AI_GOVERNANCE_SERVICE.requires_installation",
        lambda flag: False,
    )
    builder.add_ai_governance_section(enable_ai=None, embedding_model=None)
    summary = builder.build()
    assert summary["ai_governance"]["resolved"]["use_transformers"] is True
