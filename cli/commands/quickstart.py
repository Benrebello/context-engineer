"""Quickstart command for new users - 5-minute setup guide."""

from __future__ import annotations

from pathlib import Path

import click

from cli.shared import (
    echo_error,
    echo_info,
    echo_step,
    echo_success,
    echo_warning,
    embedding_model_option,
    hybrid_ai_option,
)


@click.command(help="5-minute quick guide to get started with Context Engineer")
@click.option("--skip-intro", is_flag=True, help="Skip introduction and go straight to setup")
@click.option("--interactive", "-i", is_flag=True, help="Full tutorial mode with detailed explanations (15 min)")
@click.option("--example", type=click.Choice(["todo-app", "blog", "ecommerce", "api"]), help="Use pre-configured example project")
@hybrid_ai_option()
@embedding_model_option()
def quickstart(skip_intro: bool, interactive: bool, example: str | None, enable_ai: bool | None, embedding_model: str | None) -> None:
    """Interactive quickstart guide for new users."""
    from .generation import generate_prd, generate_prps, generate_tasks, init
    from .status import status

    if not skip_intro:
        click.echo("\n" + "=" * 70)
        click.secho("CONTEXT ENGINEER - QUICKSTART", fg="cyan", bold=True)
        click.echo("=" * 70)
        
        if interactive:
            click.echo("\nFull Tutorial Mode Activated!")
            click.echo("\nThis tutorial will guide you step by step, explaining each concept.")
            click.echo("Estimated time: ~15 minutes")
        else:
            click.echo("\nWelcome! This guide will set up your first project in 5 minutes.")
        
        click.echo("\nWhat we'll do:")
        click.echo("  1. Create project structure")
        click.echo("  2. Generate PRD (Product Requirements Document)")
        click.echo("  3. Generate PRPs (Phase Requirement Plans)")
        if interactive:
            click.echo("  4. Generate executable Tasks")
            click.echo("  5. Validate traceability")
            click.echo("  6. View status and metrics")
        else:
            click.echo("  4. View project status")
        click.echo("\nYou can interrupt at any time with Ctrl+C\n")
        
        if interactive:
            click.echo("Tip: Use --example todo-app for a pre-configured example")
        
        click.echo("=" * 70)

        if not click.confirm("\nReady to start?", default=True):
            echo_warning("Quickstart cancelled. Run 'ce quickstart' when ready.")
            return
        
        if interactive:
            _show_concept_explanation("context_engineer")

    try:
        ctx = click.get_current_context()

        # Step 1: Initialize project
        echo_step(1, 4, "Initialize Project")
        click.echo("")

        project_name = click.prompt(
            "Project name",
            default=Path.cwd().name,
            show_default=True,
        )

        stack_options = ["python-fastapi", "node-react", "vue3", "go-gin"]
        click.echo("\nAvailable stacks:")
        for idx, stack in enumerate(stack_options, 1):
            click.echo(f"  {idx}. {stack}")

        stack_choice = click.prompt(
            "\nChoose stack",
            type=click.Choice([str(i) for i in range(1, len(stack_options) + 1)]),
            default="1",
        )
        stack = stack_options[int(stack_choice) - 1]

        click.echo(f"\nInitializing project '{project_name}' with stack '{stack}'...")

        ctx.invoke(
            init,
            project_name=project_name,
            template="base",
            stack=stack,
            output="./",
            git_hooks=True,
            enable_ai=enable_ai,
            embedding_model=embedding_model,
        )

        echo_success("Project initialized!")
        click.echo("")

        # Step 2: Generate PRD
        echo_step(2, 4, "Generate PRD")
        click.echo("")

        if not click.confirm("Do you want to create the PRD now?", default=True):
            echo_info("You can generate the PRD later with: ce generate-prd --interactive")
            _show_next_steps()
            return

        click.echo("\nLet's create a simple PRD. Answer a few questions:\n")

        ctx.invoke(
            generate_prd,
            input_file=None,
            output="./prd",
            interactive=True,
            auto_validate=True,
            preview=False,
            enable_ai=enable_ai,
            embedding_model=embedding_model,
        )

        echo_success("PRD created!")
        click.echo("")

        # Step 3: Generate PRPs
        echo_step(3, 4, "Generate PRPs")
        click.echo("")

        if not click.confirm("Do you want to generate PRPs now?", default=True):
            echo_info("You can generate PRPs later with: ce generate-prps")
            _show_next_steps()
            return

        click.echo("\nGenerating PRPs (this may take a few seconds)...\n")

        ctx.invoke(
            generate_prps,
            prd_file=None,
            output="./prps",
            parallel=False,
            interactive=True,
            auto_validate=True,
            preview=False,
            phase=None,
            enable_ai=enable_ai,
            embedding_model=embedding_model,
        )

        echo_success("PRPs generated!")
        click.echo("")

        # Step 4: Show status
        echo_step(4, 4, "Project Status")
        click.echo("")

        ctx.invoke(
            status,
            project_dir=".",
            json=False,
            enable_ai=enable_ai,
            embedding_model=embedding_model,
        )

        # Final summary
        click.echo("\n" + "=" * 70)
        echo_success("QUICKSTART COMPLETED!")
        click.echo("=" * 70)

        _show_next_steps()

    except click.Abort:
        echo_warning("\nQuickstart interrupted. You can resume by running 'ce quickstart'")
    except Exception as exc:
        echo_error(f"Error during quickstart: {exc}")
        echo_info("Run 'ce doctor' for complete diagnostics")
        raise click.Abort()


def _show_concept_explanation(concept: str) -> None:
    """Show detailed explanation of a concept."""
    explanations = {
        "context_engineer": (
            "\nWhat is Context Engineer?\n"
            "\nContext Engineer is a framework that transforms ideas into functional code\n"
            "through a structured and validated process:\n"
            "\n  Idea -> PRD -> PRPs -> Tasks -> Code\n"
            "\n* PRD: Product Requirements Document (WHAT to build)\n"
            "* PRPs: Phase Requirement Plans (HOW to build, divided into phases)\n"
            "* Tasks: Executable tasks with code and tests\n"
        ),
        "prd": (
            "\nWhat is a PRD?\n"
            "\nPRD (Product Requirements Document) defines:\n"
            "* Product vision\n"
            "* Functional requirements (FRs)\n"
            "* Non-functional requirements (NFRs)\n"
            "* Acceptance criteria\n"
            "\nIt's the foundation for all development.\n"
        ),
        "prps": (
            "\nWhat are PRPs?\n"
            "\nPRPs (Phase Requirement Plans) divide development into phases:\n"
            "* F0: Setup and Configuration\n"
            "* F1-F8: Incremental Implementation\n"
            "* F9: Testing and Validation\n"
            "\nEach phase has clear objectives and automatic validation.\n"
        ),
    }
    
    if concept in explanations:
        click.echo(explanations[concept])
        click.pause("\nPress Enter to continue...")


def _get_example_config(example_type: str) -> dict:
    """Get pre-configured example project settings."""
    examples = {
        "todo-app": {
            "name": "todo-app",
            "stack": "python-fastapi",
            "idea": "Todo list application with JWT authentication and REST API",
            "features": ["Create tasks", "Mark as completed", "Filter by status", "User authentication"],
        },
        "blog": {
            "name": "blog-platform",
            "stack": "node-react",
            "idea": "Blog platform with Markdown editor and comment system",
            "features": ["Create posts", "Markdown editor", "Comments", "Tags and categories"],
        },
        "ecommerce": {
            "name": "ecommerce-api",
            "stack": "python-fastapi",
            "idea": "E-commerce API with shopping cart and payment processing",
            "features": ["Product catalog", "Shopping cart", "Checkout", "Payment integration"],
        },
        "api": {
            "name": "rest-api",
            "stack": "go-gin",
            "idea": "Generic REST API with full CRUD and authentication",
            "features": ["CRUD operations", "JWT auth", "Rate limiting", "Swagger docs"],
        },
    }
    return examples.get(example_type, examples["todo-app"])


def _show_next_steps() -> None:
    """Display recommended next steps."""
    click.echo("\nRecommended Next Steps:")
    click.echo("")
    click.echo("  1. Generate executable tasks:")
    click.echo("     ce generate-tasks")
    click.echo("")
    click.echo("  2. Validate traceability:")
    click.echo("     ce validate --check-traceability")
    click.echo("")
    click.echo("  3. View interactive checklist:")
    click.echo("     ce checklist")
    click.echo("")
    click.echo("  4. Use conversational assistant:")
    click.echo("     ce assist")
    click.echo("")
    click.echo("Tips:")
    click.echo("  * Use aliases for quick commands: ce gp, ce gpr, ce gt")
    click.echo("  * Run 'ce --help' to see all commands")
    click.echo("  * Run 'ce status' anytime to see progress")
    click.echo("  * Use 'ce quickstart --interactive' for full tutorial")
    click.echo("")


__all__ = ["quickstart"]
