"""Tests for cli.commands.patterns module."""

from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from cli.commands.patterns import patterns, _render_pattern_card


class TestRenderPatternCard:
    def test_basic(self):
        pattern = {
            "pattern_id": "auth-jwt",
            "name": "JWT Auth",
            "category": "authentication",
            "complexity": "medium",
            "stack": ["python-fastapi"],
            "tags": ["auth", "jwt"],
            "content": "# JWT\nImplement JWT auth",
        }
        _render_pattern_card(pattern)

    def test_with_content(self):
        pattern = {
            "pattern_id": "auth-jwt",
            "name": "JWT Auth",
            "category": "authentication",
            "complexity": "medium",
            "stack": [],
            "tags": [],
            "content": "# JWT\nLine 1\nLine 2",
        }
        _render_pattern_card(pattern, show_content=True)

    def test_empty_pattern(self):
        _render_pattern_card({})


class TestPatternsList:
    def test_list_no_results(self):
        runner = CliRunner()
        mock_engine = MagicMock()
        mock_engine.pattern_library.search.return_value = []
        with patch("cli.commands.patterns.create_engine", return_value=mock_engine):
            result = runner.invoke(patterns, ["list", "--no-ai"])
        assert result.exit_code == 0
        assert "No patterns found" in result.output

    def test_list_with_results(self):
        runner = CliRunner()
        mock_engine = MagicMock()
        mock_engine.pattern_library.search.return_value = [
            {"pattern_id": "p1", "name": "Pattern 1", "category": "api", "complexity": "low", "stack": ["python"], "tags": ["rest"]},
        ]
        with patch("cli.commands.patterns.create_engine", return_value=mock_engine):
            result = runner.invoke(patterns, ["list", "--no-ai"])
        assert result.exit_code == 0
        assert "p1" in result.output

    def test_list_json_format(self):
        runner = CliRunner()
        mock_engine = MagicMock()
        mock_engine.pattern_library.search.return_value = [
            {"pattern_id": "p1", "name": "Pattern 1"},
        ]
        with patch("cli.commands.patterns.create_engine", return_value=mock_engine):
            result = runner.invoke(patterns, ["list", "--no-ai", "--format", "json"])
        assert result.exit_code == 0
        assert '"count"' in result.output

    def test_list_with_filters(self):
        runner = CliRunner()
        mock_engine = MagicMock()
        mock_engine.pattern_library.search.return_value = []
        with patch("cli.commands.patterns.create_engine", return_value=mock_engine):
            result = runner.invoke(patterns, [
                "list", "--no-ai",
                "--category", "authentication",
                "--stack", "python-fastapi",
                "--complexity", "medium",
                "--tag", "jwt",
            ])
        assert result.exit_code == 0


class TestPatternsShow:
    def test_show_found(self):
        runner = CliRunner()
        mock_engine = MagicMock()
        mock_engine.pattern_library.get_pattern.return_value = {
            "pattern_id": "auth-jwt", "name": "JWT", "category": "auth",
            "complexity": "medium", "stack": [], "tags": [], "content": "# JWT",
        }
        with patch("cli.commands.patterns.create_engine", return_value=mock_engine):
            result = runner.invoke(patterns, ["show", "auth-jwt", "--no-ai"])
        assert result.exit_code == 0
        assert "auth-jwt" in result.output

    def test_show_not_found(self):
        runner = CliRunner()
        mock_engine = MagicMock()
        mock_engine.pattern_library.get_pattern.return_value = None
        with patch("cli.commands.patterns.create_engine", return_value=mock_engine):
            result = runner.invoke(patterns, ["show", "nonexistent", "--no-ai"])
        assert result.exit_code == 0
        assert "not found" in result.output


class TestPatternsSuggest:
    def test_suggest_no_stack(self, tmp_path):
        runner = CliRunner()
        with patch("cli.commands.patterns.ProjectAnalyzer") as MockAnalyzer:
            instance = MockAnalyzer.return_value
            instance.build_assistant_context.return_value = {"pattern_context": {"stack": []}}
            result = runner.invoke(patterns, ["suggest", "--project-dir", str(tmp_path), "--no-ai"])
        assert result.exit_code == 0
        assert "Stack not detected" in result.output

    def test_suggest_with_results(self, tmp_path):
        runner = CliRunner()
        mock_engine = MagicMock()
        mock_engine.pattern_library.suggest_patterns.return_value = [
            {"pattern_id": "p1", "name": "P1", "category": "api", "complexity": "low", "stack": ["python"], "tags": []},
        ]
        with patch("cli.commands.patterns.ProjectAnalyzer") as MockAnalyzer, \
             patch("cli.commands.patterns.create_engine", return_value=mock_engine):
            instance = MockAnalyzer.return_value
            instance.build_assistant_context.return_value = {
                "pattern_context": {"stack": ["python-fastapi"]},
            }
            result = runner.invoke(patterns, ["suggest", "--project-dir", str(tmp_path), "--no-ai"])
        assert result.exit_code == 0
        assert "p1" in result.output
