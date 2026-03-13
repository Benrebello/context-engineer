"""Context Engineer CLI entry point."""

from __future__ import annotations

import subprocess

import click

from cli.commands.ai_governance import ai_governance
from cli.commands.alias import alias
from cli.commands.autopilot import autopilot
from cli.commands.commit import commit
from cli.commands.devops import ci_bootstrap, git_setup, install_hooks, mock_server
from cli.commands.discuss import discuss
from cli.commands.doctor import doctor
from cli.commands.explore import explore
from cli.commands.generation import (
    check_dependencies,
    estimate_batch,
    estimate_effort,
    generate_prd,
    generate_prps,
    generate_tasks,
    init,
    validate,
)
from cli.commands.health_cmd import health
from cli.commands.ide import ide
from cli.commands.marketplace import marketplace
from cli.commands.patterns import patterns
from cli.commands.provider import provider
from cli.commands.quickstart import quickstart
from cli.commands.reporting import ai_status, metrics_summary, report
from cli.commands.session import session
from cli.commands.state import state
from cli.commands.status import assist, checklist, status, wizard
from cli.commands.verify import verify_phase
from cli.shared import (
    configure_logging as shared_configure_logging,
)
from cli.shared import (
    create_engine as shared_create_engine,
)
from cli.shared import (
    load_project_config as shared_load_project_config,
)
from core import __version__ as core_version
from core.cache import TRANSFORMERS_AVAILABLE as core_transformers_available
from core.engine import ContextEngine as CoreContextEngine

create_engine = shared_create_engine
load_project_config = shared_load_project_config
configure_logging = shared_configure_logging
ContextEngine = CoreContextEngine
TRANSFORMERS_AVAILABLE = core_transformers_available

# Expose subprocess module for backward-compatible monkeypatching in tests.
subprocess = subprocess


@click.group()
@click.version_option(version=core_version)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging (DEBUG) for the entire CLI session.",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress most logs by forcing WARNING level.",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
    help="Override logging level explicitly (overrides --verbose/--quiet).",
)
@click.option(
    "--install-completion",
    type=click.Choice(["bash", "zsh", "fish", "powershell"], case_sensitive=False),
    help="Install shell completion for the specified shell.",
)
@click.option(
    "--skill",
    multiple=True,
    help="Activate a specific agent skill (e.g. python, testing). Can be used multiple times.",
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool, log_level: str | None, install_completion: str | None, skill: tuple[str, ...]) -> None:
    """Context Engineer CLI - Framework de desenvolvimento assistido por IA."""
    ctx.ensure_object(dict)
    ctx.obj["skills"] = skill

    if install_completion:
        _install_shell_completion(install_completion)
        return

    configure_logging(verbose=verbose, quiet=quiet, level=log_level)

    # Log activated skills for visibility
    if skill:
        click.secho(f"Active Skills: {', '.join(skill)}", fg="cyan", dim=True)


    # Os comandos são registrados dinamicamente em _register_commands().


def _install_shell_completion(shell: str) -> None:
    """Install shell completion for the specified shell."""
    from pathlib import Path

    shell = shell.lower()

    click.echo(f"\nInstalling {shell} completion for Context Engineer CLI...\n")

    completion_scripts = {
        "bash": {
            "file": "~/.bashrc",
            "content": 'eval "$(_CE_COMPLETE=bash_source ce)"',
            "test": "ce --help > /dev/null 2>&1 && echo 'OK' || echo 'FAIL'",
        },
        "zsh": {
            "file": "~/.zshrc",
            "content": 'eval "$(_CE_COMPLETE=zsh_source ce)"',
            "test": "ce --help > /dev/null 2>&1 && echo 'OK' || echo 'FAIL'",
        },
        "fish": {
            "file": "~/.config/fish/completions/ce.fish",
            "content": "eval (env _CE_COMPLETE=fish_source ce)",
            "test": "ce --help > /dev/null 2>&1; and echo 'OK'; or echo 'FAIL'",
        },
        "powershell": {
            "file": "$PROFILE",
            "content": "Invoke-Expression (& ce --completion powershell)",
            "test": "ce --help",
        },
    }

    if shell not in completion_scripts:
        click.secho(f"Error: Shell '{shell}' not supported", fg="red")
        click.echo(f"Supported shells: {', '.join(completion_scripts.keys())}")
        return

    config = completion_scripts[shell]
    config_file = Path(config["file"]).expanduser()

    # Create directory if needed (for fish)
    if shell == "fish":
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(config["content"] + "\n")
        click.secho(f"[OK] Created {config_file}", fg="green")
    # Append to rc file
    elif config_file.exists():
        content = config_file.read_text()
        if config["content"] in content:
            click.secho(f"[OK] Completion already installed in {config_file}", fg="yellow")
        else:
            with open(config_file, "a") as f:
                f.write(f"\n# Context Engineer CLI completion\n{config['content']}\n")
            click.secho(f"[OK] Added completion to {config_file}", fg="green")
    else:
        click.secho(f"Warning: {config_file} not found, creating it...", fg="yellow")
        config_file.write_text(f"# Context Engineer CLI completion\n{config['content']}\n")
        click.secho(f"[OK] Created {config_file}", fg="green")

    click.echo("\nNext steps:")
    click.echo("  1. Reload your shell configuration:")
    if shell == "bash":
        click.echo("     source ~/.bashrc")
    elif shell == "zsh":
        click.echo("     source ~/.zshrc")
    elif shell == "fish":
        click.echo("     # Fish will auto-load on next shell start")
    elif shell == "powershell":
        click.echo("     . $PROFILE")

    click.echo("\n  2. Test completion:")
    click.echo("     ce <TAB><TAB>")
    click.echo("\nCompletion installed successfully!\n")


def _register_commands() -> None:
    """Adiciona todos os comandos modulares ao entrypoint principal."""
    # Pipeline principal
    cli.add_command(init)
    cli.add_command(generate_prd)
    cli.add_command(generate_prps)
    cli.add_command(generate_tasks)
    cli.add_command(state)
    cli.add_command(validate)
    cli.add_command(check_dependencies)
    cli.add_command(estimate_effort)
    cli.add_command(estimate_batch)
    cli.add_command(commit)

    # Assistentes e automações
    cli.add_command(quickstart)
    cli.add_command(explore)
    cli.add_command(status)
    cli.add_command(checklist)
    cli.add_command(assist)
    cli.add_command(wizard)
    cli.add_command(autopilot)

    # Marketplace e padrões
    cli.add_command(marketplace)
    cli.add_command(patterns)
    cli.add_command(ide)

    # Relatórios e diagnósticos
    cli.add_command(report)
    cli.add_command(metrics_summary)
    cli.add_command(ai_status)
    cli.add_command(ai_governance)
    cli.add_command(doctor)

    # DevOps e utilidades
    cli.add_command(ci_bootstrap)
    cli.add_command(git_setup)
    cli.add_command(install_hooks)
    cli.add_command(mock_server)
    cli.add_command(alias)

    # Configuração de provedores LLM
    cli.add_command(provider)

    # Round 2: Novos comandos de otimização
    cli.add_command(discuss)
    cli.add_command(verify_phase)
    cli.add_command(health)
    cli.add_command(session)


_register_commands()


__all__ = [
    "cli",
    "create_engine",
    "load_project_config",
    "ContextEngine",
    "TRANSFORMERS_AVAILABLE",
    "subprocess",
    "ai_governance",
]


if __name__ == "__main__":
    cli()
