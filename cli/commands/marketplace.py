"""Marketplace commands for Context Engineer CLI."""

from __future__ import annotations

from pathlib import Path

import click

from cli.shared import MARKETPLACE_SERVICE


@click.group(help="Explore and install marketplace assets (patterns, workflows, accelerators).")
def marketplace():
    """Local marketplace command group."""


@marketplace.command("list", help="List available marketplace items.")
def marketplace_list():
    """List the local marketplace catalog."""
    catalog = MARKETPLACE_SERVICE.load_catalog()
    if not catalog:
        click.echo("No items found in docs/marketplace_catalog.json")
        return

    click.echo("\nAvailable items:\n")
    for item in catalog:
        click.echo(f"• {item.get('id')} - {item.get('name', 'Untitled')} ({item.get('category', 'unknown category')})")
        if item.get("description"):
            click.echo(f"    {item['description']}")
        if item.get("stack"):
            click.echo(f"    stacks: {', '.join(item['stack'])}")
        click.echo("")


@marketplace.command("install", help="Install a marketplace item into the current project.")
@click.argument("item_id")
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    help="Directory where the resource will be installed.",
)
@click.option(
    "--destination",
    help="Destination subdirectory (overrides target_dir defined in the item).",
)
def marketplace_install(item_id, project_dir, destination):
    """Install a specific marketplace item into the project."""
    item = MARKETPLACE_SERVICE.find_item(item_id)
    if not item:
        raise click.ClickException(f"Item '{item_id}' not found. Run 'ce marketplace list' to see available IDs.")

    project_path = Path(project_dir).resolve()
    try:
        target_path = MARKETPLACE_SERVICE.copy_resource(item, project_path, destination)
        click.echo(f"[OK] Item '{item_id}' installed at {target_path}")
    except click.ClickException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise click.ClickException(f"Failed to install item: {exc}")


__all__ = ["marketplace"]
