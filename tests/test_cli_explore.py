"""Tests for cli.commands.explore module."""

from click.testing import CliRunner

from cli.commands.explore import explore


class TestExplore:
    def test_explore_all(self):
        runner = CliRunner()
        result = runner.invoke(explore)
        assert result.exit_code == 0
        assert "EXPLORADOR DE COMANDOS" in result.output

    def test_explore_category_geracao(self):
        runner = CliRunner()
        result = runner.invoke(explore, ["--category", "geração"])
        assert result.exit_code == 0
        assert "init" in result.output

    def test_explore_category_validacao(self):
        runner = CliRunner()
        result = runner.invoke(explore, ["--category", "validação"])
        assert result.exit_code == 0
        assert "validate" in result.output

    def test_explore_category_devops(self):
        runner = CliRunner()
        result = runner.invoke(explore, ["--category", "devops"])
        assert result.exit_code == 0

    def test_explore_category_not_found(self):
        runner = CliRunner()
        result = runner.invoke(explore, ["--category", "nonexistent"])
        assert result.exit_code == 0
        assert "não encontrada" in result.output
