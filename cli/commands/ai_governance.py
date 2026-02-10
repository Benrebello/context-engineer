"""AI governance CLI tools."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import click

from cli.shared import (
    AI_GOVERNANCE_SERVICE,
    _attempt_transformer_install,
    detect_git_hook_status,
    embedding_model_option,
    get_roi_snapshot,
    hybrid_ai_option,
)
from core.logging_service import LOGGING_SERVICE

LOGGER = LOGGING_SERVICE.get_logger(__name__)


@click.group(name="ai-governance", help="Tools to inspect AI governance policies.")
def ai_governance() -> None:
    """Namespace for AI governance commands."""


def build_ai_governance_summary(
    project_dir: Path | str,
    *,
    auto_install_mode: str = "prompt",
    enable_ai: bool | None,
    embedding_model: str | None,
    allow_auto_install: bool = True,
) -> dict:
    """Build governance summary without emitting output."""
    project_path = Path(project_dir).resolve()
    resolved_pref, resolved_model, project_root, config = AI_GOVERNANCE_SERVICE.resolve_preferences(
        enable_ai=enable_ai,
        embedding_model=embedding_model,
        context_hint=project_path,
    )
    dependencies_ready = AI_GOVERNANCE_SERVICE.dependencies_ready()
    policy_mode = auto_install_mode.lower()
    requested_flag = enable_ai if enable_ai is not None else resolved_pref
    requires_install = AI_GOVERNANCE_SERVICE.requires_installation(requested_flag)
    attempted_auto_install = False
    auto_install_success = False

    if policy_mode == "always" and requires_install and allow_auto_install:
        attempted_auto_install = True
        auto_install_success = _attempt_transformer_install(exit_after_success=False)
        dependencies_ready = AI_GOVERNANCE_SERVICE.dependencies_ready()
        requires_install = not auto_install_success
        if not auto_install_success:
            click.secho(
                "[Governance] Auto-install policy 'always' failed. Please review logs or run manually.",
                fg="red",
            )
            LOGGER.warning(
                "AI auto-install failed",
                extra={
                    "project_dir": str(project_path),
                    "auto_install_policy": policy_mode,
                    "dependencies_ready": dependencies_ready,
                },
            )

    stored_config = config or {}
    summary = {
        "project_dir": str(project_path),
        "config_detected": str(project_root) if project_root else None,
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
            "auto_install_attempted": attempted_auto_install,
            "auto_install_success": auto_install_success,
            "auto_install_policy": policy_mode,
        },
        "meta": {
            "generated_at": datetime.now(UTC).isoformat(),
            "policy_version": stored_config.get("policy_version"),
        },
        "roi": get_roi_snapshot(project_root),
        "hooks": detect_git_hook_status(project_root),
    }
    return summary


@ai_governance.command("status", help="Show resolved preferences and active policies.")
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    help="Directory used to locate .ce-config.json.",
)
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json", "html"]),
    help="Output format (table, json, html).",
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False),
    help="Destination HTML file (used only when --format=html).",
)
@click.option(
    "--auto-install",
    "auto_install_mode",
    type=click.Choice(["never", "prompt", "always"], case_sensitive=False),
    default="prompt",
    help="Policy for automatic installation (never, prompt, always).",
)
@hybrid_ai_option("Force lightweight AI mode only for diagnostics.")
@embedding_model_option("Override the embedding model for this diagnostic run.")
def ai_governance_status(project_dir, output_format, output, auto_install_mode, enable_ai, embedding_model):
    """Diagnose the AI policy applied to the current context."""
    project_path = Path(project_dir).resolve()
    summary = build_ai_governance_summary(
        project_path,
        auto_install_mode=auto_install_mode,
        enable_ai=enable_ai,
        embedding_model=embedding_model,
        allow_auto_install=True,
    )

    if output_format == "json":
        click.echo(json.dumps(summary, indent=2, ensure_ascii=False))
        return

    if output_format == "html":
        html_content = _render_html_report(summary)
        target_path = (
            Path(output).resolve()
            if output
            else project_path / f"ai_governance_status_{project_path.name or 'report'}.html"
        )
        target_path.write_text(html_content, encoding="utf-8")
        click.echo(f"[OK] Report saved to {target_path}")
        return

    _render_table(summary)


def _render_table(summary: dict) -> None:
    """Emit tabular/console view for governance summary."""
    click.echo("\n" + "=" * 70)
    click.echo("AI Governance Status")
    click.echo("=" * 70)
    click.echo(f"Project dir       : {summary['project_dir']}")
    click.echo(f"Config detected   : {summary['config_detected'] or 'not found'}")
    click.echo(
        f"Stored preference : {summary['stored']['use_transformers'] if summary['stored']['use_transformers'] is not None else 'not set'}"
    )
    click.echo(f"Stored model      : {summary['stored']['embedding_model'] or 'not set'}")
    click.echo(
        f"CLI override      : {summary['overrides']['cli_enable_ai'] if summary['overrides']['cli_enable_ai'] is not None else 'not provided'}"
    )
    click.echo(f"Model override    : {summary['overrides']['cli_embedding_model'] or 'not provided'}")

    click.echo("\nResolved policy")
    click.echo("-" * 70)
    click.echo(f"Dependencies ready    : {'yes' if summary['resolved']['dependencies_ready'] else 'no'}")
    resolved_pref = summary["resolved"]["use_transformers"]
    click.echo(f"Use transformers?     : {resolved_pref if resolved_pref is not None else 'auto'}")
    click.echo(f"Resolved embedding    : {summary['resolved']['embedding_model']}")
    click.echo(f"Requires installation : {'yes' if summary['resolved']['requires_installation'] else 'no'}")
    roi = summary.get("roi")
    click.echo("\nROI (Context Pruning)")
    click.echo("-" * 70)
    if roi:
        click.echo(f"Tokens saved          : {roi.get('tokens_saved')}")
        click.echo(f"Tokens used           : {roi.get('tokens_used')}")
        click.echo(f"Savings (%)           : {roi.get('savings_percentage', 0.0):.2f}%")
        click.echo(f"Cost saved USD        : ${roi.get('estimated_cost_saved_usd', 0.0):.2f}")
        click.echo(f"Events                : {roi.get('context_pruning_events')}")
    else:
        click.echo("No events recorded yet.")

    hooks = summary.get("hooks") or {}
    click.echo("\nGit Hooks")
    click.echo("-" * 70)
    pre_push = hooks.get("pre_push", {})
    click.echo(
        f"pre-push              : {'installed' if pre_push.get('installed') else 'missing'}"
        f" ({pre_push.get('mode') or 'n/a'})"
    )
    pre_commit = hooks.get("pre_commit", {})
    click.echo(
        f"pre-commit            : {'installed' if pre_commit.get('installed') else 'missing'}"
        f" ({pre_commit.get('mode') or 'n/a'})"
    )
    click.echo("=" * 70 + "\n")


def _render_html_report(summary: dict) -> str:
    """Build lightweight HTML report for governance status."""
    rows = [
        ("Project directory", summary["project_dir"]),
        ("Config detected", summary["config_detected"] or "not found"),
        ("Stored preference", summary["stored"]["use_transformers"]),
        ("Stored model", summary["stored"]["embedding_model"]),
        ("CLI override (AI)", summary["overrides"]["cli_enable_ai"]),
        ("CLI override (model)", summary["overrides"]["cli_embedding_model"]),
        ("Dependencies ready", summary["resolved"]["dependencies_ready"]),
        ("Resolved use_transformers", summary["resolved"]["use_transformers"]),
        ("Resolved embedding model", summary["resolved"]["embedding_model"]),
        ("Requires installation", summary["resolved"]["requires_installation"]),
    ]
    rows_html = "\n".join(
        f"<tr><th>{label}</th><td>{value if value is not None else '—'}</td></tr>" for label, value in rows
    )

    roi = summary.get("roi")
    roi_rows = ""
    if roi:
        roi_pairs = [
            ("Tokens saved", roi.get("tokens_saved")),
            ("Tokens used", roi.get("tokens_used")),
            ("Savings %", f"{roi.get('savings_percentage', 0.0):.2f}%"),
            ("Estimated cost saved (USD)", f"${roi.get('estimated_cost_saved_usd', 0.0):.2f}"),
            ("Events", roi.get("context_pruning_events")),
        ]
        roi_rows = (
            "<h2>ROI (Context Pruning)</h2><table>"
            + "\n".join(
                f"<tr><th>{label}</th><td>{value if value is not None else '—'}</td></tr>" for label, value in roi_pairs
            )
            + "</table>"
        )

    hooks = summary.get("hooks") or {}
    hook_rows = (
        "<h2>Git Hooks</h2>"
        "<table>"
        f"<tr><th>pre-push</th><td>{'installed' if hooks.get('pre_push', {}).get('installed') else 'missing'}"
        f" ({hooks.get('pre_push', {}).get('mode') or 'n/a'})</td></tr>"
        f"<tr><th>pre-commit</th><td>{'installed' if hooks.get('pre_commit', {}).get('installed') else 'missing'}"
        f" ({hooks.get('pre_commit', {}).get('mode') or 'n/a'})</td></tr>"
        "</table>"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>AI Governance Status</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; background: #f8fafc; color: #0f172a; }}
    h1 {{ margin-bottom: 1rem; }}
    table {{ border-collapse: collapse; width: 100%; background: white; margin-bottom: 1.5rem; }}
    th, td {{ text-align: left; padding: 0.75rem; border-bottom: 1px solid #e2e8f0; }}
    th {{ width: 30%; background: #f1f5f9; }}
  </style>
</head>
<body>
  <h1>AI Governance Status</h1>
  <table>
    {rows_html}
  </table>
  {roi_rows}
  {hook_rows}
</body>
</html>
"""


__all__ = ["ai_governance", "build_ai_governance_summary"]
