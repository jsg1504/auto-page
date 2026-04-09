from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from app.models import IssueRequest
from app.openai_client import OpenAIResponsesClient, extract_output_text


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class OpenAIClientTests(unittest.TestCase):
    def test_extract_output_text_uses_nested_output(self) -> None:
        payload = {
            "output": [
                {"content": [{"text": '{"title":"Doc","summary":"Summary","category":"개념정리","slug":"doc","tags":["a"],"markdown":"# Doc"}'}]}
            ]
        }
        self.assertIn('"title":"Doc"', extract_output_text(payload))

    def test_generate_document_uses_confirmed_model(self) -> None:
        issue = IssueRequest(
            issue_number=7,
            title="OAuth",
            body="",
            author="alice",
            requested_category="개념정리",
            reference_links=["https://example.com"],
            request_details="OAuth를 설명해줘",
        )
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse(
                {
                    "output": [
                        {
                            "content": [
                                {
                                    "text": json.dumps(
                                        {
                                            "title": "OAuth",
                                            "summary": "summary",
                                            "category": "개념정리",
                                            "slug": "oauth",
                                            "tags": ["auth"],
                                            "markdown": "# OAuth\n\n본문",
                                        }
                                    )
                                }
                            ]
                        }
                    ]
                }
            )

        client = OpenAIResponsesClient("key", "gpt-5.4")
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            document = client.generate_document(issue)
        self.assertEqual(captured["body"]["model"], "gpt-5.4")
        self.assertEqual(document.slug, "oauth")
        self.assertEqual(document.category, "개념정리")


if __name__ == "__main__":
    unittest.main()
