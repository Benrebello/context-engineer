"""
LLM Provider service for Context Engineer.

Manages multiple LLM provider configurations with encrypted API key storage.
Supports OpenAI, Gemini, Anthropic, GROQ, GROK, Deepseek, and local providers
(Ollama, LM Studio).
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import platform
import secrets
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_KEYFILE_NAME = ".ce-keyring"
_CREDENTIALS_FILENAME = ".ce-credentials.enc"
_DEFAULT_OLLAMA_PORT = 11434
_DEFAULT_LM_STUDIO_PORT = 1234


class LLMProviderType(str, Enum):
    """Supported LLM provider identifiers."""

    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    GROK = "grok"
    DEEPSEEK = "deepseek"
    LOCAL_OLLAMA = "local-ollama"
    LOCAL_LM_STUDIO = "local-lm-studio"


# Metadata for each provider (display name, default model, requires API key)
PROVIDER_REGISTRY: dict[str, dict[str, Any]] = {
    LLMProviderType.OPENAI: {
        "display_name": "OpenAI",
        "default_model": "gpt-4o",
        "requires_api_key": True,
        "base_url": "https://api.openai.com/v1",
        "env_var": "OPENAI_API_KEY",
    },
    LLMProviderType.GEMINI: {
        "display_name": "Google Gemini",
        "default_model": "gemini-2.0-flash",
        "requires_api_key": True,
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "env_var": "GEMINI_API_KEY",
    },
    LLMProviderType.ANTHROPIC: {
        "display_name": "Anthropic (Claude)",
        "default_model": "claude-sonnet-4-20250514",
        "requires_api_key": True,
        "base_url": "https://api.anthropic.com/v1",
        "env_var": "ANTHROPIC_API_KEY",
    },
    LLMProviderType.GROQ: {
        "display_name": "GROQ",
        "default_model": "llama-3.3-70b-versatile",
        "requires_api_key": True,
        "base_url": "https://api.groq.com/openai/v1",
        "env_var": "GROQ_API_KEY",
    },
    LLMProviderType.GROK: {
        "display_name": "xAI (Grok)",
        "default_model": "grok-3",
        "requires_api_key": True,
        "base_url": "https://api.x.ai/v1",
        "env_var": "XAI_API_KEY",
    },
    LLMProviderType.DEEPSEEK: {
        "display_name": "DeepSeek",
        "default_model": "deepseek-chat",
        "requires_api_key": True,
        "base_url": "https://api.deepseek.com/v1",
        "env_var": "DEEPSEEK_API_KEY",
    },
    LLMProviderType.LOCAL_OLLAMA: {
        "display_name": "Ollama (Local)",
        "default_model": "llama3.2",
        "requires_api_key": False,
        "base_url": f"http://localhost:{_DEFAULT_OLLAMA_PORT}",
        "env_var": None,
    },
    LLMProviderType.LOCAL_LM_STUDIO: {
        "display_name": "LM Studio (Local)",
        "default_model": "local-model",
        "requires_api_key": False,
        "base_url": f"http://localhost:{_DEFAULT_LM_STUDIO_PORT}/v1",
        "env_var": None,
    },
}


# ---------------------------------------------------------------------------
# Encryption helpers (Fernet-compatible using stdlib only)
# ---------------------------------------------------------------------------


class _CredentialVault:
    """
    Encrypts and decrypts API tokens using a machine-local key derived from
    a random secret stored in the user's home directory with restricted
    permissions.  Uses AES-like XOR obfuscation with HMAC integrity when
    the ``cryptography`` package is unavailable, and full Fernet encryption
    when it is installed.
    """

    def __init__(self, key_dir: Path | None = None) -> None:
        self._key_dir = key_dir or Path.home() / ".config" / "context-engineer"
        self._key_dir.mkdir(parents=True, exist_ok=True)
        self._key_path = self._key_dir / _KEYFILE_NAME
        self._fernet: Any | None = None
        self._secret_bytes: bytes = self._load_or_create_key()

    # -- key management -----------------------------------------------------

    def _load_or_create_key(self) -> bytes:
        """Load existing key or generate a new one with restricted permissions."""
        if self._key_path.exists():
            raw = self._key_path.read_bytes()
        else:
            raw = secrets.token_bytes(32)
            self._key_path.write_bytes(raw)
            # Restrict permissions (owner-only read/write)
            if platform.system() != "Windows":
                self._key_path.chmod(0o600)
        # Try to use Fernet for real encryption
        try:
            from cryptography.fernet import Fernet  # type: ignore[import-untyped]

            fernet_key = base64.urlsafe_b64encode(raw[:32])
            self._fernet = Fernet(fernet_key)
        except ImportError:
            self._fernet = None
        return raw

    # -- encrypt / decrypt --------------------------------------------------

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string and return a base64-encoded ciphertext."""
        if self._fernet is not None:
            return self._fernet.encrypt(plaintext.encode()).decode()
        # Fallback: XOR with HMAC integrity tag
        data = plaintext.encode()
        key_stream = self._derive_stream(len(data))
        cipher = bytes(a ^ b for a, b in zip(data, key_stream))
        tag = self._hmac(cipher)
        payload = tag + cipher
        return base64.urlsafe_b64encode(payload).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a base64-encoded ciphertext back to plaintext."""
        if self._fernet is not None:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        payload = base64.urlsafe_b64decode(ciphertext.encode())
        tag, cipher = payload[:32], payload[32:]
        expected_tag = self._hmac(cipher)
        if not secrets.compare_digest(tag, expected_tag):
            msg = "Credential integrity check failed — key may have changed"
            raise ValueError(msg)
        key_stream = self._derive_stream(len(cipher))
        data = bytes(a ^ b for a, b in zip(cipher, key_stream))
        return data.decode()

    # -- internal helpers ---------------------------------------------------

    def _derive_stream(self, length: int) -> bytes:
        """Derive a repeatable key stream from the secret."""
        stream = b""
        counter = 0
        while len(stream) < length:
            stream += hashlib.sha256(self._secret_bytes + counter.to_bytes(4, "big")).digest()
            counter += 1
        return stream[:length]

    def _hmac(self, data: bytes) -> bytes:
        """Compute HMAC-SHA256 over *data* using the stored secret."""
        import hmac as _hmac

        return _hmac.new(self._secret_bytes, data, hashlib.sha256).digest()


# ---------------------------------------------------------------------------
# Provider configuration dataclass
# ---------------------------------------------------------------------------


@dataclass
class LLMProviderConfig:
    """Resolved configuration for a single LLM provider."""

    provider: LLMProviderType
    model: str
    base_url: str
    api_key: str | None = None
    custom_port: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        """Human-readable provider name."""
        meta = PROVIDER_REGISTRY.get(self.provider, {})
        return meta.get("display_name", self.provider.value)

    @property
    def is_local(self) -> bool:
        """Whether this provider runs locally."""
        return self.provider in {LLMProviderType.LOCAL_OLLAMA, LLMProviderType.LOCAL_LM_STUDIO}

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary (API key is masked)."""
        return {
            "provider": self.provider.value,
            "model": self.model,
            "base_url": self.base_url,
            "has_api_key": self.api_key is not None,
            "is_local": self.is_local,
            "custom_port": self.custom_port,
        }


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------


class LLMProviderService:
    """
    Manages LLM provider selection, API key storage (encrypted), and
    configuration persistence in the project's ``.ce-config.json``.
    """

    def __init__(
        self,
        config_dir: Path | None = None,
        vault: _CredentialVault | None = None,
    ) -> None:
        self._config_dir = config_dir or Path.home() / ".config" / "context-engineer"
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._creds_path = self._config_dir / _CREDENTIALS_FILENAME
        self._vault = vault or _CredentialVault(self._config_dir)
        self._credentials: dict[str, str] = self._load_credentials()

    # -- credential persistence ---------------------------------------------

    def _load_credentials(self) -> dict[str, str]:
        """Load encrypted credentials from disk."""
        if not self._creds_path.exists():
            return {}
        try:
            raw = self._creds_path.read_text(encoding="utf-8")
            decrypted = self._vault.decrypt(raw)
            return json.loads(decrypted)
        except Exception:
            logger.warning("Could not load credentials — file may be corrupted")
            return {}

    def _save_credentials(self) -> None:
        """Persist encrypted credentials to disk."""
        plaintext = json.dumps(self._credentials, ensure_ascii=False)
        encrypted = self._vault.encrypt(plaintext)
        self._creds_path.write_text(encrypted, encoding="utf-8")
        if platform.system() != "Windows":
            self._creds_path.chmod(0o600)

    # -- public API ---------------------------------------------------------

    @staticmethod
    def list_providers() -> list[dict[str, Any]]:
        """Return metadata for all supported providers."""
        result = []
        for provider_type, meta in PROVIDER_REGISTRY.items():
            result.append(
                {
                    "id": (provider_type.value if isinstance(provider_type, LLMProviderType) else provider_type),
                    "display_name": meta["display_name"],
                    "default_model": meta["default_model"],
                    "requires_api_key": meta["requires_api_key"],
                }
            )
        return result

    def store_api_key(self, provider: str, api_key: str) -> None:
        """
        Encrypt and store an API key for the given provider.

        Args:
            provider: Provider identifier (e.g. ``openai``).
            api_key: The raw API key / token.
        """
        self._credentials[provider] = api_key
        self._save_credentials()
        logger.info("API key stored for provider %s", provider)

    def get_api_key(self, provider: str) -> str | None:
        """
        Retrieve the stored API key for a provider.

        Falls back to the provider's environment variable when no stored
        credential is found.

        Args:
            provider: Provider identifier.

        Returns:
            The API key string, or ``None`` if unavailable.
        """
        stored = self._credentials.get(provider)
        if stored:
            return stored
        # Fallback: environment variable
        meta = PROVIDER_REGISTRY.get(LLMProviderType(provider), {})
        env_var = meta.get("env_var")
        if env_var:
            return os.getenv(env_var)
        return None

    def remove_api_key(self, provider: str) -> bool:
        """
        Remove a stored API key.

        Args:
            provider: Provider identifier.

        Returns:
            True if a key was removed, False if none existed.
        """
        if provider in self._credentials:
            del self._credentials[provider]
            self._save_credentials()
            return True
        return False

    def has_api_key(self, provider: str) -> bool:
        """Check whether an API key is available (stored or env)."""
        return self.get_api_key(provider) is not None

    def resolve_provider(
        self,
        provider: str,
        *,
        model: str | None = None,
        base_url: str | None = None,
        custom_port: int | None = None,
    ) -> LLMProviderConfig:
        """
        Build a fully resolved provider configuration.

        Args:
            provider: Provider identifier string.
            model: Override the default model.
            base_url: Override the default base URL.
            custom_port: Custom port for local providers.

        Returns:
            A populated ``LLMProviderConfig``.

        Raises:
            ValueError: When the provider is unknown or a required API key is missing.
        """
        try:
            provider_type = LLMProviderType(provider)
        except ValueError:
            supported = ", ".join(p.value for p in LLMProviderType)
            msg = f"Unknown provider '{provider}'. Supported: {supported}"
            raise ValueError(msg) from None

        meta = PROVIDER_REGISTRY[provider_type]
        resolved_model = model or meta["default_model"]
        resolved_url = base_url or meta["base_url"]

        # Apply custom port for local providers
        if custom_port and provider_type == LLMProviderType.LOCAL_OLLAMA:
            resolved_url = f"http://localhost:{custom_port}"
        elif custom_port and provider_type == LLMProviderType.LOCAL_LM_STUDIO:
            resolved_url = f"http://localhost:{custom_port}/v1"

        api_key: str | None = None
        if meta["requires_api_key"]:
            api_key = self.get_api_key(provider)
            if not api_key:
                msg = (
                    f"API key required for {meta['display_name']}. "
                    f"Use 'ce config provider --set-key' or set {meta.get('env_var', 'the env var')}."
                )
                raise ValueError(msg)

        return LLMProviderConfig(
            provider=provider_type,
            model=resolved_model,
            base_url=resolved_url,
            api_key=api_key,
            custom_port=custom_port,
        )

    def get_configured_provider(self, project_config: dict) -> LLMProviderConfig | None:
        """
        Resolve the provider from project configuration.

        Args:
            project_config: The project's ``.ce-config.json`` content.

        Returns:
            Resolved config or None if no provider is configured.
        """
        provider_id = project_config.get("llm_provider")
        if not provider_id:
            return None
        try:
            return self.resolve_provider(
                provider_id,
                model=project_config.get("llm_model"),
                base_url=project_config.get("llm_base_url"),
                custom_port=project_config.get("llm_custom_port"),
            )
        except ValueError as exc:
            logger.warning("Could not resolve configured provider: %s", exc)
            return None


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

LLM_PROVIDER_SERVICE = LLMProviderService()

__all__ = [
    "LLM_PROVIDER_SERVICE",
    "LLMProviderConfig",
    "LLMProviderService",
    "LLMProviderType",
    "PROVIDER_REGISTRY",
]
