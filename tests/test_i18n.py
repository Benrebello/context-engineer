"""Tests for core.i18n module."""

import json
from pathlib import Path

import pytest

from core.i18n import I18n, get_i18n, t, DEFAULT_LANGUAGE, TRANSLATIONS


class TestI18n:
    def test_default_language(self):
        i18n = I18n()
        assert i18n.language == DEFAULT_LANGUAGE

    def test_explicit_language(self):
        i18n = I18n(language="pt-br")
        assert i18n.language == "pt-br"

    def test_normalize_en(self):
        i18n = I18n(language="en")
        assert i18n.language == "en-us"

    def test_normalize_english(self):
        i18n = I18n(language="English")
        assert i18n.language == "en-us"

    def test_normalize_pt(self):
        i18n = I18n(language="pt")
        assert i18n.language == "pt-br"

    def test_normalize_portuguese(self):
        i18n = I18n(language="portuguese")
        assert i18n.language == "pt-br"

    def test_normalize_unknown_falls_back(self):
        i18n = I18n(language="fr")
        assert i18n.language == DEFAULT_LANGUAGE

    def test_translate_known_key(self):
        i18n = I18n(language="en-us")
        result = i18n.t("success")
        assert result == "Success"

    def test_translate_unknown_key(self):
        i18n = I18n()
        result = i18n.t("nonexistent.key")
        assert result == "nonexistent.key"

    def test_translate_with_params(self):
        i18n = I18n(language="en-us")
        result = i18n.t("cmd.init.success", name="test", path="/tmp")
        assert "test" in result
        assert "/tmp" in result

    def test_translate_with_bad_params(self):
        i18n = I18n(language="en-us")
        result = i18n.t("cmd.init.success", wrong_param="x")
        # Should not crash, returns template as-is
        assert isinstance(result, str)

    def test_set_language(self):
        i18n = I18n()
        i18n.set_language("pt-br")
        assert i18n.language == "pt-br"

    def test_resolve_from_config(self, tmp_path):
        config = {"language": "pt-br"}
        (tmp_path / ".ce-config.json").write_text(json.dumps(config), encoding="utf-8")
        i18n = I18n(project_dir=tmp_path)
        assert i18n.language == "pt-br"

    def test_resolve_from_config_missing(self, tmp_path):
        i18n = I18n(project_dir=tmp_path)
        assert i18n.language == DEFAULT_LANGUAGE

    def test_resolve_explicit_overrides_config(self, tmp_path):
        config = {"language": "pt-br"}
        (tmp_path / ".ce-config.json").write_text(json.dumps(config), encoding="utf-8")
        i18n = I18n(language="en-us", project_dir=tmp_path)
        assert i18n.language == "en-us"

    def test_pt_br_translations(self):
        i18n = I18n(language="pt-br")
        result = i18n.t("success")
        assert result == "Sucesso"


class TestGetI18n:
    def test_default(self):
        i18n = get_i18n()
        assert i18n is not None
        assert i18n.language == DEFAULT_LANGUAGE

    def test_with_language(self):
        i18n = get_i18n(language="pt-br")
        assert i18n.language == "pt-br"

    def test_with_project_dir(self, tmp_path):
        i18n = get_i18n(project_dir=tmp_path)
        assert i18n.language == DEFAULT_LANGUAGE


class TestShorthandT:
    def test_t_function(self):
        result = t("success")
        assert isinstance(result, str)
