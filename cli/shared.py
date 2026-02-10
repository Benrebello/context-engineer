"""Shared services and helpers for the Context Engineer CLI."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess

# Ensure core modules are importable when running CLI directly
import sys
from pathlib import Path
from typing import Any

import click

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ai_governance_service import AIGovernanceService
from core.autopilot_service import AutopilotService
from core.cache import TRANSFORMERS_AVAILABLE
from core.config_service import ProjectConfigService
from core.engine import ContextEngine
from core.git_service import GitHookManager, GitService
from core.i18n import get_i18n
from core.logging_service import LOGGING_SERVICE
from core.marketplace_service import MarketplaceService
from core.metrics import MetricsCollector
from core.project_status_service import ProjectStatusService
from core.prompt_service import PromptService

REPO_ROOT = Path(__file__).parent.parent
CONFIG_FILENAME = ".ce-config.json"
AVAILABLE_EMBEDDING_MODELS = {
    "all-minilm-l6-v2": "all-MiniLM-L6-v2",
    "bge-small-en-v1.5": "BAAI/bge-small-en-v1.5",
    "embeddinggemma-300m": "google/embeddinggemma-300m",
}
AI_PROFILE_PRESETS = {
    "local": {
        "description": "Lightweight mode for laptops/offline work",
        "use_transformers": False,
        "embedding_model": "all-MiniLM-L6-v2",
        "auto_install_policy": "never",
    },
    "balanced": {
        "description": "Default hybrid mode with semantic search enabled",
        "use_transformers": True,
        "embedding_model": "all-MiniLM-L6-v2",
        "auto_install_policy": "prompt",
    },
    "corporate": {
        "description": "Strict corporate policy with curated model and no auto-install",
        "use_transformers": True,
        "embedding_model": "bge-small-en-v1.5",
        "auto_install_policy": "never",
        "policy_version": "corporate-1.0",
    },
}
MARKETPLACE_CATALOG = REPO_ROOT / "docs" / "marketplace_catalog.json"

PROMPT_SERVICE = PromptService()
CONFIG_SERVICE = ProjectConfigService(CONFIG_FILENAME)
STATUS_SERVICE = ProjectStatusService(PROMPT_SERVICE, CONFIG_SERVICE)
MARKETPLACE_SERVICE = MarketplaceService(repo_root=REPO_ROOT)
AUTOPILOT_SERVICE = AutopilotService(CONFIG_FILENAME)
AI_GOVERNANCE_SERVICE = AIGovernanceService(CONFIG_SERVICE, available_models=AVAILABLE_EMBEDDING_MODELS)


def _resolve_cli_main_attr(name: str, default: Any) -> Any:
    """Retrieve attribute from cli.main when available to preserve monkeypatch compatibility."""
    try:
        from cli import main as cli_main

        return getattr(cli_main, name)
    except (ImportError, AttributeError):
        return default


def normalize_embedding_model(alias: str | None) -> str | None:
    """Normalize embedding model identifiers, accepting either alias or full name."""
    return AI_GOVERNANCE_SERVICE.normalize_embedding_model(alias)


def embedding_model_option(
    help_text: str = "Define o modelo de embedding para modo IA (ex.: all-minilm-l6-v2)",
) -> Any:
    """Reusable click option for selecting embedding models per comando."""
    choices = sorted(set(list(AVAILABLE_EMBEDDING_MODELS.keys()) + list(AVAILABLE_EMBEDDING_MODELS.values())))
    return click.option(
        "--embedding-model",
        type=click.Choice(choices),
        help=help_text,
    )


def hybrid_ai_option(help_text: str = "Define modo IA ou leve apenas para este comando") -> Any:
    """Reusable click option for toggling hybrid intelligence per command."""
    return click.option(
        "--ai/--no-ai",
        "enable_ai",
        default=None,
        help=help_text,
    )


def _normalize_dir(path: Path) -> Path:
    """Ensure we always operate on directory paths."""
    resolved = path.resolve()
    return resolved if resolved.is_dir() else resolved.parent


def _find_project_root(start_dir: Path, config_filename: str = CONFIG_FILENAME) -> Path | None:
    """Search upwards for the project configuration file."""
    current = _normalize_dir(start_dir)
    for candidate in [current, *current.parents]:
        if (candidate / config_filename).exists():
            return candidate
    return None


def load_project_config(start_dir: Path | None = None) -> tuple[Path | None, dict]:
    """Load project configuration starting from given directory upwards."""
    start_dir = start_dir or Path.cwd()
    project_root = _find_project_root(start_dir)
    if not project_root:
        return None, {}

    config_path = project_root / CONFIG_FILENAME
    try:
        with open(config_path, encoding="utf-8") as config_file:
            return project_root, json.load(config_file)
    except Exception:
        return project_root, {}


def save_project_config(project_dir: Path, overrides: dict) -> None:
    """Persist project configuration merging with existing data."""
    project_dir = project_dir.resolve()
    config_path = project_dir / CONFIG_FILENAME
    existing: dict = {}
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as config_file:
                existing = json.load(config_file)
        except Exception:
            existing = {}

    existing.update(overrides)
    with open(config_path, "w", encoding="utf-8") as config_file:
        json.dump(existing, config_file, indent=2, ensure_ascii=False)


def resolve_ai_preference(enable_ai: bool | None, context_hint: Path | None = None) -> tuple[bool, Path | None]:
    """
    Decide whether transformers should be enabled for this command execution.

    Preference priority:
        1. Command flag (--ai/--no-ai)
        2. Stored project preference (.ce-config.json)
        3. Interactive prompt (fallback)
    """
    resolved_pref, _, project_root, _ = AI_GOVERNANCE_SERVICE.resolve_preferences(
        enable_ai=enable_ai, embedding_model=None, context_hint=context_hint
    )
    use_transformers = check_intelligence_mode(enable_override=resolved_pref)
    return use_transformers, project_root


def _attempt_transformer_install(exit_after_success: bool = True) -> bool:
    """Install transformer dependencies using uv (if available) or pip."""
    subprocess_module = _resolve_cli_main_attr("subprocess", subprocess)
    uv_path = shutil.which("uv")
    if uv_path:
        install_cmd = [uv_path, "pip", "install"]
        tool_name = "uv"
    else:
        install_cmd = ["pip", "install"]
        tool_name = "pip"

    click.echo(f"Instalando dependencias de IA via {tool_name}...")
    try:
        subprocess_module.check_call(install_cmd + ["sentence-transformers", "numpy"])
        click.secho(
            "Sucesso! Por favor, execute o comando novamente para ativar a IA.",
            fg="green",
        )
        if exit_after_success:
            raise click.exceptions.Exit()
        return True
    except Exception as exc:  # pragma: no cover - interactive path
        click.secho(
            f"Falha na instalacao: {exc}. Mantendo modo Levenshtein.",
            fg="red",
        )
        return False


def check_intelligence_mode(enable_override: bool | None = None) -> bool:
    """Assess transformer availability, honoring user overrides and guiding install."""
    transformers_available = _resolve_cli_main_attr("TRANSFORMERS_AVAILABLE", TRANSFORMERS_AVAILABLE)
    if enable_override is False:
        click.secho(
            "\n[Context Engineer] Modo IA desativado manualmente (--no-ai).",
            fg="yellow",
        )
        return False

    if transformers_available:
        if enable_override is None:
            click.secho(
                "\n[Context Engineer] Modo Inteligência Híbrida disponível. IA vetorial ativada.",
                fg="green",
            )
        else:
            click.secho(
                "\n[Context Engineer] IA vetorial ativada conforme flag --ai.",
                fg="green",
            )
        return True

    click.secho(
        "\n[Context Engineer] Busca Semântica via IA não detectada.",
        fg="yellow",
    )
    click.echo("O sistema usará o modo 'Levenshtein' (leve) por padrão.")

    if enable_override is True:
        click.echo("Dependências de IA são obrigatórias para --ai.")
        _attempt_transformer_install()
        return False

    install = click.confirm(
        "Deseja baixar o suporte a Transformers (IA) para entender sinônimos? (~500MB)",
        default=False,
    )

    if install:
        _attempt_transformer_install()
        return False

    return False


def create_engine(
    use_transformers: bool | None = None,
    context_hint: Path | None = None,
    embedding_model: str | None = None,
) -> ContextEngine:
    """
    Instantiate ContextEngine honoring the hybrid intelligence preference.

    Resolution order:
        1. Explicit parameter (use_transformers)
        2. Project config (.ce-config.json)
        3. Global availability (TRANSFORMERS_AVAILABLE)
    """
    context_engine_cls = _resolve_cli_main_attr("ContextEngine", ContextEngine)
    resolved_use, resolved_model, _, _ = AI_GOVERNANCE_SERVICE.resolve_preferences(
        enable_ai=use_transformers,
        embedding_model=embedding_model,
        context_hint=context_hint,
    )
    return context_engine_cls(use_transformers=resolved_use, embedding_model=resolved_model)


def apply_ai_profile(project_dir: Path, profile_name: str) -> dict:
    """Persist AI profile defaults into the project configuration."""
    normalized = profile_name.lower()
    preset = AI_PROFILE_PRESETS.get(normalized)
    if not preset:
        raise ValueError(f"Unknown AI profile '{profile_name}'")
    payload = {
        "ai_profile": normalized,
        "use_transformers": preset["use_transformers"],
        "embedding_model": preset["embedding_model"],
        "auto_install_policy": preset.get("auto_install_policy"),
    }
    if preset.get("policy_version"):
        payload["policy_version"] = preset["policy_version"]
    CONFIG_SERVICE.save_project_config(project_dir, payload)
    return payload


def ai_profile_option(help_text: str = "Aplica preset corporativo de IA para este diagnóstico."):
    """Click option helper for AI profile selection."""
    return click.option(
        "--ai-profile",
        type=click.Choice(sorted(AI_PROFILE_PRESETS.keys())),
        help=help_text,
    )


def configure_logging(*, verbose: bool = False, quiet: bool = False, level: str | int | None = None):
    """
    Configure logging level for CLI execution.

    Args:
        verbose: When True, sets DEBUG level regardless of other flags.
        quiet: When True, reduces output to WARNING (ignored if verbose).
        level: Optional explicit level override (string or numeric).
    """
    resolved_level: str | int | None = level
    if resolved_level is None:
        if verbose:
            resolved_level = logging.DEBUG
        elif quiet:
            resolved_level = logging.WARNING
        else:
            resolved_level = logging.INFO
    LOGGING_SERVICE.configure(resolved_level)


def _generate_git_hooks(project_dir: Path, project_name: str, soft_gate: bool = True):
    """Generate git hooks for the project."""
    hook_manager = GitHookManager(project_dir)
    hook_manager.generate_hooks(project_name, soft_gate=soft_gate)
    mode_text = "Soft-Gate (consultivo)" if soft_gate else "Hard-Gate (bloqueante)"
    click.echo(" Hooks gerados:")
    click.echo(" • pre-commit: Validação rápida antes do commit")
    click.echo(f" • pre-push: Validação completa antes do push ({mode_text})")


def build_commit_mapping(
    project_dir: Path,
    since: str | None = None,
    include_uncommitted: bool = True,
) -> dict:
    """Build Task → commits mapping using git history and task file references."""
    git_service = GitService(project_dir)
    return git_service.build_commit_mapping(since=since, include_uncommitted=include_uncommitted)


def get_roi_snapshot(project_root: Path | None, project_name: str | None = None) -> dict | None:
    """Return ROI metrics from cache when available."""
    if not project_root:
        return None
    metrics_dir = project_root / ".cache" / "metrics"
    if not metrics_dir.exists():
        return None
    collector = MetricsCollector(metrics_dir)
    project_ref = project_name or project_root.name
    try:
        snapshot = collector.get_roi_metrics(project_ref)
        snapshot["project_name"] = project_ref
        return snapshot
    except Exception:
        return None


def detect_git_hook_status(project_root: Path | None) -> dict[str, dict[str, str | None]]:
    """Inspect git hooks installation status and mode."""
    status: dict[str, dict[str, Any]] = {
        "pre_push": {"installed": False, "mode": None},
        "pre_commit": {"installed": False, "mode": None},
    }
    if not project_root:
        return status
    hooks_dir = project_root / ".git" / "hooks"
    if not hooks_dir.exists():
        return status
    pre_push = hooks_dir / "pre-push"
    pre_commit = hooks_dir / "pre-commit"
    if pre_push.exists():
        status["pre_push"]["installed"] = True
        try:
            content = pre_push.read_text(encoding="utf-8")
            if "Soft-Gate" in content:
                status["pre_push"]["mode"] = "soft"
            elif "Hard-Gate" in content:
                status["pre_push"]["mode"] = "hard"
            else:
                status["pre_push"]["mode"] = "custom"
        except Exception:
            status["pre_push"]["mode"] = "unknown"
    if pre_commit.exists():
        status["pre_commit"]["installed"] = True
        status["pre_commit"]["mode"] = "syntax"
    return status


def echo_success(message: str) -> None:
    """Display success message with consistent formatting."""
    click.secho(f"✓ {message}", fg="green", bold=True)


def echo_error(message: str) -> None:
    """Display error message with consistent formatting."""
    click.secho(f"✗ {message}", fg="red", bold=True)


def echo_warning(message: str) -> None:
    """Display warning message with consistent formatting."""
    click.secho(f"⚠ {message}", fg="yellow")


def echo_info(message: str) -> None:
    """Display info message with consistent formatting."""
    click.secho(f"ℹ {message}", fg="blue")


def echo_step(step_number: int, total_steps: int, description: str) -> None:
    """Display step progress with consistent formatting."""
    click.secho(f"[{step_number}/{total_steps}] {description}", fg="cyan", bold=True)


def get_project_language(project_dir: Path | None = None) -> str:
    """Get language preference from project configuration.

    Args:
        project_dir: Project directory. If None, uses current directory.

    Returns:
        Language code (en-us or pt-br)
    """
    if project_dir is None:
        project_dir = Path.cwd()

    i18n = get_i18n(project_dir=project_dir)
    return i18n.language


def validate_command_prerequisites(command_name: str, project_dir: Path) -> bool:
    """Validate prerequisites before running command to prevent mid-execution failures.

    Args:
        command_name: Name of the command to validate
        project_dir: Project directory path

    Returns:
        True if all prerequisites are met, False otherwise
    """
    from core.project_analyzer import ProjectAnalyzer

    i18n = get_i18n(project_dir=project_dir)

    prerequisites = {
        "generate-prps": {
            "checks": ["has_prd"],
            "keys": {"has_prd": "cmd.generate_prps.prereq_failed"},
        },
        "generate-tasks": {
            "checks": ["has_prps"],
            "keys": {"has_prps": "cmd.generate_tasks.prereq_failed"},
        },
        "validate": {"checks": ["has_prd"], "keys": {"has_prd": "cmd.validate.prereq_failed"}},
    }

    if command_name not in prerequisites:
        return True

    try:
        analyzer = ProjectAnalyzer(project_dir)
        state = analyzer.analyze_project_state()

        prereq_config = prerequisites[command_name]
        for check in prereq_config["checks"]:
            if not state.get(check, False):
                echo_error(i18n.t(prereq_config["keys"][check]))
                echo_info(i18n.t("cmd.validate.tip"))
                return False

        return True
    except Exception as exc:
        echo_warning(i18n.t("error.prereq_validation_failed", error=str(exc)))
        return True


__all__ = [
    "AUTOPILOT_SERVICE",
    "AI_PROFILE_PRESETS",
    "AVAILABLE_EMBEDDING_MODELS",
    "CONFIG_FILENAME",
    "CONFIG_SERVICE",
    "REPO_ROOT",
    "MARKETPLACE_CATALOG",
    "MARKETPLACE_SERVICE",
    "PROMPT_SERVICE",
    "STATUS_SERVICE",
    "_generate_git_hooks",
    "build_commit_mapping",
    "check_intelligence_mode",
    "create_engine",
    "embedding_model_option",
    "hybrid_ai_option",
    "load_project_config",
    "normalize_embedding_model",
    "resolve_ai_preference",
    "save_project_config",
    "apply_ai_profile",
    "ai_profile_option",
    "echo_success",
    "echo_error",
    "echo_warning",
    "echo_info",
    "echo_step",
    "get_project_language",
    "validate_command_prerequisites",
]
