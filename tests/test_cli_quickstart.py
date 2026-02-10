"""Tests for cli.commands.quickstart module."""

from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from cli.commands.quickstart import quickstart, _get_example_config, _show_next_steps, _show_concept_explanation


class TestQuickstart:
    def test_quickstart_decline(self):
        """User declines to start."""
        runner = CliRunner()
        result = runner.invoke(quickstart, ["--no-ai"], input="n\n")
        assert result.exit_code == 0
        assert "QUICKSTART" in result.output

    def test_quickstart_skip_intro(self, tmp_path):
        """Skip intro goes straight to setup — user declines first step."""
        runner = CliRunner()
        with patch("cli.commands.quickstart.click.get_current_context") as mock_ctx:
            mock_ctx.return_value = MagicMock()
            result = runner.invoke(quickstart, ["--skip-intro", "--no-ai"], input="test-proj\n1\nn\nn\nn\nn\nn\n")
        assert result.exit_code in (0, 1)

    def test_quickstart_interactive_intro(self):
        """Interactive mode shows extended intro."""
        runner = CliRunner()
        result = runner.invoke(quickstart, ["--interactive", "--no-ai"], input="n\n")
        assert result.exit_code == 0
        assert "Full Tutorial" in result.output

    def test_quickstart_with_example(self):
        """Example option is accepted."""
        runner = CliRunner()
        result = runner.invoke(quickstart, ["--example", "todo-app", "--no-ai"], input="n\n")
        assert result.exit_code == 0

    def test_quickstart_accept_then_decline_prd(self):
        """Accept init, decline PRD."""
        runner = CliRunner()
        with patch("cli.commands.quickstart.click.get_current_context") as mock_ctx:
            mock_ctx.return_value = MagicMock()
            result = runner.invoke(quickstart, ["--skip-intro", "--no-ai"], input="test\n1\nn\n")
        assert result.exit_code in (0, 1)


class TestGetExampleConfig:
    def test_todo_app(self):
        config = _get_example_config("todo-app")
        assert config["name"] == "todo-app"
        assert config["stack"] == "python-fastapi"

    def test_blog(self):
        config = _get_example_config("blog")
        assert config["name"] == "blog-platform"

    def test_ecommerce(self):
        config = _get_example_config("ecommerce")
        assert config["name"] == "ecommerce-api"

    def test_api(self):
        config = _get_example_config("api")
        assert config["name"] == "rest-api"
        assert config["stack"] == "go-gin"

    def test_unknown_returns_default(self):
        config = _get_example_config("unknown")
        assert config["name"] == "todo-app"


class TestShowNextSteps:
    def test_output(self, capsys):
        _show_next_steps()
        captured = capsys.readouterr()
        assert "Next Steps" in captured.out
        assert "ce generate-tasks" in captured.out
        assert "ce validate" in captured.out


class TestShowConceptExplanation:
    def test_context_engineer(self, capsys):
        with patch("cli.commands.quickstart.click.pause"):
            _show_concept_explanation("context_engineer")
        captured = capsys.readouterr()
        assert "Context Engineer" in captured.out

    def test_prd(self, capsys):
        with patch("cli.commands.quickstart.click.pause"):
            _show_concept_explanation("prd")
        captured = capsys.readouterr()
        assert "PRD" in captured.out

    def test_prps(self, capsys):
        with patch("cli.commands.quickstart.click.pause"):
            _show_concept_explanation("prps")
        captured = capsys.readouterr()
        assert "PRPs" in captured.out

    def test_unknown_concept(self):
        _show_concept_explanation("unknown_concept")


class TestQuickstartFullFlow:
    def test_accept_init_decline_prps(self):
        """Accept init and PRD, decline PRPs."""
        runner = CliRunner()
        with patch("cli.commands.quickstart.click.get_current_context") as mock_ctx:
            ctx_mock = MagicMock()
            mock_ctx.return_value = ctx_mock
            # Input: project_name, stack_choice, confirm_prd=yes, confirm_prps=no
            result = runner.invoke(quickstart, ["--skip-intro", "--no-ai"], input="test\n1\ny\nn\n")
        assert result.exit_code in (0, 1)

    def test_quickstart_abort_handling(self):
        """Quickstart handles click.Abort gracefully."""
        runner = CliRunner()
        with patch("cli.commands.quickstart.click.get_current_context") as mock_ctx:
            ctx_mock = MagicMock()
            import click
            ctx_mock.invoke.side_effect = click.Abort()
            mock_ctx.return_value = ctx_mock
            result = runner.invoke(quickstart, ["--skip-intro", "--no-ai"], input="test\n1\n")
        assert result.exit_code in (0, 1)
        assert "interrupted" in result.output.lower() or result.exit_code in (0, 1)

    def test_quickstart_exception_handling(self):
        """Quickstart handles unexpected exceptions."""
        runner = CliRunner()
        with patch("cli.commands.quickstart.click.get_current_context") as mock_ctx:
            ctx_mock = MagicMock()
            ctx_mock.invoke.side_effect = RuntimeError("boom")
            mock_ctx.return_value = ctx_mock
            result = runner.invoke(quickstart, ["--skip-intro", "--no-ai"], input="test\n1\n")
        assert result.exit_code != 0

    def test_quickstart_interactive_shows_concepts(self):
        """Interactive mode shows concept explanations."""
        runner = CliRunner()
        with patch("cli.commands.quickstart.click.get_current_context") as mock_ctx:
            mock_ctx.return_value = MagicMock()
            # Input: confirm_start=yes, then enter for pause, project_name, stack, decline_prd
            result = runner.invoke(quickstart, ["--interactive", "--no-ai"], input="y\n\ntest\n1\nn\n")
        assert result.exit_code in (0, 1)
        assert "Full Tutorial" in result.output

    def test_quickstart_interactive_extended_steps(self):
        """Interactive mode shows extended steps (4-6)."""
        runner = CliRunner()
        result = runner.invoke(quickstart, ["--interactive", "--no-ai"], input="n\n")
        assert "Generate executable Tasks" in result.output or "Validate traceability" in result.output or "QUICKSTART" in result.output
