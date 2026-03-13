"""Tests for CLI shared helpers covering installation prompts and utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cli import shared


def _resolver_with_transformers_unavailable(name: str, default):
    if name == "TRANSFORMERS_AVAILABLE":
        return False
    return default


def _resolver_with_transformers_available(name: str, default):
    if name == "TRANSFORMERS_AVAILABLE":
        return True
    return default


# -- check_intelligence_mode --

def test_check_intelligence_mode_forces_install_when_ai_flag(monkeypatch):
    monkeypatch.setattr(shared, "_resolve_cli_main_attr", _resolver_with_transformers_unavailable, raising=False)

    installs = {"count": 0}

    def fake_install():
        installs["count"] += 1

    monkeypatch.setattr(shared, "_attempt_transformer_install", fake_install)

    result = shared.check_intelligence_mode(enable_override=True)

    assert installs["count"] == 1
    assert result is False


def test_check_intelligence_mode_prompt_install(monkeypatch):
    monkeypatch.setattr(shared, "_resolve_cli_main_attr", _resolver_with_transformers_unavailable, raising=False)

    installs = {"count": 0}

    def fake_install():
        installs["count"] += 1

    monkeypatch.setattr(shared, "_attempt_transformer_install", fake_install)
    monkeypatch.setattr(shared.click, "confirm", lambda *_, **__: True)

    result = shared.check_intelligence_mode(enable_override=None)

    assert installs["count"] == 1
    assert result is False


def test_check_intelligence_mode_no_ai(monkeypatch):
    result = shared.check_intelligence_mode(enable_override=False)
    assert result is False


def test_check_intelligence_mode_available_none(monkeypatch):
    monkeypatch.setattr(shared, "_resolve_cli_main_attr", _resolver_with_transformers_available, raising=False)
    result = shared.check_intelligence_mode(enable_override=None)
    assert result is True


def test_check_intelligence_mode_available_explicit(monkeypatch):
    monkeypatch.setattr(shared, "_resolve_cli_main_attr", _resolver_with_transformers_available, raising=False)
    result = shared.check_intelligence_mode(enable_override=True)
    assert result is True


def test_check_intelligence_mode_decline_install(monkeypatch):
    monkeypatch.setattr(shared, "_resolve_cli_main_attr", _resolver_with_transformers_unavailable, raising=False)
    monkeypatch.setattr(shared.click, "confirm", lambda *_, **__: False)
    result = shared.check_intelligence_mode(enable_override=None)
    assert result is False


# -- load_project_config / save_project_config --

def test_load_project_config_found(tmp_path):
    config = {"stack": "python-fastapi", "language": "pt-br"}
    (tmp_path / shared.CONFIG_FILENAME).write_text(json.dumps(config), encoding="utf-8")
    root, data = shared.load_project_config(tmp_path)
    assert root == tmp_path
    assert data["stack"] == "python-fastapi"


def test_load_project_config_not_found(tmp_path):
    root, data = shared.load_project_config(tmp_path)
    assert root is None
    assert data == {}


def test_save_project_config_new(tmp_path):
    shared.save_project_config(tmp_path, {"stack": "node-react"})
    config_path = tmp_path / shared.CONFIG_FILENAME
    assert config_path.exists()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert data["stack"] == "node-react"


def test_save_project_config_merge(tmp_path):
    (tmp_path / shared.CONFIG_FILENAME).write_text(json.dumps({"language": "pt-br"}), encoding="utf-8")
    shared.save_project_config(tmp_path, {"stack": "go-gin"})
    data = json.loads((tmp_path / shared.CONFIG_FILENAME).read_text(encoding="utf-8"))
    assert data["language"] == "pt-br"
    assert data["stack"] == "go-gin"


# -- _normalize_dir / _find_project_root --

def test_normalize_dir_directory(tmp_path):
    result = shared._normalize_dir(tmp_path)
    assert result == tmp_path.resolve()


def test_normalize_dir_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("x", encoding="utf-8")
    result = shared._normalize_dir(f)
    assert result == tmp_path.resolve()


def test_find_project_root_found(tmp_path):
    (tmp_path / shared.CONFIG_FILENAME).write_text("{}", encoding="utf-8")
    result = shared._find_project_root(tmp_path)
    assert result == tmp_path


def test_find_project_root_not_found(tmp_path):
    sub = tmp_path / "deep" / "nested"
    sub.mkdir(parents=True)
    result = shared._find_project_root(sub)
    assert result is None


# -- echo helpers --

def test_echo_success(capsys):
    shared.echo_success("done")
    # Should not raise


def test_echo_error(capsys):
    shared.echo_error("fail")


def test_echo_warning(capsys):
    shared.echo_warning("warn")


def test_echo_info(capsys):
    shared.echo_info("info")


def test_echo_step(capsys):
    shared.echo_step(1, 5, "Processing")


# -- configure_logging --

def test_configure_logging_default():
    shared.configure_logging()


def test_configure_logging_verbose():
    shared.configure_logging(verbose=True)


def test_configure_logging_quiet():
    shared.configure_logging(quiet=True)


def test_configure_logging_explicit_level():
    shared.configure_logging(level="DEBUG")


# -- get_roi_snapshot --

def test_get_roi_snapshot_no_root():
    result = shared.get_roi_snapshot(None)
    assert result is None


def test_get_roi_snapshot_no_metrics_dir(tmp_path):
    result = shared.get_roi_snapshot(tmp_path)
    assert result is None


def test_get_roi_snapshot_with_metrics(tmp_path):
    metrics_dir = tmp_path / ".cache" / "metrics"
    metrics_dir.mkdir(parents=True)
    from core.metrics import MetricsCollector
    collector = MetricsCollector(metrics_dir)
    collector.record_project_start(tmp_path.name)
    result = shared.get_roi_snapshot(tmp_path)
    assert result is not None
    assert "project_name" in result


# -- detect_git_hook_status --

def test_detect_git_hook_status_no_root():
    result = shared.detect_git_hook_status(None)
    assert result["pre_push"]["installed"] is False


def test_detect_git_hook_status_no_git(tmp_path):
    result = shared.detect_git_hook_status(tmp_path)
    assert result["pre_push"]["installed"] is False


def test_detect_git_hook_status_with_hooks(tmp_path):
    hooks_dir = tmp_path / ".git" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / "pre-push").write_text("#!/bin/sh\n# Soft-Gate\necho test", encoding="utf-8")
    (hooks_dir / "pre-commit").write_text("#!/bin/sh\necho test", encoding="utf-8")
    result = shared.detect_git_hook_status(tmp_path)
    assert result["pre_push"]["installed"] is True
    assert result["pre_push"]["mode"] == "soft"
    assert result["pre_commit"]["installed"] is True


def test_detect_git_hook_status_hard_gate(tmp_path):
    hooks_dir = tmp_path / ".git" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / "pre-push").write_text("#!/bin/sh\n# Hard-Gate\nexit 1", encoding="utf-8")
    result = shared.detect_git_hook_status(tmp_path)
    assert result["pre_push"]["mode"] == "hard"


def test_detect_git_hook_status_custom_hook(tmp_path):
    hooks_dir = tmp_path / ".git" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / "pre-push").write_text("#!/bin/sh\necho custom", encoding="utf-8")
    result = shared.detect_git_hook_status(tmp_path)
    assert result["pre_push"]["mode"] == "custom"


# -- get_project_language --

def test_get_project_language_default(tmp_path):
    lang = shared.get_project_language(tmp_path)
    assert isinstance(lang, str)


# -- validate_command_prerequisites --

def test_validate_command_prerequisites_unknown(tmp_path):
    result = shared.validate_command_prerequisites("unknown-cmd", tmp_path)
    assert result is True


def test_validate_command_prerequisites_validate_no_prd(tmp_path):
    result = shared.validate_command_prerequisites("validate", tmp_path)
    assert result is False


def test_validate_command_prerequisites_validate_with_prd(tmp_path):
    (tmp_path / "PRD.md").write_text("# PRD", encoding="utf-8")
    result = shared.validate_command_prerequisites("validate", tmp_path)
    assert result is True


# -- create_engine --

def test_create_engine():
    engine = shared.create_engine(use_transformers=False)
    assert engine is not None


# -- apply_ai_profile --

def test_apply_ai_profile_local(tmp_path):
    result = shared.apply_ai_profile(tmp_path, "local")
    assert result["ai_profile"] == "local"
    assert result["use_transformers"] is False


def test_apply_ai_profile_balanced(tmp_path):
    result = shared.apply_ai_profile(tmp_path, "balanced")
    assert result["use_transformers"] is True


def test_apply_ai_profile_corporate(tmp_path):
    result = shared.apply_ai_profile(tmp_path, "corporate")
    assert "policy_version" in result


def test_apply_ai_profile_unknown(tmp_path):
    with pytest.raises(ValueError, match="Unknown AI profile"):
        shared.apply_ai_profile(tmp_path, "nonexistent")
