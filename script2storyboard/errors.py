"""Application-specific exceptions."""

from __future__ import annotations


class S2SError(Exception):
    """Base error for CLI-friendly failures."""

    exit_code = 1

    def __init__(self, message: str, *, exit_code: int | None = None) -> None:
        super().__init__(message)
        if exit_code is not None:
            self.exit_code = exit_code
        self.message = message


class ConfigError(S2SError):
    """Configuration is missing or invalid."""

    exit_code = 2


class ArkTextError(S2SError):
    """Ark text API request failed."""

    exit_code = 3


class ValidationError(S2SError):
    """Generated or supplied storyboard did not pass validation."""

    exit_code = 4
