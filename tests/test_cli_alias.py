"""Tests for cli.commands.alias module."""

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from cli.commands.alias import alias


class TestAlias:
    def test_list_default(self, tmp_path):
        runner = CliRunner()
        with patch.object(Path, "home", return_value=tmp_path):
            result = runner.invoke(alias, ["list"])
        assert result.exit_code == 0
        assert "Available Aliases" in result.output

    def test_list_no_action(self, tmp_path):
        runner = CliRunner()
        with patch.object(Path, "home", return_value=tmp_path):
            result = runner.invoke(alias)
        assert result.exit_code == 0
        assert "Available Aliases" in result.output

    def test_add_alias(self, tmp_path):
        runner = CliRunner()
        with patch.object(Path, "home", return_value=tmp_path):
            result = runner.invoke(alias, ["add", "test-alias", "status"])
        assert result.exit_code == 0
        assert "created" in result.output

    def test_add_alias_missing_command(self, tmp_path):
        runner = CliRunner()
        with patch.object(Path, "home", return_value=tmp_path):
            result = runner.invoke(alias, ["add", "test-alias"])
        assert result.exit_code != 0

    def test_remove_alias(self, tmp_path):
        runner = CliRunner()
        config_dir = tmp_path / ".context-engineer"
        config_dir.mkdir(parents=True)
        (config_dir / "aliases.json").write_text(json.dumps({"myalias": "status"}), encoding="utf-8")
        with patch.object(Path, "home", return_value=tmp_path):
            result = runner.invoke(alias, ["remove", "myalias"])
        assert result.exit_code == 0
        assert "removed" in result.output

    def test_remove_default_alias(self, tmp_path):
        runner = CliRunner()
        with patch.object(Path, "home", return_value=tmp_path):
            result = runner.invoke(alias, ["remove", "gp"])
        assert result.exit_code == 0
        assert "default alias" in result.output

    def test_remove_nonexistent_alias(self, tmp_path):
        runner = CliRunner()
        with patch.object(Path, "home", return_value=tmp_path):
            result = runner.invoke(alias, ["remove", "nonexistent"])
        assert result.exit_code == 0
        assert "not found" in result.output

    def test_remove_alias_missing_name(self, tmp_path):
        runner = CliRunner()
        with patch.object(Path, "home", return_value=tmp_path):
            result = runner.invoke(alias, ["remove"])
        assert result.exit_code != 0
