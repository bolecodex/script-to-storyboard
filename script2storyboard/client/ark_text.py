"""Volcengine Ark Chat Completions client."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import httpx

from script2storyboard.config import AppConfig
from script2storyboard.errors import ArkTextError


Message = dict[str, str]


class ArkTextClient:
    def __init__(self, config: AppConfig, *, http_client: httpx.Client | None = None) -> None:
        self.config = config
        self._client = http_client

    def complete(
        self,
        messages: Sequence[Message],
        *,
        temperature: float = 0.4,
        max_tokens: int = 12000,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": list(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        try:
            if self._client is not None:
                response = self._client.post(
                    self.config.chat_completions_url,
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout_s,
                )
            else:
                with httpx.Client(timeout=self.config.timeout_s) as client:
                    response = client.post(
                        self.config.chat_completions_url,
                        headers=headers,
                        json=payload,
                    )
        except httpx.HTTPError as exc:
            raise ArkTextError(f"Ark text request failed: {exc}") from exc

        if response.status_code >= 400:
            detail = _extract_error_detail(response)
            raise ArkTextError(f"Ark text request failed ({response.status_code}): {detail}")

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ArkTextError("Ark text response did not contain choices[0].message.content.") from exc

        if not isinstance(content, str) or not content.strip():
            raise ArkTextError("Ark text response content is empty.")
        return _strip_markdown_fence(content.strip())


def _extract_error_detail(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text[:500]
    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            return str(error.get("message") or error.get("code") or error)
        if error:
            return str(error)
        return str(data.get("message") or data)[:500]
    return str(data)[:500]


def _strip_markdown_fence(text: str) -> str:
    lines = text.strip().splitlines()
    if len(lines) >= 2 and lines[0].strip().startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return text.strip()
