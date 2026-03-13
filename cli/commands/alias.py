"""Alias management commands for Context Engineer CLI."""

from __future__ import annotations

import json
from pathlib import Path

import click


@click.command(help="Manage handy aliases for common commands.")
@click.argument("action", type=click.Choice(["list", "add", "remove"]), required=False)
@click.argument("alias", required=False)
@click.argument("command", required=False)
def alias(action, alias, command):
    """Create, remove, or list custom aliases."""
    config_dir = Path.home() / ".context-engineer"
    config_dir.mkdir(exist_ok=True)
    aliases_file = config_dir / "aliases.json"

    aliases = {}
    if aliases_file.exists():
        try:
            with open(aliases_file, encoding="utf-8") as f:
                aliases = json.load(f)
        except Exception:
            aliases = {}

    default_aliases = {
        "gp": "generate-prd",
        "gpr": "generate-prps",
        "gt": "generate-tasks",
        "v": "validate",
        "s": "status",
        "c": "checklist",
        "a": "assist",
    }

    if not action or action == "list":
        click.echo("\nAvailable Aliases:")
        click.echo("─" * 70)
        all_aliases = {**default_aliases, **aliases}
        for alias_name, cmd in sorted(all_aliases.items()):
            click.echo(f"   {alias_name:10} -> ce {cmd}")
        click.echo("\n[Tip] Use 'ce alias add <alias> <command>' to create new shortcuts.")
        return

    if action == "add":
        if not alias or not command:
            click.echo("Error: specify both alias and command.", err=True)
            click.echo("Usage: ce alias add <alias> <command>")
            raise click.Abort()
        aliases[alias] = command
        with open(aliases_file, "w", encoding="utf-8") as f:
            json.dump(aliases, f, indent=2)
        click.echo(f"[OK] Alias '{alias}' created: ce {alias} -> ce {command}")

    elif action == "remove":
        if not alias:
            click.echo("Error: specify the alias to remove.", err=True)
            raise click.Abort()
        if alias in aliases:
            del aliases[alias]
            with open(aliases_file, "w", encoding="utf-8") as f:
                json.dump(aliases, f, indent=2)
            click.echo(f"[OK] Alias '{alias}' removed")
        elif alias in default_aliases:
            click.echo(f"[WARN] '{alias}' is a default alias and cannot be removed.")
        else:
            click.echo(f"[WARN] Alias '{alias}' not found.")


__all__ = ["alias"]
