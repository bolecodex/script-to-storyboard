from __future__ import annotations

import pytest

from script2storyboard.config import DEFAULT_BASE_URL, load_config
from script2storyboard.errors import ConfigError


def test_config_precedence_cli_env_dotenv(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "S2S_ARK_API_KEY=dotenv-key\nS2S_TEXT_MODEL=dotenv-model\nS2S_ARK_BASE_URL=https://dotenv.example.com\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("S2S_ARK_API_KEY", "env-key")
    monkeypatch.setenv("S2S_TEXT_MODEL", "env-model")
    monkeypatch.setenv("S2S_ARK_BASE_URL", "https://env.example.com")

    cfg = load_config(
        api_key="cli-key",
        model="cli-model",
        base_url="https://cli.example.com",
        env_file=env_file,
    )

    assert cfg.api_key == "cli-key"
    assert cfg.model == "cli-model"
    assert cfg.base_url == "https://cli.example.com"


def test_config_loads_dotenv_when_env_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("S2S_ARK_API_KEY", raising=False)
    monkeypatch.delenv("ARK_API_KEY", raising=False)
    monkeypatch.delenv("S2S_TEXT_MODEL", raising=False)
    monkeypatch.delenv("S2S_ARK_BASE_URL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("S2S_ARK_API_KEY=k\nS2S_TEXT_MODEL=m\n", encoding="utf-8")

    cfg = load_config(env_file=env_file)

    assert cfg.api_key == "k"
    assert cfg.model == "m"
    assert cfg.base_url == DEFAULT_BASE_URL


def test_missing_required_config_raises(monkeypatch):
    monkeypatch.delenv("S2S_ARK_API_KEY", raising=False)
    monkeypatch.delenv("ARK_API_KEY", raising=False)
    monkeypatch.delenv("S2S_TEXT_MODEL", raising=False)

    with pytest.raises(ConfigError, match="S2S_ARK_API_KEY"):
        load_config()
