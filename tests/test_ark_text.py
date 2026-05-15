from __future__ import annotations

import httpx
import pytest

from script2storyboard.client.ark_text import ArkTextClient
from script2storyboard.config import AppConfig
from script2storyboard.errors import ArkTextError


def test_ark_text_extracts_message_content():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v3/chat/completions"
        assert request.headers["authorization"] == "Bearer key"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "```markdown\n# ok\n```"}}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    ark = ArkTextClient(AppConfig(api_key="key", model="model"), http_client=client)

    assert ark.complete([{"role": "user", "content": "hi"}]) == "# ok"


def test_ark_text_raises_on_error_payload():
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(401, json={"error": {"message": "bad key"}})
        )
    )
    ark = ArkTextClient(AppConfig(api_key="key", model="model"), http_client=client)

    with pytest.raises(ArkTextError, match="bad key"):
        ark.complete([{"role": "user", "content": "hi"}])
