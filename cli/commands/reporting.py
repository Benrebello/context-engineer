"""Reporting and observability commands."""

from __future__ import annotations

import json
import re
from pathlib import Path

import click

from cli.shared import (
    STATUS_SERVICE,
    create_engine,
    embedding_model_option,
)
from core.metrics import MetricsCollector
from core.planning import EffortEstimator
from core.reporting_service import ReportingService


@click.command(help="AI efficiency dashboard with rework and ROI analysis.")
@click.option("--project-name", help="Specific project name.")
@click.option("--stack", help="Filter by stack.")
@click.option(
    "--format",
    default="table",
    type=click.Choice(["table", "json", "html"]),
    help="Output format.",
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False),
    help="HTML output file when --format=html.",
)
def report(project_name, stack, format, output):
    """Render individual or global dashboards."""
    try:
        metrics_collector = MetricsCollector(Path(".cache") / "metrics")
        reporting_service = ReportingService(metrics_collector)

        if project_name:
            metrics, analysis, roi_metrics = reporting_service.load_project_metrics(project_name)
            if format == "json":
                click.echo(
                    json.dumps(
                        {
                            "project": project_name,
                            "metrics": {
                                "prp_generation_time_minutes": metrics.prp_generation_time_minutes,
                                "task_completion_rate": metrics.task_completion_rate,
                                "test_coverage_achieved": metrics.test_coverage_achieved,
                                "code_quality_score": metrics.code_quality_score,
                                "rework_rate": metrics.rework_rate,
                                "total_tasks": metrics.total_tasks,
                                "completed_tasks": metrics.completed_tasks,
                            },
                            "efficiency_analysis": analysis,
                            "roi": roi_metrics,
                        },
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            elif format == "html":
                html_content = reporting_service.render_project_dashboard_html(
                    project_name, metrics, analysis, roi_metrics
                )
                output_path = Path(output or f"dashboard_{project_name}.html").resolve()
                output_path.write_text(html_content, encoding="utf-8")
                click.echo(f"[OK] Dashboard saved to {output_path}")
            else:
                click.echo(
                    reporting_service.render_project_dashboard_html(project_name, metrics, analysis, roi_metrics)
                )
            return

        all_metrics, avg_metrics = reporting_service.load_global_metrics(stack_filter=stack)
        if not all_metrics:
            click.echo("No metrics found.")
            return
        if format == "json":
            click.echo(
                json.dumps(
                    {
                        "total_projects": len(all_metrics),
                        "average_metrics": avg_metrics,
                        "projects": [
                            {
                                "name": m.project_name,
                                "rework_rate": m.rework_rate,
                                "completion_rate": m.task_completion_rate,
                            }
                            for m in all_metrics
                        ],
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
        elif format == "html":
            html_content = reporting_service.render_global_dashboard_html(
                all_metrics,
                avg_metrics,
                stack_filter=stack,
            )
            output_path = Path(output or "dashboard_global.html").resolve()
            output_path.write_text(html_content, encoding="utf-8")
            click.echo(f"[OK] Global dashboard saved to {output_path}")
        else:
            click.echo(reporting_service.render_global_dashboard_html(all_metrics, avg_metrics, stack_filter=stack))
    except Exception as exc:  # pragma: no cover
        click.echo(f"Error: {exc}", err=True)
        raise click.Abort()


def _analyze_efficiency(metrics) -> dict:
    """Return risk analysis for project efficiency metrics."""
    rework_risk = "low"
    if metrics.rework_rate > 30:
        rework_risk = "high"
    elif metrics.rework_rate > 15:
        rework_risk = "medium"

    completion_risk = "low"
    if metrics.task_completion_rate < 50:
        completion_risk = "high"
    elif metrics.task_completion_rate < 70:
        completion_risk = "medium"

    overall_score = (
        (100 - metrics.rework_rate * 2)
        + metrics.task_completion_rate
        + metrics.test_coverage_achieved / 10
        + metrics.code_quality_score * 10
    ) / 4

    return {
        "rework_risk": rework_risk,
        "completion_risk": completion_risk,
        "overall_score": overall_score,
    }


@click.command(help="Quick metrics summary for Git hooks.")
@click.option("--project-name", required=True, help="Project name.")
@click.option(
    "--tasks-dir",
    type=click.Path(exists=True, file_okay=False),
    help="Tasks directory (optional) for Story Point estimation.",
)
def metrics_summary(project_name, tasks_dir):
    """Show compact metrics snapshot for Git hook contexts."""
    try:
        metrics_collector = MetricsCollector(Path(".cache") / "metrics")
        metrics = metrics_collector.load_metrics(project_name)

        total_story_points = None
        if tasks_dir:
            tasks_path = Path(tasks_dir)
            task_files = list(tasks_path.glob("TASK.*.json")) + list(tasks_path.glob("TASK.*.md"))
            if task_files:
                estimator = EffortEstimator(metrics_collector)
                total_points = 0
                stack = "python-fastapi"
                if (tasks_path.parent / "package.json").exists():
                    stack = "node-react"
                elif (tasks_path.parent / "vite.config.js").exists() or (tasks_path.parent / "vite.config.ts").exists():
                    stack = "vue3"
                for task_file in task_files[:10]:
                    try:
                        with open(task_file, encoding="utf-8") as f:
                            if task_file.suffix == ".json":
                                task = json.load(f)
                            else:
                                content = f.read()
                                match = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
                                if not match:
                                    continue
                                task = json.loads(match.group(1))
                        points = estimator.estimate_effort_points(task, stack, project_name)
                        total_points += points
                    except Exception:
                        continue
                total_story_points = total_points

        click.echo("")
        click.echo("PROJECT METRICS SUMMARY")
        click.echo("─" * 50)
        if total_story_points is not None:
            click.echo(f"   Estimated Story Points: {total_story_points}")
        click.echo(f"   Rework rate: {metrics.rework_rate:.1f}%")
        click.echo(f"   Completion rate: {metrics.task_completion_rate:.1f}%")
        click.echo(f"   Tasks: {metrics.completed_tasks}/{metrics.total_tasks}")
        analysis = _analyze_efficiency(metrics)
        if analysis["rework_risk"] == "high":
            click.echo("")
            click.echo("   HIGH RISK: Rework rate above 30%")
            click.echo("      Breaking traceability may increase this risk further.")
        elif analysis["rework_risk"] == "medium":
            click.echo("")
            click.echo("   MODERATE RISK: Rework rate between 15-30%")
        click.echo("─" * 50)
        click.echo("")
    except Exception as exc:  # pragma: no cover
        click.echo(f"   Could not load metrics: {exc}", err=True)


@click.command(help="Diagnose AI/embedding mode and suggest fixes.")
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    help="Project directory to load .ce-config.",
)
@embedding_model_option("Override embedding model just for this diagnosis.")
def ai_status(project_dir, embedding_model):
    """Report IA/embedding configuration state for the target project."""
    project_path = Path(project_dir).resolve()
    project_root, config = STATUS_SERVICE.config_service.load_project_config(project_path)
    stored_pref = config.get("use_transformers") if config else None
    stored_model = config.get("embedding_model") if config else None
    chosen_model = embedding_model or stored_model

    click.echo("\n" + "=" * 70)
    click.echo("AI Mode Diagnostic")
    click.echo("=" * 70)
    click.echo(f"Analyzed directory: {project_path}")
    click.echo(f"Config detected: {project_root or 'not found'}")
    click.echo(f"Configured preference: {stored_pref if stored_pref is not None else 'not set'}")
    click.echo(f"Configured model: {stored_model}")
    click.echo(f"Requested model: {chosen_model}")

    try:
        engine = create_engine(
            context_hint=project_path,
            use_transformers=stored_pref,
            embedding_model=chosen_model,
        )
        cache = engine.cache
        resolved_mode = "Transformers (AI)" if cache.use_transformers else "Levenshtein (light)"
        click.echo(f"\nResolved mode (Modo resolvido) for this project: {resolved_mode}")
        click.echo(f"Effective model: {cache.selected_model}")
    except Exception as exc:  # pragma: no cover
        click.echo("\n[WARN] Could not initialize the engine for diagnostics.")
        click.echo(f"Details: {exc}")

    click.echo("\n" + "=" * 70)
    click.echo("Useful commands:")
    click.echo("  • ce init --ai            # force AI mode")
    click.echo("  • ce init --no-ai         # force lightweight mode")
    click.echo("  • ce <cmd> --embedding-model bge-small-en-v1.5")
    click.echo('  • pip install "context-engineer[ai]"')
    click.echo("=" * 70 + "\n")


__all__ = ["report", "metrics_summary", "ai_status"]
