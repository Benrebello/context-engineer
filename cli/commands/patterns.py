"""Pattern library commands for Context Engineer CLI."""

from __future__ import annotations

import json
from pathlib import Path

import click

from cli.shared import create_engine, embedding_model_option, hybrid_ai_option
from core.project_analyzer import ProjectAnalyzer


def _render_pattern_card(pattern: dict, show_content: bool = False) -> None:
    """Render basic info for a pattern in CLI output."""
    click.echo(f" • {pattern.get('pattern_id')} - {pattern.get('name', 'Unnamed')}")
    click.echo(
        f"   Category: {pattern.get('category', 'N/A')} | Complexity: {pattern.get('complexity', 'N/A')}"
    )
    click.echo(
        f"   Stack: {', '.join(pattern.get('stack', [])) or 'N/A'} | Tags: {', '.join(pattern.get('tags', [])) or 'N/A'}"
    )
    if show_content:
        click.echo("\n   Content:\n   ─────────")
        for line in pattern.get("content", "").splitlines():
            click.echo(f"   {line}")
        click.echo("\n")
    else:
        click.echo("")


@click.group(help="Manage reusable Context Engineer patterns.")
def patterns():
    """Command group for listing and suggesting patterns."""


@patterns.command("list", help="List available patterns with optional filters.")
@click.option("--category", help="Pattern category.")
@click.option("--stack", multiple=True, help="Tech stack (repeatable).")
@click.option("--complexity", help="Complexity (low, medium, high).")
@click.option("--tag", "tags", multiple=True, help="Pattern tag (repeatable).")
@click.option("--limit", default=20, show_default=True, help="Maximum number of results.")
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json"]),
    show_default=True,
    help="Output format.",
)
@hybrid_ai_option()
@embedding_model_option()
def patterns_list(category, stack, complexity, tags, limit, output_format, enable_ai, embedding_model):
    """List patterns applying optional filters."""
    try:
        engine = create_engine(use_transformers=enable_ai, embedding_model=embedding_model)
        results = engine.pattern_library.search(
            stack=list(stack) if stack else None,
            category=category,
            complexity=complexity,
            tags=list(tags) if tags else None,
        )

        if not results:
            click.echo("No patterns found.")
            return

        limited = results[:limit]
        if output_format == "json":
            click.echo(
                json.dumps(
                    {
                        "count": len(limited),
                        "results": limited,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return

        click.echo(f"{len(limited)} pattern(s) shown out of {len(results)} total:\n")
        for pattern in limited:
            _render_pattern_card(pattern)
    except Exception as exc:  # pragma: no cover - defensive
        click.echo(f"Error: {exc}", err=True)


@patterns.command("show", help="Show full details of a pattern.")
@click.argument("pattern_id")
@click.option("--content/--no-content", default=True, show_default=True, help="Display pattern content.")
@hybrid_ai_option()
@embedding_model_option()
def patterns_show(pattern_id, content, enable_ai, embedding_model):
    """Display detailed info about a specific pattern."""
    try:
        engine = create_engine(use_transformers=enable_ai, embedding_model=embedding_model)
        pattern = engine.pattern_library.get_pattern(pattern_id)
        if not pattern:
            click.echo(f"Pattern '{pattern_id}' not found.")
            return

        _render_pattern_card(pattern, show_content=content)
    except Exception as exc:  # pragma: no cover
        click.echo(f"Error: {exc}", err=True)


@patterns.command("suggest", help="Suggest patterns based on project context.")
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    help="Project directory for context extraction.",
)
@click.option("--limit", default=5, show_default=True, help="Maximum number of suggestions.")
@hybrid_ai_option()
@embedding_model_option()
def patterns_suggest(project_dir, limit, enable_ai, embedding_model):
    """Suggest relevant patterns using project context."""
    try:
        project_path = Path(project_dir).resolve()
        analyzer = ProjectAnalyzer(project_path)
        assistant_context = analyzer.build_assistant_context()
        pattern_context = assistant_context.get("pattern_context", {})

        if not pattern_context.get("stack"):
            click.echo("Stack not detected. Run 'ce init' or configure .ce-config.json first.")
            return

        engine = create_engine(
            use_transformers=enable_ai,
            context_hint=project_path,
            embedding_model=embedding_model,
        )
        suggestions = engine.pattern_library.suggest_patterns(pattern_context)

        if not suggestions:
            click.echo("No relevant patterns found for the current context.")
            return

        click.echo(
            f"Suggestions for stack {', '.join(pattern_context.get('stack', []))} (limited to {limit}):\n"
        )
        for pattern in suggestions[:limit]:
            _render_pattern_card(pattern)
    except Exception as exc:  # pragma: no cover
        click.echo(f"Error: {exc}", err=True)


__all__ = ["patterns"]
