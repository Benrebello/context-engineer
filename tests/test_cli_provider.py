"""Tests for cli.commands.provider module."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from cli.commands.provider import provider


class TestProviderList:
    def test_list(self):
        runner = CliRunner()
        result = runner.invoke(provider, ["list"])
        assert result.exit_code == 0
        assert "Supported LLM Providers" in result.output


class TestProviderSetup:
    def test_setup_with_provider_id(self, tmp_path):
        runner = CliRunner()
        with patch("cli.commands.provider.LLM_PROVIDER_SERVICE") as mock_svc, \
             patch("cli.commands.provider.CONFIG_SERVICE") as mock_cfg:
            mock_svc.has_api_key.return_value = False
            # Input: API key, use default model? y
            result = runner.invoke(provider, [
                "setup",
                "--provider-id", "openai",
                "--project-dir", str(tmp_path),
            ], input="sk-test-key\ny\n")
        assert result.exit_code == 0
        assert "configured" in result.output

    def test_setup_local_ollama(self, tmp_path):
        runner = CliRunner()
        with patch("cli.commands.provider.LLM_PROVIDER_SERVICE") as mock_svc, \
             patch("cli.commands.provider.CONFIG_SERVICE"):
            mock_svc.has_api_key.return_value = False
            # Input: use default model? y, use default port? y
            result = runner.invoke(provider, [
                "setup",
                "--provider-id", "local-ollama",
                "--project-dir", str(tmp_path),
            ], input="y\ny\n")
        assert result.exit_code == 0

    def test_setup_interactive_selection(self, tmp_path):
        runner = CliRunner()
        with patch("cli.commands.provider.LLM_PROVIDER_SERVICE") as mock_svc, \
             patch("cli.commands.provider.CONFIG_SERVICE"):
            mock_svc.has_api_key.return_value = False
            # Input: select provider 1 (openai), API key, use default model? y
            result = runner.invoke(provider, [
                "setup",
                "--project-dir", str(tmp_path),
            ], input="1\nsk-test\ny\n")
        assert result.exit_code == 0

    def test_setup_invalid_provider(self, tmp_path):
        runner = CliRunner()
        with patch("cli.commands.provider.LLM_PROVIDER_SERVICE"), \
             patch("cli.commands.provider.CONFIG_SERVICE"):
            result = runner.invoke(provider, [
                "setup",
                "--provider-id", "nonexistent",
                "--project-dir", str(tmp_path),
            ])
        assert result.exit_code != 0


class TestProviderSetKey:
    def test_set_key(self):
        runner = CliRunner()
        with patch("cli.commands.provider.LLM_PROVIDER_SERVICE") as mock_svc:
            result = runner.invoke(provider, ["set-key", "openai"], input="sk-new-key\n")
        assert result.exit_code == 0
        assert "encrypted" in result.output


class TestProviderRemoveKey:
    def test_remove_key_exists(self):
        runner = CliRunner()
        with patch("cli.commands.provider.LLM_PROVIDER_SERVICE") as mock_svc:
            mock_svc.remove_api_key.return_value = True
            result = runner.invoke(provider, ["remove-key", "openai"])
        assert result.exit_code == 0
        assert "removed" in result.output

    def test_remove_key_not_found(self):
        runner = CliRunner()
        with patch("cli.commands.provider.LLM_PROVIDER_SERVICE") as mock_svc:
            mock_svc.remove_api_key.return_value = False
            result = runner.invoke(provider, ["remove-key", "openai"])
        assert result.exit_code == 0
        assert "No stored" in result.output


class TestProviderShow:
    def test_show_configured(self, tmp_path):
        runner = CliRunner()
        with patch("cli.commands.provider.CONFIG_SERVICE") as mock_cfg, \
             patch("cli.commands.provider.LLM_PROVIDER_SERVICE") as mock_svc:
            mock_cfg.load_project_config.return_value = (tmp_path, {
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
            })
            mock_svc.has_api_key.return_value = True
            result = runner.invoke(provider, ["show", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "openai" in result.output

    def test_show_not_configured(self, tmp_path):
        runner = CliRunner()
        with patch("cli.commands.provider.CONFIG_SERVICE") as mock_cfg:
            mock_cfg.load_project_config.return_value = (tmp_path, {})
            result = runner.invoke(provider, ["show", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "No LLM provider configured" in result.output

    def test_show_with_custom_port(self, tmp_path):
        runner = CliRunner()
        with patch("cli.commands.provider.CONFIG_SERVICE") as mock_cfg, \
             patch("cli.commands.provider.LLM_PROVIDER_SERVICE") as mock_svc:
            mock_cfg.load_project_config.return_value = (tmp_path, {
                "llm_provider": "local-ollama",
                "llm_model": "llama3",
                "llm_custom_port": 11434,
            })
            mock_svc.has_api_key.return_value = False
            result = runner.invoke(provider, ["show", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "11434" in result.output

    def test_show_custom_model_indicator(self, tmp_path):
        """Custom model should display '(custom)' indicator."""
        runner = CliRunner()
        with patch("cli.commands.provider.CONFIG_SERVICE") as mock_cfg, \
             patch("cli.commands.provider.LLM_PROVIDER_SERVICE") as mock_svc:
            mock_cfg.load_project_config.return_value = (tmp_path, {
                "llm_provider": "openai",
                "llm_model": "gpt-4-turbo",
            })
            mock_svc.has_api_key.return_value = True
            result = runner.invoke(provider, ["show", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "gpt-4-turbo" in result.output
        assert "custom" in result.output

    def test_show_default_model_no_indicator(self, tmp_path):
        """Default model should NOT display '(custom)' indicator."""
        runner = CliRunner()
        with patch("cli.commands.provider.CONFIG_SERVICE") as mock_cfg, \
             patch("cli.commands.provider.LLM_PROVIDER_SERVICE") as mock_svc:
            mock_cfg.load_project_config.return_value = (tmp_path, {
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
            })
            mock_svc.has_api_key.return_value = True
            result = runner.invoke(provider, ["show", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "gpt-4o" in result.output
        assert "custom" not in result.output


class TestProviderSetModel:
    def test_set_model_custom(self, tmp_path):
        """Set a custom model — should show API name warning."""
        runner = CliRunner()
        with patch("cli.commands.provider.CONFIG_SERVICE") as mock_cfg:
            result = runner.invoke(provider, [
                "set-model", "openai", "gpt-4-turbo",
                "--project-dir", str(tmp_path),
            ])
        assert result.exit_code == 0
        assert "gpt-4-turbo" in result.output
        assert "Model set to" in result.output
        assert "matches exactly" in result.output

    def test_set_model_default(self, tmp_path):
        """Set the default model — no warning needed."""
        runner = CliRunner()
        with patch("cli.commands.provider.CONFIG_SERVICE") as mock_cfg:
            result = runner.invoke(provider, [
                "set-model", "openai", "gpt-4o",
                "--project-dir", str(tmp_path),
            ])
        assert result.exit_code == 0
        assert "Model set to" in result.output
        assert "must match exactly" not in result.output

    def test_set_model_local_ollama(self, tmp_path):
        """Set a custom model for local Ollama."""
        runner = CliRunner()
        with patch("cli.commands.provider.CONFIG_SERVICE") as mock_cfg:
            result = runner.invoke(provider, [
                "set-model", "local-ollama", "codellama:13b",
                "--project-dir", str(tmp_path),
            ])
        assert result.exit_code == 0
        assert "codellama:13b" in result.output

    def test_set_model_persists_config(self, tmp_path):
        """Verify config is saved with correct payload."""
        runner = CliRunner()
        with patch("cli.commands.provider.CONFIG_SERVICE") as mock_cfg:
            result = runner.invoke(provider, [
                "set-model", "gemini", "gemini-1.5-pro",
                "--project-dir", str(tmp_path),
            ])
        mock_cfg.save_project_config.assert_called_once()
        call_args = mock_cfg.save_project_config.call_args
        payload = call_args[0][1]
        assert payload["llm_provider"] == "gemini"
        assert payload["llm_model"] == "gemini-1.5-pro"


class TestProviderSetupCustomModel:
    def test_setup_custom_model_interactive(self, tmp_path):
        """User declines default model and types a custom one — should see warning."""
        runner = CliRunner()
        with patch("cli.commands.provider.LLM_PROVIDER_SERVICE") as mock_svc, \
             patch("cli.commands.provider.CONFIG_SERVICE"):
            mock_svc.has_api_key.return_value = False
            # Input: API key, use default model? n, custom model name
            result = runner.invoke(provider, [
                "setup",
                "--provider-id", "openai",
                "--project-dir", str(tmp_path),
            ], input="sk-test-key\nn\ngpt-4-turbo\n")
        assert result.exit_code == 0
        assert "must match exactly" in result.output
        assert "gpt-4-turbo" in result.output

    def test_setup_custom_model_via_flag(self, tmp_path):
        """Pass --model flag with non-default model — should see warning."""
        runner = CliRunner()
        with patch("cli.commands.provider.LLM_PROVIDER_SERVICE") as mock_svc, \
             patch("cli.commands.provider.CONFIG_SERVICE"):
            mock_svc.has_api_key.return_value = False
            result = runner.invoke(provider, [
                "setup",
                "--provider-id", "openai",
                "--model", "o1-preview",
                "--project-dir", str(tmp_path),
            ], input="sk-test-key\n")
        assert result.exit_code == 0
        assert "custom model" in result.output.lower() or "o1-preview" in result.output


class TestProviderListTip:
    def test_list_shows_set_model_tip(self):
        """Provider list should show tip about set-model command."""
        runner = CliRunner()
        result = runner.invoke(provider, ["list"])
        assert result.exit_code == 0
        assert "set-model" in result.output
