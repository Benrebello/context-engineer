"""IDE tooling commands for prompt synchronization."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import click

from cli.shared import REPO_ROOT


@click.group(name="ide", help="Tools to prepare AI-enabled IDE prompts and workflows.")
def ide() -> None:
    """Namespace for IDE-related commands."""


@ide.command("sync", help="Sync official prompts/workflows with the current project.")
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(file_okay=False),
    help="Project directory that will receive the .ide-rules folder (or equivalent).",
)
@click.option(
    "--source-dir",
    type=click.Path(exists=True, file_okay=False),
    help="Custom prompt source (default: embedded IDE-rules bundle).",
)
@click.option(
    "--target-dir",
    default=".ide-rules",
    help="Relative or absolute destination for sync (default: .ide-rules).",
)
@click.option(
    "--ide-name",
    default="IDE",
    help="Friendly IDE name for explanatory messages.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing files instead of preserving them.",
)
def ide_sync(project_dir, source_dir, target_dir, ide_name, force) -> None:
    """Copy official prompts/workflows into the IDE directory."""
    project_path = Path(project_dir).resolve()
    if not project_path.exists():
        raise click.ClickException(f"Target directory not found: {project_path}")

    bundle_root = Path(source_dir).resolve() if source_dir else (REPO_ROOT / "IDE-rules")
    if not bundle_root.exists():
        raise click.ClickException(
            f"Prompt bundle not found at {bundle_root}. Provide --source-dir."
        )

    target_path = Path(target_dir)
    if not target_path.is_absolute():
        target_path = project_path / target_path
    target_path = target_path.resolve()

    copied = 0
    skipped = 0
    overwritten = 0

    for root, dirs, files in os.walk(bundle_root):
        rel_root = Path(root).relative_to(bundle_root)
        dest_dir = target_path / rel_root
        dest_dir.mkdir(parents=True, exist_ok=True)

        for d in dirs:
            (dest_dir / d).mkdir(parents=True, exist_ok=True)

        for file_name in files:
            src_file = Path(root) / file_name
            dest_file = dest_dir / file_name

            if dest_file.exists():
                if force:
                    shutil.copy2(src_file, dest_file)
                    overwritten += 1
                else:
                    skipped += 1
                    continue
            else:
                shutil.copy2(src_file, dest_file)
                copied += 1

    click.echo("")
    click.echo("=" * 70)
    click.echo("IDE Sync - Context Engineer")
    click.echo("=" * 70)
    click.echo(f"Source     : {bundle_root}")
    click.echo(f"Target     : {target_path}")
    click.echo(f"Target IDE : {ide_name}")
    click.echo("-" * 70)
    click.echo(f"Files copied        : {copied}")
    click.echo(f"Files overwritten   : {overwritten}")
    click.echo(f"Files preserved     : {skipped}")
    click.echo("=" * 70)
    click.echo(
        "Setup complete! Open your IDE and reference the prompts directly "
        f"(e.g., @{ide_name}/prompts/Agente_PRD_360.md or configure the equivalent shortcut)."
    )


__all__ = ["ide"]
