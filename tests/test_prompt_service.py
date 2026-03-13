"""Tests for core.prompt_service module."""

from unittest.mock import patch, MagicMock

import pytest
import click

from core.prompt_service import PromptService


@pytest.fixture()
def service():
    return PromptService()


class TestPromptMultiline:
    def test_default_on_empty(self, service):
        with patch("builtins.input", side_effect=["", ""]):
            result = service.prompt_multiline("Enter:", default="fallback")
        assert result == "fallback"

    def test_multiline_input(self, service):
        with patch("builtins.input", side_effect=["line1", "line2", ""]):
            result = service.prompt_multiline("Enter:")
        assert result == "line1\nline2"

    def test_eof(self, service):
        with patch("builtins.input", side_effect=["data", EOFError]):
            result = service.prompt_multiline("Enter:")
        assert result == "data"

    def test_keyboard_interrupt(self, service):
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with pytest.raises(click.Abort):
                service.prompt_multiline("Enter:")


class TestPromptUserStory:
    def test_prompt_user_story(self, service):
        with patch("click.prompt") as mock_prompt, \
             patch.object(service, "prompt_multiline", return_value="Dado que estou logado"):
            mock_prompt.side_effect = ["admin", "gerenciar usuários", "controle de acesso"]
            result = service.prompt_user_story()
        assert result["persona"] == "admin"
        assert result["acao"] == "gerenciar usuários"
        assert result["valor"] == "controle de acesso"
        assert len(result["criterios_aceitacao"]) >= 1


class TestPromptPrdIdea:
    def test_prompt_prd_idea(self, service):
        with patch.object(service, "prompt_multiline") as mock_ml:
            mock_ml.side_effect = [
                "App de tarefas",      # visao
                "Mercado produtividade",  # contexto
                "Desenvolvedores",      # usuarios
                "LGPD",                 # restricoes
                "Login\nCRUD tarefas",  # requisitos
            ]
            result = service.prompt_prd_idea()
        assert result["visao"] == "App de tarefas"
        assert result["contexto"] == "Mercado produtividade"
        assert len(result["requisitos_funcionais"]) == 2


class TestPromptPrpInfo:
    def test_prompt_prp_info_no_context(self, service):
        with patch("click.confirm", return_value=False), \
             patch("click.prompt", return_value="MoSCoW"):
            result = service.prompt_prp_info()
        assert result["contexto_adicional"] == ""
        assert result["metodo_priorizacao"] == "MoSCoW"

    def test_prompt_prp_info_with_context(self, service):
        with patch("click.confirm", return_value=True), \
             patch("click.prompt", return_value="RICE"), \
             patch.object(service, "prompt_multiline", return_value="Usar microserviços"):
            result = service.prompt_prp_info()
        assert result["contexto_adicional"] == "Usar microserviços"
        assert result["metodo_priorizacao"] == "RICE"


class TestPromptServiceInit:
    def test_init(self):
        svc = PromptService()
        assert svc is not None
