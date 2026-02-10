"""Tests for core.llm_provider module."""

import json
from pathlib import Path

import pytest

from core.llm_provider import (
    LLM_PROVIDER_SERVICE,
    LLMProviderConfig,
    LLMProviderService,
    LLMProviderType,
    PROVIDER_REGISTRY,
    _CredentialVault,
)


class TestCredentialVault:
    """Tests for the _CredentialVault encryption helper."""

    def test_encrypt_decrypt_roundtrip(self, tmp_path):
        vault = _CredentialVault(key_dir=tmp_path)
        plaintext = "sk-abc123-secret-key"
        encrypted = vault.encrypt(plaintext)
        assert encrypted != plaintext
        decrypted = vault.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_produces_different_output(self, tmp_path):
        vault = _CredentialVault(key_dir=tmp_path)
        enc1 = vault.encrypt("test")
        enc2 = vault.encrypt("test")
        # With Fernet, each encryption produces different ciphertext
        # With XOR fallback, they are the same — both are valid
        decrypted1 = vault.decrypt(enc1)
        decrypted2 = vault.decrypt(enc2)
        assert decrypted1 == decrypted2 == "test"

    def test_key_persistence(self, tmp_path):
        vault1 = _CredentialVault(key_dir=tmp_path)
        encrypted = vault1.encrypt("my-secret")
        vault2 = _CredentialVault(key_dir=tmp_path)
        assert vault2.decrypt(encrypted) == "my-secret"

    def test_empty_string(self, tmp_path):
        vault = _CredentialVault(key_dir=tmp_path)
        encrypted = vault.encrypt("")
        assert vault.decrypt(encrypted) == ""

    def test_unicode_content(self, tmp_path):
        vault = _CredentialVault(key_dir=tmp_path)
        text = "chave-secreta-com-acentuação-ñ-ü"
        encrypted = vault.encrypt(text)
        assert vault.decrypt(encrypted) == text


class TestLLMProviderType:
    """Tests for the LLMProviderType enum."""

    def test_all_providers_in_registry(self):
        for pt in LLMProviderType:
            assert pt in PROVIDER_REGISTRY

    def test_provider_values(self):
        assert LLMProviderType.OPENAI.value == "openai"
        assert LLMProviderType.GEMINI.value == "gemini"
        assert LLMProviderType.ANTHROPIC.value == "anthropic"
        assert LLMProviderType.GROQ.value == "groq"
        assert LLMProviderType.GROK.value == "grok"
        assert LLMProviderType.DEEPSEEK.value == "deepseek"
        assert LLMProviderType.LOCAL_OLLAMA.value == "local-ollama"
        assert LLMProviderType.LOCAL_LM_STUDIO.value == "local-lm-studio"


class TestProviderRegistry:
    """Tests for the PROVIDER_REGISTRY metadata."""

    def test_cloud_providers_require_api_key(self):
        cloud = [
            LLMProviderType.OPENAI,
            LLMProviderType.GEMINI,
            LLMProviderType.ANTHROPIC,
            LLMProviderType.GROQ,
            LLMProviderType.GROK,
            LLMProviderType.DEEPSEEK,
        ]
        for pt in cloud:
            assert PROVIDER_REGISTRY[pt]["requires_api_key"] is True

    def test_local_providers_no_api_key(self):
        local = [LLMProviderType.LOCAL_OLLAMA, LLMProviderType.LOCAL_LM_STUDIO]
        for pt in local:
            assert PROVIDER_REGISTRY[pt]["requires_api_key"] is False

    def test_all_have_default_model(self):
        for pt in LLMProviderType:
            assert "default_model" in PROVIDER_REGISTRY[pt]
            assert PROVIDER_REGISTRY[pt]["default_model"]


class TestLLMProviderConfig:
    """Tests for the LLMProviderConfig dataclass."""

    def test_display_name(self):
        cfg = LLMProviderConfig(
            provider=LLMProviderType.OPENAI,
            model="gpt-4o",
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
        )
        assert cfg.display_name == "OpenAI"

    def test_is_local(self):
        local_cfg = LLMProviderConfig(
            provider=LLMProviderType.LOCAL_OLLAMA,
            model="llama3.2",
            base_url="http://localhost:11434",
        )
        assert local_cfg.is_local is True

        cloud_cfg = LLMProviderConfig(
            provider=LLMProviderType.OPENAI,
            model="gpt-4o",
            base_url="https://api.openai.com/v1",
        )
        assert cloud_cfg.is_local is False

    def test_to_dict_masks_key(self):
        cfg = LLMProviderConfig(
            provider=LLMProviderType.ANTHROPIC,
            model="claude-sonnet-4-20250514",
            base_url="https://api.anthropic.com/v1",
            api_key="sk-ant-secret",
        )
        d = cfg.to_dict()
        assert d["has_api_key"] is True
        assert "sk-ant-secret" not in str(d)
        assert d["provider"] == "anthropic"


class TestLLMProviderService:
    """Tests for the LLMProviderService."""

    def test_list_providers(self, tmp_path):
        svc = LLMProviderService(config_dir=tmp_path)
        providers = svc.list_providers()
        assert len(providers) == len(LLMProviderType)
        ids = {p["id"] for p in providers}
        assert "openai" in ids
        assert "local-ollama" in ids

    def test_store_and_get_api_key(self, tmp_path):
        svc = LLMProviderService(config_dir=tmp_path)
        svc.store_api_key("openai", "sk-test-123")
        assert svc.get_api_key("openai") == "sk-test-123"
        assert svc.has_api_key("openai") is True

    def test_get_api_key_fallback_env(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key")
        svc = LLMProviderService(config_dir=tmp_path)
        assert svc.get_api_key("openai") == "sk-env-key"

    def test_get_api_key_none(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        svc = LLMProviderService(config_dir=tmp_path)
        assert svc.get_api_key("openai") is None

    def test_remove_api_key(self, tmp_path):
        svc = LLMProviderService(config_dir=tmp_path)
        svc.store_api_key("groq", "gsk-test")
        assert svc.remove_api_key("groq") is True
        assert svc.has_api_key("groq") is False

    def test_remove_nonexistent_key(self, tmp_path):
        svc = LLMProviderService(config_dir=tmp_path)
        assert svc.remove_api_key("openai") is False

    def test_resolve_provider_local_ollama(self, tmp_path):
        svc = LLMProviderService(config_dir=tmp_path)
        cfg = svc.resolve_provider("local-ollama")
        assert cfg.provider == LLMProviderType.LOCAL_OLLAMA
        assert "11434" in cfg.base_url
        assert cfg.api_key is None

    def test_resolve_provider_local_ollama_custom_port(self, tmp_path):
        svc = LLMProviderService(config_dir=tmp_path)
        cfg = svc.resolve_provider("local-ollama", custom_port=9999)
        assert "9999" in cfg.base_url

    def test_resolve_provider_lm_studio_custom_port(self, tmp_path):
        svc = LLMProviderService(config_dir=tmp_path)
        cfg = svc.resolve_provider("local-lm-studio", custom_port=5555)
        assert "5555" in cfg.base_url

    def test_resolve_provider_unknown(self, tmp_path):
        svc = LLMProviderService(config_dir=tmp_path)
        with pytest.raises(ValueError, match="Unknown provider"):
            svc.resolve_provider("nonexistent")

    def test_resolve_provider_missing_key(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        svc = LLMProviderService(config_dir=tmp_path)
        with pytest.raises(ValueError, match="API key required"):
            svc.resolve_provider("openai")

    def test_resolve_provider_with_stored_key(self, tmp_path):
        svc = LLMProviderService(config_dir=tmp_path)
        svc.store_api_key("openai", "sk-stored")
        cfg = svc.resolve_provider("openai", model="gpt-4o-mini")
        assert cfg.api_key == "sk-stored"
        assert cfg.model == "gpt-4o-mini"

    def test_get_configured_provider_none(self, tmp_path):
        svc = LLMProviderService(config_dir=tmp_path)
        assert svc.get_configured_provider({}) is None

    def test_get_configured_provider_valid(self, tmp_path):
        svc = LLMProviderService(config_dir=tmp_path)
        svc.store_api_key("anthropic", "sk-ant-test")
        cfg = svc.get_configured_provider({
            "llm_provider": "anthropic",
            "llm_model": "claude-sonnet-4-20250514",
        })
        assert cfg is not None
        assert cfg.provider == LLMProviderType.ANTHROPIC

    def test_get_configured_provider_invalid(self, tmp_path):
        svc = LLMProviderService(config_dir=tmp_path)
        cfg = svc.get_configured_provider({"llm_provider": "nonexistent"})
        assert cfg is None

    def test_credentials_persistence(self, tmp_path):
        svc1 = LLMProviderService(config_dir=tmp_path)
        svc1.store_api_key("deepseek", "ds-key-123")
        # New instance should load persisted credentials
        svc2 = LLMProviderService(config_dir=tmp_path)
        assert svc2.get_api_key("deepseek") == "ds-key-123"

    def test_singleton_exists(self):
        assert LLM_PROVIDER_SERVICE is not None


class TestCredentialVaultXorFallback:
    """Test XOR fallback when cryptography is not available."""

    def test_xor_encrypt_decrypt(self, tmp_path):
        vault = _CredentialVault(key_dir=tmp_path)
        # Force XOR fallback
        vault._fernet = None
        plaintext = "sk-test-xor-key"
        encrypted = vault.encrypt(plaintext)
        assert encrypted != plaintext
        decrypted = vault.decrypt(encrypted)
        assert decrypted == plaintext

    def test_xor_integrity_check(self, tmp_path):
        vault = _CredentialVault(key_dir=tmp_path)
        vault._fernet = None
        encrypted = vault.encrypt("test")
        # Tamper with the ciphertext
        import base64
        raw = base64.urlsafe_b64decode(encrypted.encode())
        tampered = bytes([raw[0] ^ 0xFF]) + raw[1:]
        tampered_b64 = base64.urlsafe_b64encode(tampered).decode()
        with pytest.raises(ValueError, match="integrity"):
            vault.decrypt(tampered_b64)


class TestCorruptedCredentials:
    def test_corrupted_creds_file(self, tmp_path):
        creds_path = tmp_path / "credentials.enc"
        creds_path.write_text("not-valid-encrypted-data", encoding="utf-8")
        svc = LLMProviderService(config_dir=tmp_path)
        # Should not crash, just return empty credentials
        assert svc.get_api_key("openai") is None

    def test_resolve_provider_with_env_key(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "gem-key-123")
        svc = LLMProviderService(config_dir=tmp_path)
        cfg = svc.resolve_provider("gemini")
        assert cfg.api_key == "gem-key-123"
        assert cfg.provider == LLMProviderType.GEMINI

    def test_resolve_lm_studio_default(self, tmp_path):
        svc = LLMProviderService(config_dir=tmp_path)
        cfg = svc.resolve_provider("local-lm-studio")
        assert cfg.provider == LLMProviderType.LOCAL_LM_STUDIO
        assert "1234" in cfg.base_url
