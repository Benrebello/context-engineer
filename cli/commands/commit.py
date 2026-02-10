"""Commit mapping commands for Context Engineer CLI."""

from __future__ import annotations

from pathlib import Path

import click

from cli.shared import build_commit_mapping


@click.command(help="Generate commits.json with Task → commits/PR mapping.")
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    help="Project root directory (must contain .git).",
)
@click.option(
    "--output",
    default="commits.json",
    type=click.Path(dir_okay=False),
    help="Output file path.",
)
@click.option(
    "--git-range",
    "git_range",
    help="Git history filter (e.g., origin/main..HEAD). Default: entire local history.",
)
@click.option(
    "--include-uncommitted/--skip-uncommitted",
    default=True,
    show_default=True,
    help="Include uncommitted changes as WORKTREE.",
)
def generate_commit_map(project_dir, output, git_range, include_uncommitted):
    """Generate Task → commits mapping file from git history."""
    try:
        project_path = Path(project_dir).resolve()
        git_dir = project_path / ".git"
        if not git_dir.exists():
            click.echo(".git directory not found. Run 'git init' first.", err=True)
            raise click.Abort()

        mapping = build_commit_mapping(project_path, since=git_range, include_uncommitted=include_uncommitted)

        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = project_path / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as fp:
            import json

            json.dump(mapping, fp, indent=2, ensure_ascii=False)

        click.echo(f"[OK] Commit map saved to {output_path}")
    except click.Abort:
        raise
    except Exception as exc:
        click.echo(f"Error while generating commit map: {exc}", err=True)
        raise click.Abort()


__all__ = ["generate_commit_map"]
