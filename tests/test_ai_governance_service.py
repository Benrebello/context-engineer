"""Tests covering AI governance logic and logging configuration helpers."""

import logging
from pathlib import Path

from cli.shared import configure_logging
from core.ai_governance_service import AIGovernanceService


class DummyConfigService:
    """Lightweight stub for ProjectConfigService behavior."""

    def __init__(self, project_root: Path, config: dict):
        self.project_root = project_root
        self.config = config

    def load_project_config(self, *_args, **_kwargs):
        """Return the pre-seeded configuration without touching disk."""
        return self.project_root, self.config


def test_resolve_preferences_prioritizes_cli_override(tmp_path):
    config_service = DummyConfigService(tmp_path, {"use_transformers": False})
    service = AIGovernanceService(
        config_service,
        available_models={"embeddinggemma-300m": "google/embeddinggemma-300m"},
        transformers_available_provider=lambda: True,
    )

    resolved_pref, model, project_root, _ = service.resolve_preferences(
        enable_ai=True,
        embedding_model="embeddinggemma-300m",
        context_hint=tmp_path,
    )

    assert resolved_pref is True
    assert model == "google/embeddinggemma-300m"
    assert project_root == tmp_path


def test_resolve_preferences_uses_defaults_when_config_missing(tmp_path):
    config_service = DummyConfigService(tmp_path, {})
    service = AIGovernanceService(
        config_service,
        available_models={},
        transformers_available_provider=lambda: False,
    )

    resolved_pref, model, project_root, _ = service.resolve_preferences(
        enable_ai=None,
        embedding_model=None,
        context_hint=tmp_path,
    )

    assert resolved_pref is None
    assert model == service.default_model
    assert project_root == tmp_path


def test_dependencies_ready_handles_provider_errors(tmp_path, caplog):
    def failing_provider():
        raise RuntimeError("boom")

    config_service = DummyConfigService(tmp_path, {})
    service = AIGovernanceService(
        config_service,
        transformers_available_provider=failing_provider,
    )

    with caplog.at_level(logging.ERROR):
        ready = service.dependencies_ready()

    assert ready is False
    assert "Transformer availability provider failed" in caplog.text


def test_requires_installation_flags_missing_dependencies(tmp_path):
    config_service = DummyConfigService(tmp_path, {})
    service = AIGovernanceService(
        config_service,
        transformers_available_provider=lambda: False,
    )

    assert service.requires_installation(True) is True
    assert service.requires_installation(False) is False


class FakeLoggingService:
    """Captures configured log levels for assertions."""

    def __init__(self):
        self.levels = []

    def configure(self, level):
        self.levels.append(level)


def test_configure_logging_verbose_forces_debug(monkeypatch):
    fake_logger = FakeLoggingService()
    monkeypatch.setattr("cli.shared.LOGGING_SERVICE", fake_logger)

    configure_logging(verbose=True)

    assert fake_logger.levels == [logging.DEBUG]


def test_configure_logging_quiet_sets_warning(monkeypatch):
    fake_logger = FakeLoggingService()
    monkeypatch.setattr("cli.shared.LOGGING_SERVICE", fake_logger)

    configure_logging(quiet=True)

    assert fake_logger.levels == [logging.WARNING]


def test_configure_logging_explicit_level_wins(monkeypatch):
    fake_logger = FakeLoggingService()
    monkeypatch.setattr("cli.shared.LOGGING_SERVICE", fake_logger)

    configure_logging(level="ERROR", verbose=True, quiet=True)

    assert fake_logger.levels == ["ERROR"]
