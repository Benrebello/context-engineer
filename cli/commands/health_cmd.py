"""CLI commands for project health checks."""

from pathlib import Path

import click


@click.command(name="health", help="Check project health and integrity.")
@click.option("--project-dir", default=".", help="Project root directory.")
@click.option("--repair", is_flag=True, default=False, help="Auto-fix fixable issues.")
@click.option("--json-output", "json_out", is_flag=True, default=False, help="Output as JSON.")
def health(project_dir: str, repair: bool, json_out: bool) -> None:
    """Diagnose and optionally repair project issues."""
    import json

    from core.health import HealthChecker

    project_path = Path(project_dir).resolve()
    checker = HealthChecker(project_path)
    issues = checker.run_full_check()

    if json_out:
        output = {
            "healthy": len(issues) == 0,
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "message": i.message,
                    "auto_fixable": i.auto_fixable,
                }
                for i in issues
            ],
        }
        click.echo(json.dumps(output, indent=2))
        return

    if not issues:
        click.secho("✅ Project is healthy! All checks passed.", fg="green")
        return

    # Display issues
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    click.secho(f"\n🏥 Health Report: {len(issues)} issue(s) found\n", fg="yellow", bold=True)

    if errors:
        click.secho("❌ Errors:", fg="red", bold=True)
        for issue in errors:
            click.echo(f"   [{issue.category}] {issue.message}")

    if warnings:
        click.secho("⚠️  Warnings:", fg="yellow", bold=True)
        for issue in warnings:
            fixable = " (auto-fixable)" if issue.auto_fixable else ""
            click.echo(f"   [{issue.category}] {issue.message}{fixable}")

    if infos:
        click.secho("ℹ️  Info:", fg="blue")
        for issue in infos:
            click.echo(f"   [{issue.category}] {issue.message}")

    # Repair if requested
    fixable_count = sum(1 for i in issues if i.auto_fixable)
    if repair and fixable_count:
        click.echo("")
        actions = checker.repair()
        for action in actions:
            click.secho(f"  🔧 {action}", fg="green")
        click.secho(f"\n✅ Repaired {len(actions)} issue(s).", fg="green")
    elif fixable_count:
        click.secho(f"\n💡 {fixable_count} issue(s) can be auto-fixed. Run with --repair.", fg="cyan")
