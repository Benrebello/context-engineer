"""Tests for CLI shared helpers covering installation prompts."""

from __future__ import annotations

from cli import shared


def _resolver_with_transformers_unavailable(name: str, default):
    if name == "TRANSFORMERS_AVAILABLE":
        return False
    return default


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
