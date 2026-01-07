"""DevOps and infrastructure-related CLI commands."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import click

from cli.shared import REPO_ROOT, _generate_git_hooks
from core.validators import PRPValidator


@click.command(
    name="ci-bootstrap",
    help="Generate the default CI workflow with automatic commits.json generation and validation.",
)
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    help="Project directory where the workflow will be created.",
)
@click.option(
    "--workflow-file",
    default=".github/workflows/context-engineer-ci.yml",
    type=click.Path(dir_okay=False),
    help="Relative path for the generated workflow.",
)
def ci_bootstrap(project_dir, workflow_file):
    """Install the default CI workflow based on the official template."""
    project_path = Path(project_dir).resolve()
    template_path = REPO_ROOT / "docs" / "ci_bootstrap_template.yml"
    if not template_path.exists():
        raise click.ClickException("CI template not found in docs/ci_bootstrap_template.yml")

    workflow_path = project_path / workflow_file
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template_path, workflow_path)

    click.echo(f"[OK] Workflow created at {workflow_path}")
    click.echo("Additional recommendations:")
    click.echo("  • Run 'ce install-hooks' to align local validations.")
    click.echo("  • Adjust lint/test steps inside the workflow file to match your stack.")


@click.command(help="Install Git hooks for automatic validation.")
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    help="Project directory (default: current directory).",
)
@click.option(
    "--hard-gate",
    is_flag=True,
    default=False,
    help="Use Hard-Gate (blocking) instead of Soft-Gate (advisory).",
)
def install_hooks(project_dir, hard_gate):
    """Install advisory or blocking Git hooks."""
    project_path = Path(project_dir).resolve()
    git_dir = project_path / ".git"
    if not git_dir.exists():
        click.echo(".git directory not found! Run 'git init' first.", err=True)
        raise click.Abort()

    project_name = project_path.name
    try:
        git_result = subprocess.run(
            ["git", "config", "remote.origin.url"],
            check=False, cwd=project_path,
            capture_output=True,
            text=True,
        )
        if git_result.returncode == 0 and git_result.stdout.strip():
            remote_url = git_result.stdout.strip()
            if "/" in remote_url:
                project_name = remote_url.split("/")[-1].replace(".git", "")
    except Exception:
        pass

    try:
        _generate_git_hooks(project_path, project_name, soft_gate=not hard_gate)
        mode = "Hard-Gate (blocking)" if hard_gate else "Soft-Gate (advisory)"
        click.echo("\nGit hooks installed successfully!")
        click.echo(f"   Mode: {mode}")
        click.echo(f"   Project: {project_name}")
        click.echo(f"   Location: {git_dir / 'hooks'}")
        if not hard_gate:
            click.echo("\nSoft-Gate mode:")
            click.echo("   • Displays warnings before push")
            click.echo("   • Allows continuing during emergencies (e.g., hotfixes)")
    except Exception as exc:
        click.echo(f"Error while installing hooks: {exc}", err=True)
        raise click.Abort()


@click.command(help="Launch an ephemeral mock server from an OpenAPI spec.")
@click.argument("openapi_spec", type=click.Path(exists=True))
@click.option("--port", default=4010, help="Mock server port.")
def mock_server(openapi_spec, port):
    """Generate a temporary mock server via Prism (F3)."""
    try:
        validator = PRPValidator()
        result = validator.generate_transient_mock(Path(openapi_spec), port)
        if result["success"]:
            click.echo(result["message"])
            click.echo(f"   URL: {result['mock_url']}")
            click.echo(f"   PID: {result['process_id']}")
            click.echo("\nUse the mock to exercise your UI. Press Ctrl+C to stop.")
        else:
            click.echo("Error while starting the mock server:")
            for error in result.get("errors", []):
                click.echo(f"   - {error}")
            for warning in result.get("warnings", []):
                click.echo(f"   {warning}")
            if "command" in result:
                click.echo(f"\nRun manually: {result['command']}")
            raise click.Abort()
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise click.Abort()


__all__ = ["ci_bootstrap", "install_hooks", "mock_server"]
