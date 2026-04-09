from __future__ import annotations

import json
import urllib.error
import urllib.request

from app.category_manager import canonical_category, slugify
from app.config import CATEGORY_PATHS
from app.issue_parser import issue_summary_for_prompt
from app.models import GeneratedDocument, IssueRequest

OPENAI_URL = "https://api.openai.com/v1/responses"


class OpenAIError(RuntimeError):
    pass


class OpenAIResponsesClient:
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise OpenAIError("OPENAI_API_KEY is required for document generation")
        self.api_key = api_key
        self.model = model

    def generate_document(self, issue_request: IssueRequest) -> GeneratedDocument:
        payload = {
            "model": self.model,
            "instructions": (
                "You generate high-quality, citation-friendly documentation pages for a GitHub Pages knowledge base. "
                "Return JSON only with keys: title, summary, category, slug, tags, markdown. "
                f"Valid categories: {', '.join(CATEGORY_PATHS.keys())}. "
                "The markdown should be detailed, readable, and include sections for overview, key points, references, and follow-up notes. "
                "Honor a user-requested category when present."
            ),
            "input": issue_summary_for_prompt(issue_request),
        }
        request = urllib.request.Request(
            OPENAI_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # pragma: no cover - exercised with mocked errors in tests
            body = exc.read().decode("utf-8", errors="replace")
            raise OpenAIError(f"OpenAI request failed ({exc.code}): {body}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover - network failure path
            raise OpenAIError(f"OpenAI request failed: {exc}") from exc

        text = extract_output_text(raw)
        parsed = parse_json_payload(text)
        category = canonical_category(issue_request.requested_category, parsed.get("category"), issue_request.request_details)
        title = parsed.get("title") or issue_request.title
        slug = slugify(parsed.get("slug") or title)
        tags = [str(tag).strip() for tag in parsed.get("tags", []) if str(tag).strip()]
        markdown = parsed.get("markdown") or fallback_markdown(issue_request)
        summary = parsed.get("summary") or title
        return GeneratedDocument(
            title=title,
            slug=slug,
            category=category,
            summary=summary,
            tags=tags,
            markdown=markdown,
        )


def extract_output_text(response: dict) -> str:
    if isinstance(response.get("output_text"), str) and response["output_text"].strip():
        return response["output_text"]
    output = response.get("output", [])
    chunks: list[str] = []
    for item in output:
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    if not chunks:
        raise OpenAIError("OpenAI response did not contain text output")
    return "\n".join(chunks)


def parse_json_payload(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise OpenAIError(f"OpenAI response was not valid JSON: {cleaned[:200]}") from exc


def fallback_markdown(issue_request: IssueRequest) -> str:
    references = "\n".join(f"- {link}" for link in issue_request.reference_links) or "- 참고 링크 없음"
    return (
        f"# {issue_request.title}\n\n"
        "## 개요\n"
        f"{issue_request.request_details}\n\n"
        "## 참고 링크\n"
        f"{references}\n"
    )
