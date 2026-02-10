"""Health check and governance diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

import click

from cli.shared import (
    AI_GOVERNANCE_SERVICE,
    AI_PROFILE_PRESETS,
    CONFIG_SERVICE,
    ai_profile_option,
    apply_ai_profile,
    detect_git_hook_status,
    get_roi_snapshot,
)


class DoctorReportBuilder:
    """Aggregates diagnostics for ce doctor."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.project_root: Path | None = None
        self.config: dict = {}
        self.refresh_config()
        self.summary: dict[str, dict | None] = {
            "config": None,
            "ai_governance": None,
            "roi": None,
            "git_hooks": None,
        }

    def refresh_config(self) -> None:
        project_root, config = CONFIG_SERVICE.load_project_config(self.project_dir)
        self.project_root = project_root
        self.config = config or {}

    def add_config_section(self) -> None:
        config_info = {
            "project_root": str(self.project_root) if self.project_root else None,
            "use_transformers": self.config.get("use_transformers"),
            "embedding_model": self.config.get("embedding_model"),
            "ai_profile": self.config.get("ai_profile"),
            "policy_version": self.config.get("policy_version"),
        }
        self.summary["config"] = config_info

    def add_ai_governance_section(self, enable_ai, embedding_model) -> None:
        resolved_pref, resolved_model, project_root, config = AI_GOVERNANCE_SERVICE.resolve_preferences(
            enable_ai=enable_ai,
            embedding_model=embedding_model,
            context_hint=self.project_dir,
        )
        if project_root:
            self.project_root = project_root
        if config:
            self.config = config

        dependencies_ready = AI_GOVERNANCE_SERVICE.dependencies_ready()
        requested_flag = enable_ai if enable_ai is not None else resolved_pref
        requires_install = AI_GOVERNANCE_SERVICE.requires_installation(requested_flag)
        stored_config = config or {}
        summary = {
            "project_dir": str(self.project_dir),
            "config_detected": str(self.project_root) if self.project_root else None,
            "stored": {
                "use_transformers": stored_config.get("use_transformers"),
                "embedding_model": stored_config.get("embedding_model"),
            },
            "overrides": {
                "cli_enable_ai": enable_ai,
                "cli_embedding_model": embedding_model,
            },
            "resolved": {
                "dependencies_ready": dependencies_ready,
                "use_transformers": resolved_pref,
                "embedding_model": resolved_model,
                "requires_installation": requires_install,
                "auto_install_attempted": False,
                "auto_install_success": False,
                "auto_install_policy": stored_config.get("auto_install_policy", "prompt"),
            },
            "meta": {
                "generated_at": None,
                "policy_version": stored_config.get("policy_version"),
            },
        }
        self.summary["ai_governance"] = summary

    def add_roi_section(self) -> None:
        roi = get_roi_snapshot(self.project_root)
        self.summary["roi"] = roi

    def add_git_hooks_section(self) -> None:
        hooks = detect_git_hook_status(self.project_root)
        self.summary["git_hooks"] = hooks

    def build(self) -> dict[str, dict | None]:
        return self.summary


@click.command(help="Run AI, hooks, and metrics health-check for quick diagnostics.")
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    help="Project base directory.",
)
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json"]),
    help="Output format (table, json).",
)
@click.option(
    "--apply-profile",
    is_flag=True,
    default=False,
    help="Apply the selected --ai-profile preset to .ce-config.json before diagnostics.",
)
@ai_profile_option("AI preset to apply or just inspect.")
@click.option(
    "--embedding-model",
    help="Override the embedding model for diagnostics.",
)
@click.option(
    "--ai/--no-ai",
    "enable_ai",
    default=None,
    help="Force AI mode for diagnosis.",
)
def doctor(project_dir, output_format, apply_profile, ai_profile, embedding_model, enable_ai):
    """Run a full project diagnostic."""
    project_path = Path(project_dir).resolve()
    builder = DoctorReportBuilder(project_path)

    if ai_profile:
        preset = AI_PROFILE_PRESETS.get(ai_profile.lower())
        if not preset:
            raise click.ClickException(f"Unknown AI profile: {ai_profile}")
        if apply_profile:
            if not builder.project_root:
                raise click.ClickException("Project has no .ce-config.json to apply profiles.")
            payload = apply_ai_profile(builder.project_root, ai_profile)
            builder.refresh_config()
            click.echo(f"[OK] AI profile '{ai_profile}' applied:")
            click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            click.echo(f"[INFO] Preview for AI profile '{ai_profile}':")
            click.echo(json.dumps(preset, indent=2, ensure_ascii=False))

    builder.add_config_section()
    builder.add_ai_governance_section(enable_ai, embedding_model)
    builder.add_roi_section()
    builder.add_git_hooks_section()
    report = builder.build()

    if output_format == "json":
        click.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return

    _render_table(report)


def _render_table(report: dict) -> None:
    click.echo("\nContext Engineer Doctor Report")
    click.echo("=" * 70)
    config = report.get("config") or {}
    click.echo("Configuration")
    click.echo("-" * 70)
    click.echo(f"Project root           : {config.get('project_root') or 'not found'}")
    click.echo(f"Use transformers       : {config.get('use_transformers')}")
    click.echo(f"Configured embedding   : {config.get('embedding_model')}")
    click.echo(f"AI profile             : {config.get('ai_profile')}")
    click.echo(f"Policy version         : {config.get('policy_version')}")

    governance = report.get("ai_governance") or {}
    resolved = governance.get("resolved") or {}
    click.echo("\nAI Governance")
    click.echo("-" * 70)
    click.echo(f"Dependencies ready     : {resolved.get('dependencies_ready')}")
    click.echo(f"Use transformers       : {resolved.get('use_transformers')}")
    click.echo(f"Embedding model        : {resolved.get('embedding_model')}")
    click.echo(f"Requires installation  : {resolved.get('requires_installation')}")
    click.echo(f"Auto-install policy    : {resolved.get('auto_install_policy')}")

    roi = report.get("roi")
    click.echo("\nROI (Context Pruning)")
    click.echo("-" * 70)
    if roi:
        click.echo(f"Tokens saved           : {roi.get('tokens_saved')}")
        click.echo(f"Tokens used            : {roi.get('tokens_used')}")
        click.echo(f"Savings %              : {roi.get('savings_percentage', 0.0):.2f}%")
        click.echo(f"Cost saved (USD)       : ${roi.get('estimated_cost_saved_usd', 0.0):.2f}")
        click.echo(f"Events                 : {roi.get('context_pruning_events')}")
    else:
        click.echo("No ROI events recorded yet.")

    hooks = report.get("git_hooks") or {}
    click.echo("\nGit Hooks")
    click.echo("-" * 70)
    pre_push = hooks.get("pre_push", {})
    click.echo(
        f"pre-push               : {'installed' if pre_push.get('installed') else 'missing'}"
        f" ({pre_push.get('mode') or 'n/a'})"
    )
    pre_commit = hooks.get("pre_commit", {})
    click.echo(
        f"pre-commit             : {'installed' if pre_commit.get('installed') else 'missing'}"
        f" ({pre_commit.get('mode') or 'n/a'})"
    )
    click.echo("=" * 70 + "\n")


__all__ = ["doctor"]
