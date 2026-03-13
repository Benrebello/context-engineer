"""Centralized logging utilities for Context Engineer services."""

from __future__ import annotations

import logging
import os

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"
ENV_LOG_LEVEL = "CONTEXT_ENGINEER_LOG_LEVEL"


class LoggingService:
    """Configures and exposes Python loggers with consistent settings."""

    def __init__(self) -> None:
        self._configured = False
        self._level = logging.INFO

    def configure(self, level: str | int | None = None) -> None:
        """
        Configure global logging.

        Args:
            level: Desired logging level (name or numeric). Falls back to
                environment variable or INFO when omitted.
        """
        resolved_level = self._resolve_level(level)
        if self._configured and resolved_level == self._level:
            return

        logging.basicConfig(
            level=resolved_level,
            format=LOG_FORMAT,
            datefmt=LOG_DATE_FORMAT,
            force=True,
        )
        self._configured = True
        self._level = resolved_level

    def get_logger(self, name: str) -> logging.Logger:
        """
        Return a logger configured through the LoggingService.

        Args:
            name: Logger name, usually the fully qualified module path.
        """
        if not self._configured:
            self.configure()
        return logging.getLogger(name)

    @staticmethod
    def _resolve_level(level: str | int | None) -> int:
        """Translate textual or numeric level definitions."""
        if isinstance(level, int):
            return level

        candidates = [level, os.getenv(ENV_LOG_LEVEL), "INFO"]
        for candidate in candidates:
            if not candidate:
                continue
            if isinstance(candidate, str):
                normalized = candidate.strip().upper()
                if normalized.isdigit():
                    return int(normalized)
                if normalized in logging._nameToLevel:  # type: ignore[attr-defined]
                    return logging._nameToLevel[normalized]  # type: ignore[attr-defined]
            else:
                return int(candidate)
        return logging.INFO


LOGGING_SERVICE = LoggingService()
