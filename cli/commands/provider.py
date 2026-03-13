"""CLI commands for LLM provider configuration."""

from __future__ import annotations

from pathlib import Path

import click

from cli.shared import CONFIG_SERVICE, echo_error, echo_info, echo_success, echo_warning
from core.llm_provider import LLM_PROVIDER_SERVICE, PROVIDER_REGISTRY, LLMProviderType

# ---------------------------------------------------------------------------
# Provider group
# ---------------------------------------------------------------------------


@click.group(name="provider", help="Configure LLM provider, model, and API keys.")
def provider() -> None:
    """Manage LLM provider settings."""


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------


@provider.command("list", help="List all supported LLM providers.")
def provider_list() -> None:
    """Display available providers and their status."""
    providers = LLM_PROVIDER_SERVICE.list_providers()
    click.echo("\n" + "=" * 70)
    click.echo("  Supported LLM Providers")
    click.echo("=" * 70)
    for p in providers:
        has_key = LLM_PROVIDER_SERVICE.has_api_key(p["id"])
        status = click.style(" [configured]", fg="green") if has_key else ""
        if not p["requires_api_key"]:
            status = click.style(" [local]", fg="cyan")
        click.echo(f"  {p['id']:<20} {p['display_name']:<25} model: {p['default_model']}{status}")
    click.echo("=" * 70)
    echo_info("Tip: Use 'ce provider set-model <provider> <model>' to use a custom model.")
    click.echo()


@provider.command("setup", help="Interactively configure an LLM provider for the project.")
@click.option(
    "--provider-id",
    type=click.Choice([p.value for p in LLMProviderType], case_sensitive=False),
    help="Provider to configure (skip interactive selection).",
)
@click.option("--model", help="Override the default model for the provider.")
@click.option("--port", type=int, help="Custom port for local providers (Ollama / LM Studio).")
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    help="Project directory to save configuration.",
)
def provider_setup(
    provider_id: str | None,
    model: str | None,
    port: int | None,
    project_dir: str,
) -> None:
    """Walk the user through provider configuration."""
    project_path = Path(project_dir).resolve()

    # Step 1 — select provider
    if not provider_id:
        click.echo("\nSelect an LLM provider:\n")
        choices = list(LLMProviderType)
        for idx, pt in enumerate(choices, 1):
            meta = PROVIDER_REGISTRY[pt]
            click.echo(f"  {idx}. {meta['display_name']:<25} ({pt.value})")
        click.echo()
        selection = click.prompt(
            "Enter the number or provider id",
            type=str,
        )
        # Accept number or string
        if selection.isdigit():
            index = int(selection) - 1
            if 0 <= index < len(choices):
                provider_id = choices[index].value
            else:
                echo_error("Invalid selection.")
                raise click.Abort()
        else:
            provider_id = selection.strip().lower()

    try:
        ptype = LLMProviderType(provider_id)
    except ValueError:
        echo_error(f"Unknown provider: {provider_id}")
        raise click.Abort()

    meta = PROVIDER_REGISTRY[ptype]

    # Step 2 — API key (if required)
    if meta["requires_api_key"]:
        existing = LLM_PROVIDER_SERVICE.has_api_key(provider_id)
        if existing:
            overwrite = click.confirm(
                f"An API key for {meta['display_name']} already exists. Overwrite?",
                default=False,
            )
            if not overwrite:
                echo_info("Keeping existing API key.")
            else:
                api_key = click.prompt("Enter API key", hide_input=True)
                LLM_PROVIDER_SERVICE.store_api_key(provider_id, api_key.strip())
                echo_success("API key encrypted and stored.")
        else:
            api_key = click.prompt(f"Enter API key for {meta['display_name']}", hide_input=True)
            LLM_PROVIDER_SERVICE.store_api_key(provider_id, api_key.strip())
            echo_success("API key encrypted and stored.")

    # Step 3 — model selection
    resolved_model = model or meta["default_model"]
    if not model:
        use_default = click.confirm(
            f"Use default model '{resolved_model}'?",
            default=True,
        )
        if not use_default:
            echo_info(
                "The model name must match exactly what the provider's API expects.\n"
                f"   Examples for {meta['display_name']}: {meta['default_model']}\n"
                "   Check the provider's documentation for available model identifiers."
            )
            resolved_model = click.prompt("Enter model name")
    elif model != meta["default_model"]:
        echo_info(f"Using custom model '{model}'. " "Make sure this name matches the provider's API model identifier.")

    # Step 4 — custom port for local providers
    custom_port = port
    if ptype == LLMProviderType.LOCAL_OLLAMA and not port:
        use_default_port = click.confirm("Use default Ollama port (11434)?", default=True)
        if not use_default_port:
            custom_port = click.prompt("Enter Ollama port", type=int)

    if ptype == LLMProviderType.LOCAL_LM_STUDIO and not port:
        custom_port = click.prompt(
            "Enter LM Studio port",
            type=int,
            default=1234,
            show_default=True,
        )

    # Step 5 — persist to project config
    config_payload: dict = {
        "llm_provider": provider_id,
        "llm_model": resolved_model,
    }
    if custom_port:
        config_payload["llm_custom_port"] = custom_port

    CONFIG_SERVICE.save_project_config(project_path, config_payload)
    echo_success(f"Provider '{meta['display_name']}' configured with model '{resolved_model}'.")
    echo_info("Configuration saved to .ce-config.json")


@provider.command("set-key", help="Store or update an API key for a provider.")
@click.argument(
    "provider_id",
    type=click.Choice(
        [p.value for p in LLMProviderType if PROVIDER_REGISTRY[p]["requires_api_key"]],
        case_sensitive=False,
    ),
)
def provider_set_key(provider_id: str) -> None:
    """Prompt for and securely store an API key."""
    meta = PROVIDER_REGISTRY[LLMProviderType(provider_id)]
    api_key = click.prompt(f"Enter API key for {meta['display_name']}", hide_input=True)
    LLM_PROVIDER_SERVICE.store_api_key(provider_id, api_key.strip())
    echo_success(f"API key for {meta['display_name']} encrypted and stored.")


@provider.command("remove-key", help="Remove a stored API key for a provider.")
@click.argument(
    "provider_id",
    type=click.Choice([p.value for p in LLMProviderType], case_sensitive=False),
)
def provider_remove_key(provider_id: str) -> None:
    """Delete a stored API key."""
    removed = LLM_PROVIDER_SERVICE.remove_api_key(provider_id)
    if removed:
        echo_success(f"API key for '{provider_id}' removed.")
    else:
        echo_warning(f"No stored API key found for '{provider_id}'.")


@provider.command("show", help="Show the current LLM provider configuration.")
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    help="Project directory.",
)
def provider_show(project_dir: str) -> None:
    """Display the resolved provider configuration."""
    project_path = Path(project_dir).resolve()
    _, config = CONFIG_SERVICE.load_project_config(project_path)

    provider_id = config.get("llm_provider")
    if not provider_id:
        echo_warning("No LLM provider configured for this project.")
        echo_info("Run 'ce provider setup' to configure one.")
        return

    click.echo("\n" + "=" * 70)
    click.echo("  LLM Provider Configuration")
    click.echo("=" * 70)
    click.echo(f"  Provider      : {provider_id}")
    configured_model = config.get("llm_model", "default")
    try:
        ptype_show = LLMProviderType(provider_id)
        default_model = PROVIDER_REGISTRY[ptype_show]["default_model"]
        is_custom = configured_model != default_model
    except ValueError:
        is_custom = False
    model_label = configured_model
    if is_custom:
        model_label += click.style(" (custom)", fg="yellow")
    click.echo(f"  Model         : {model_label}")

    custom_port = config.get("llm_custom_port")
    if custom_port:
        click.echo(f"  Custom port   : {custom_port}")

    has_key = LLM_PROVIDER_SERVICE.has_api_key(provider_id)
    try:
        ptype = LLMProviderType(provider_id)
        meta = PROVIDER_REGISTRY[ptype]
        if meta["requires_api_key"]:
            key_status = click.style("configured", fg="green") if has_key else click.style("MISSING", fg="red")
            click.echo(f"  API key       : {key_status}")
        else:
            click.echo(f"  API key       : {click.style('not required (local)', fg='cyan')}")
    except ValueError:
        click.echo("  API key       : unknown provider")

    click.echo("=" * 70 + "\n")


@provider.command("set-model", help="Set or change the LLM model for a provider in this project.")
@click.argument(
    "provider_id",
    type=click.Choice([p.value for p in LLMProviderType], case_sensitive=False),
)
@click.argument("model_name")
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    help="Project directory.",
)
def provider_set_model(provider_id: str, model_name: str, project_dir: str) -> None:
    """Set a custom model for the configured provider."""
    project_path = Path(project_dir).resolve()
    try:
        ptype = LLMProviderType(provider_id)
    except ValueError:
        echo_error(f"Unknown provider: {provider_id}")
        raise click.Abort()

    meta = PROVIDER_REGISTRY[ptype]
    model_name = model_name.strip()

    if model_name != meta["default_model"]:
        echo_info(
            f"Custom model '{model_name}' selected for {meta['display_name']}.\n"
            "   Make sure this name matches exactly what the provider's API expects.\n"
            f"   Default model for this provider: {meta['default_model']}"
        )

    config_payload = {
        "llm_provider": provider_id,
        "llm_model": model_name,
    }
    CONFIG_SERVICE.save_project_config(project_path, config_payload)
    echo_success(f"Model set to '{model_name}' for provider '{meta['display_name']}'.")


__all__ = ["provider"]
