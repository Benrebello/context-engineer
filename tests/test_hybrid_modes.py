from pathlib import Path

from click.testing import CliRunner

from cli.main import cli
from core.cache import CodePattern, IntelligenceCache


def _create_dummy_engine(monkeypatch, instances):
    class DummyEngine:
        def __init__(self, *args, **kwargs):
            instances.append(kwargs)

        def init_project(self, template, project_name, stack, output_dir, **_):
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            return {
                "created_directories": ["src"],
                "created_files": [str(Path(output_dir) / "README.md")],
                "generated_files": [],
            }

    monkeypatch.setattr("cli.main.ContextEngine", DummyEngine)


def test_intelligence_cache_levenshtein_mode(tmp_path, monkeypatch):
    monkeypatch.setattr("core.cache.TRANSFORMERS_AVAILABLE", False, raising=False)
    cache = IntelligenceCache(tmp_path, use_transformers=True)

    context = {"stack": "python-fastapi", "description": "Simple greeting"}
    pattern = CodePattern(
        pattern_id="pattern-1",
        code="print('hello world')",
        metadata=context,
        context_hash=cache._hash_context(context),
    )
    cache.store_pattern(pattern)

    results = cache.search_similar(context)

    assert results
    assert results[0].pattern_id == "pattern-1"


def test_cli_init_declines_ai(monkeypatch):
    monkeypatch.setattr("cli.main.TRANSFORMERS_AVAILABLE", False, raising=False)
    instances = []
    _create_dummy_engine(monkeypatch, instances)

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["init", "proj", "--output", "./workspace"],
            input="n\n",
        )

    assert result.exit_code == 0
    assert "modo 'levenshtein'" in result.output.lower()
    assert instances, "Engine was not instantiated"
    assert instances[0]["use_transformers"] is False


def test_cli_init_accepts_ai_installs(monkeypatch):
    monkeypatch.setattr("cli.main.TRANSFORMERS_AVAILABLE", False, raising=False)
    calls = {}

    def fake_install(cmd):
        calls["cmd"] = cmd

    monkeypatch.setattr("cli.main.subprocess.check_call", fake_install, raising=False)

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["init", "proj", "--output", "./workspace"],
            input="y\n",
        )

    assert result.exit_code == 0
    assert "sentence-transformers" in calls["cmd"]
    assert "numpy" in calls["cmd"]
    assert "execute o comando novamente" in result.output.lower()
