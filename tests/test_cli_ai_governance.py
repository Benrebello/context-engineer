"""Tests for `ce ai-governance` commands."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from jsonschema import Draft7Validator

from cli.main import cli

AIGOV_SCHEMA = {
    "type": "object",
    "required": [
        "project_dir",
        "config_detected",
        "stored",
        "overrides",
        "resolved",
        "meta",
        "roi",
        "hooks",
    ],
    "properties": {
        "project_dir": {"type": "string"},
        "config_detected": {"type": ["string", "null"]},
        "stored": {
            "type": "object",
            "required": ["use_transformers", "embedding_model"],
            "properties": {
                "use_transformers": {"type": ["boolean", "null"]},
                "embedding_model": {"type": ["string", "null"]},
            },
        },
        "overrides": {
            "type": "object",
            "required": ["cli_enable_ai", "cli_embedding_model"],
            "properties": {
                "cli_enable_ai": {"type": ["boolean", "null"]},
                "cli_embedding_model": {"type": ["string", "null"]},
            },
        },
        "resolved": {
            "type": "object",
            "required": [
                "dependencies_ready",
                "use_transformers",
                "embedding_model",
                "requires_installation",
                "auto_install_attempted",
                "auto_install_policy",
            ],
            "properties": {
                "dependencies_ready": {"type": "boolean"},
                "use_transformers": {"type": ["boolean", "null"]},
                "embedding_model": {"type": ["string", "null"]},
                "requires_installation": {"type": "boolean"},
                "auto_install_attempted": {"type": "boolean"},
                "auto_install_success": {"type": "boolean"},
                "auto_install_policy": {"type": "string"},
            },
        },
        "meta": {
            "type": "object",
            "required": ["generated_at", "policy_version"],
            "properties": {
                "generated_at": {"type": "string"},
                "policy_version": {"type": ["string", "null"]},
            },
        },
        "roi": {"type": ["object", "null"]},
        "hooks": {"type": "object"},
    },
}


class StubGovernanceService:
    """Stub implementation to drive CLI output deterministically."""

    def __init__(
        self,
        *,
        use_transformers: bool = True,
        embedding: str = "corp-mini",
        dependencies_ready: bool = True,
        requires_installation: bool = False,
    ) -> None:
        self.calls = {"resolve_preferences": []}
        self.use_transformers = use_transformers
        self.embedding = embedding
        self.dependencies_ready_flag = dependencies_ready
        self.requires_install_flag = requires_installation

    def resolve_preferences(self, *, enable_ai, embedding_model, context_hint):
        self.calls["resolve_preferences"].append(
            {"enable_ai": enable_ai, "embedding_model": embedding_model, "context_hint": context_hint}
        )
        resolved_model = embedding_model or self.embedding
        return self.use_transformers, resolved_model, Path(context_hint), {
            "use_transformers": self.use_transformers,
            "embedding_model": self.embedding,
        }

    def dependencies_ready(self):
        return self.dependencies_ready_flag

    def requires_installation(self, enable_ai):
        return self.requires_install_flag


def _patch_service(monkeypatch, **kwargs):
    stub = StubGovernanceService(**kwargs)
    monkeypatch.setattr("cli.commands.ai_governance.AI_GOVERNANCE_SERVICE", stub, raising=False)
    return stub


def test_ai_governance_status_table(monkeypatch, tmp_path):
    stub = _patch_service(monkeypatch)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "ai-governance",
            "status",
            "--project-dir",
            str(tmp_path),
            "--embedding-model",
            "all-minilm-l6-v2",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "AI Governance Status" in result.output
    assert stub.calls["resolve_preferences"], "resolve_preferences should be called"


def test_ai_governance_status_json(monkeypatch, tmp_path):
    stub = _patch_service(monkeypatch)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["ai-governance", "status", "--project-dir", str(tmp_path), "--format", "json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    Draft7Validator(AIGOV_SCHEMA).validate(payload)
    meta = payload.pop("meta")
    assert "generated_at" in meta
    assert meta["generated_at"]
    assert meta["policy_version"] is None
    roi_payload = payload["roi"]
    hooks_payload = payload["hooks"]
    expected = {
        "project_dir": str(tmp_path),
        "config_detected": str(tmp_path),
        "stored": {"use_transformers": True, "embedding_model": "corp-mini"},
        "overrides": {"cli_enable_ai": None, "cli_embedding_model": None},
        "resolved": {
            "dependencies_ready": True,
            "use_transformers": True,
            "embedding_model": "corp-mini",
            "requires_installation": False,
            "auto_install_attempted": False,
            "auto_install_success": False,
            "auto_install_policy": "prompt",
        },
        "roi": roi_payload,
        "hooks": hooks_payload,
    }
    assert payload == expected
    assert expected["roi"] is None
    assert expected["hooks"] == {
        "pre_push": {"installed": False, "mode": None},
        "pre_commit": {"installed": False, "mode": None},
    }
    assert stub.calls["resolve_preferences"], "resolve_preferences should be called"


def test_ai_governance_status_html(monkeypatch, tmp_path):
    output_file = tmp_path / "status.html"
    _patch_service(monkeypatch)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "ai-governance",
            "status",
            "--project-dir",
            str(tmp_path),
            "--format",
            "html",
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output_file.exists()
    html = output_file.read_text(encoding="utf-8")
    assert "<th>Resolved embedding model</th><td>corp-mini</td>" in html
    assert f"<th>Project directory</th><td>{tmp_path}</td>" in html


def test_ai_governance_status_auto_install(monkeypatch, tmp_path):
    stub = _patch_service(
        monkeypatch,
        dependencies_ready=False,
        requires_installation=True,
    )

    def fake_install(exit_after_success=True):
        stub.dependencies_ready_flag = True
        stub.requires_install_flag = False
        return True

    monkeypatch.setattr(
        "cli.commands.ai_governance._attempt_transformer_install",
        fake_install,
        raising=False,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "ai-governance",
            "status",
            "--project-dir",
            str(tmp_path),
            "--format",
            "json",
            "--auto-install",
            "always",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["resolved"]["auto_install_attempted"] is True
    assert payload["resolved"]["auto_install_policy"] == "always"
    assert payload["resolved"]["auto_install_success"] is True
    assert payload["resolved"]["requires_installation"] is False
