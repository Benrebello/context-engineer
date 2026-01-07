"""Example showing how to extend AIGovernanceService with corporate policies."""

from __future__ import annotations

import os
from pathlib import Path

from core.ai_governance_service import AIGovernanceService
from core.config_service import ProjectConfigService

CORPORATE_MODELS = {
    "corp-mini": "contoso/corp-mini-embeddings",
    "corp-large": "contoso/corp-large-embeddings",
    "corp-legal": "contoso/legal-specialist-embeddings",
}


def corp_policy_provider() -> bool:
    """Enforce centralized policy (e.g., allow only in approved environments)."""
    return os.getenv("ALLOW_TRANSFORMERS", "true").lower() == "true"


def load_service() -> AIGovernanceService:
    """Instantiate governance service with corporate extensions."""
    config_service = ProjectConfigService(".ce-config.json")
    return AIGovernanceService(
        config_service=config_service,
        available_models=CORPORATE_MODELS,
        transformers_available_provider=corp_policy_provider,
    )


def describe_policy() -> None:
    """Prints resolved policy and preferences for the current directory."""
    service = load_service()
    use_ai, model, project_root, _ = service.resolve_preferences(
        enable_ai=None,
        embedding_model=None,
        context_hint=Path.cwd(),
    )
    print("Corporate policy allows transformers:", service.dependencies_ready())
    print("Resolved use_transformers:", use_ai)
    print("Resolved embedding model:", model)
    if project_root:
        print("Project root:", project_root)


if __name__ == "__main__":
    describe_policy()
