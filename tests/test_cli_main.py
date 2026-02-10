"""Tests for cli.main module."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from cli.main import cli, _install_shell_completion


class TestCli:
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Context Engineer" in result.output

    def test_verbose(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--verbose", "--help"])
        assert result.exit_code == 0

    def test_quiet(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--quiet", "--help"])
        assert result.exit_code == 0

    def test_log_level(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--log-level", "DEBUG", "--help"])
        assert result.exit_code == 0

    def test_commands_registered(self):
        """All expected commands should be registered."""
        expected = [
            "init", "generate-prd", "generate-prps", "generate-tasks",
            "validate", "status", "checklist", "assist", "wizard",
            "report", "doctor", "explore", "quickstart",
            "patterns", "marketplace", "provider",
        ]
        for cmd in expected:
            assert cmd in cli.commands, f"Command '{cmd}' not registered"


class TestInstallShellCompletion:
    def _patch_expanduser(self, monkeypatch, tmp_path, mapping):
        """Redirect expanduser so ~ paths land in tmp_path."""
        original = Path.expanduser

        def fake_expanduser(self_path):
            s = str(self_path)
            for src, dst in mapping.items():
                if s == src:
                    return dst
            return original(self_path)

        monkeypatch.setattr(Path, "expanduser", fake_expanduser)

    def test_bash_new_file(self, tmp_path, monkeypatch):
        bashrc = tmp_path / ".bashrc"
        self._patch_expanduser(monkeypatch, tmp_path, {"~/.bashrc": bashrc})
        _install_shell_completion("bash")
        assert bashrc.exists()
        assert "_CE_COMPLETE" in bashrc.read_text()

    def test_bash_already_installed(self, tmp_path, monkeypatch):
        bashrc = tmp_path / ".bashrc"
        bashrc.write_text('eval "$(_CE_COMPLETE=bash_source ce)"\n')
        self._patch_expanduser(monkeypatch, tmp_path, {"~/.bashrc": bashrc})
        _install_shell_completion("bash")

    def test_bash_append(self, tmp_path, monkeypatch):
        bashrc = tmp_path / ".bashrc"
        bashrc.write_text("# existing config\n")
        self._patch_expanduser(monkeypatch, tmp_path, {"~/.bashrc": bashrc})
        _install_shell_completion("bash")
        assert "_CE_COMPLETE" in bashrc.read_text()

    def test_zsh(self, tmp_path, monkeypatch):
        zshrc = tmp_path / ".zshrc"
        self._patch_expanduser(monkeypatch, tmp_path, {"~/.zshrc": zshrc})
        _install_shell_completion("zsh")
        assert zshrc.exists()

    def test_fish(self, tmp_path, monkeypatch):
        fish_file = tmp_path / "ce.fish"
        self._patch_expanduser(monkeypatch, tmp_path, {"~/.config/fish/completions/ce.fish": fish_file})
        _install_shell_completion("fish")
        assert fish_file.exists()

    def test_powershell(self, tmp_path, monkeypatch):
        ps_profile = tmp_path / "profile.ps1"
        self._patch_expanduser(monkeypatch, tmp_path, {"$PROFILE": ps_profile})
        _install_shell_completion("powershell")
        assert ps_profile.exists()
