"""AI governance helpers for dependency validation and embedding preferences."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from core.cache import DEFAULT_EMBEDDING_MODEL, TRANSFORMERS_AVAILABLE
from core.config_service import ProjectConfigService
from core.logging_service import LOGGING_SERVICE


class AIGovernanceService:
    """Centralizes decisions around transformer availability and embedding models."""

    def __init__(
        self,
        config_service: ProjectConfigService,
        *,
        available_models: dict[str, str] | None = None,
        transformers_available_provider: Callable[[], bool] | None = None,
    ) -> None:
        self.config_service = config_service
        self.available_models = available_models or {
            "all-minilm-l6-v2": "all-MiniLM-L6-v2",
            "bge-small-en-v1.5": "BAAI/bge-small-en-v1.5",
            "embeddinggemma-300m": "google/embeddinggemma-300m",
        }
        self.default_model = DEFAULT_EMBEDDING_MODEL
        self.policy_version_env_var = "AI_GOVERNANCE_POLICY_VERSION"
        self._transformers_provider = transformers_available_provider or (
            lambda: TRANSFORMERS_AVAILABLE
        )  # pragma: no cover - fallback
        self.logger = LOGGING_SERVICE.get_logger(__name__)

    def normalize_embedding_model(self, alias: str | None) -> str | None:
        """Map friendly aliases to canonical identifiers."""
        if not alias:
            return alias
        normalized = alias.strip()
        if not normalized:
            return None
        lookup = self.available_models.get(normalized.lower())
        return lookup or normalized

    def dependencies_ready(self) -> bool:
        """Return whether transformer dependencies are importable."""
        try:
            return bool(self._transformers_provider())
        except Exception:  # pragma: no cover - defensive
            self.logger.exception("Transformer availability provider failed")
            return False

    def resolve_preferences(
        self,
        *,
        enable_ai: bool | None,
        embedding_model: str | None,
        context_hint: Path | None = None,
    ) -> tuple[bool | None, str, Path | None, dict]:
        """
        Determine hybrid intelligence mode and embedding model.

        Args:
            enable_ai: Explicit CLI override for transformer usage.
            embedding_model: Requested embedding model identifier.
            context_hint: Optional directory to resolve project config.

        Returns:
            Tuple (preference_flag, resolved_model, project_root, config_dict).
            preference_flag may be None when no explicit preference was found.
        """
        context_hint = context_hint or Path.cwd()
        project_root, config = self.config_service.load_project_config(context_hint)
        config = config or {}
        policy_version_env = os.getenv(self.policy_version_env_var)
        if project_root and policy_version_env:
            if config.get("policy_version") != policy_version_env:
                self.config_service.save_project_config(project_root, {"policy_version": policy_version_env})
                config["policy_version"] = policy_version_env

        stored_pref = config.get("use_transformers")
        resolved_pref = enable_ai if enable_ai is not None else stored_pref
        if isinstance(resolved_pref, str):
            resolved_pref = resolved_pref.lower() in {"1", "true", "yes"}

        resolved_model = (
            self.normalize_embedding_model(embedding_model)
            or self.normalize_embedding_model(config.get("embedding_model"))
            or self.default_model
        )

        self.logger.debug(
            "AI preferences resolved",
            extra={
                "enable_ai": enable_ai,
                "stored_pref": stored_pref,
                "resolved_pref": resolved_pref,
                "embedding_model": resolved_model,
                "project_root": str(project_root) if project_root else None,
            },
        )

        return resolved_pref, resolved_model, project_root, config

    def requires_installation(self, enable_ai: bool | None) -> bool:
        """
        Determine whether dependency installation should be triggered.

        Args:
            enable_ai: Explicit CLI override.

        Returns:
            True when transformers were requested but are unavailable locally.
        """
        return enable_ai is True and not self.dependencies_ready()


__all__ = ["AIGovernanceService"]
