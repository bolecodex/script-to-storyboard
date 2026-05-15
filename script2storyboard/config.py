"""Configuration loading for the CLI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from script2storyboard.errors import ConfigError


DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com"


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    model: str
    base_url: str = DEFAULT_BASE_URL
    timeout_s: float = 120.0

    @property
    def chat_completions_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/api/v3/chat/completions"


def load_config(
    *,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    env_file: Path | None = None,
    require_auth: bool = True,
) -> AppConfig:
    """Load config from .env, environment variables, then CLI overrides.

    Precedence is intentionally explicit:
    CLI option > environment variable > .env value > default.
    """

    load_dotenv(dotenv_path=env_file, override=False)

    resolved_api_key = api_key or os.getenv("S2S_ARK_API_KEY") or os.getenv("ARK_API_KEY") or ""
    resolved_model = model or os.getenv("S2S_TEXT_MODEL") or ""
    resolved_base_url = base_url or os.getenv("S2S_ARK_BASE_URL") or DEFAULT_BASE_URL

    if require_auth:
        missing: list[str] = []
        if not resolved_api_key:
            missing.append("S2S_ARK_API_KEY")
        if not resolved_model:
            missing.append("S2S_TEXT_MODEL")
        if missing:
            raise ConfigError(
                "Missing required configuration: "
                + ", ".join(missing)
                + ". Set them in .env/environment or pass CLI overrides."
            )

    return AppConfig(
        api_key=resolved_api_key,
        model=resolved_model,
        base_url=resolved_base_url,
    )
