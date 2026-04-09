from __future__ import annotations

import re

from app.models import IssueRequest

DOC_REQUEST_LABEL = "doc-request"
SECTION_PATTERN = re.compile(r"^###\s+(?P<heading>.+?)\s*$", re.MULTILINE)

FIELD_ALIASES = {
    "category": "category",
    "분류": "category",
    "reference links": "reference_links",
    "참고 링크": "reference_links",
    "request details": "request_details",
    "요청사항": "request_details",
    "additional instructions": "additional_instructions",
    "추가 요청사항": "additional_instructions",
}


def parse_issue(issue_payload: dict) -> IssueRequest:
    issue = issue_payload["issue"] if "issue" in issue_payload else issue_payload
    body = issue.get("body") or ""
    parsed = parse_issue_body(body)
    labels = [label["name"] if isinstance(label, dict) else label for label in issue.get("labels", [])]
    return IssueRequest(
        issue_number=issue["number"],
        title=issue["title"],
        body=body,
        author=issue["user"]["login"],
        requested_category=parsed.get("category") or None,
        reference_links=extract_links(parsed.get("reference_links", "")),
        request_details=parsed.get("request_details") or issue["title"],
        additional_instructions=parsed.get("additional_instructions") or None,
        labels=labels,
        html_url=issue.get("html_url"),
    )


def parse_issue_body(body: str) -> dict[str, str]:
    if not body.strip():
        return {}
    matches = list(SECTION_PATTERN.finditer(body))
    if not matches:
        return {}
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = normalize_heading(match.group("heading"))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        content = body[start:end].strip()
        field = FIELD_ALIASES.get(heading)
        if field:
            result[field] = clean_issue_form_value(content)
    return result


def has_doc_request_label(labels: list[str]) -> bool:
    return DOC_REQUEST_LABEL in labels


def normalize_heading(heading: str) -> str:
    return heading.strip().lower()


def clean_issue_form_value(value: str) -> str:
    cleaned = value.strip()
    if cleaned in {"_No response_", "No response"}:
        return ""
    return cleaned


def extract_links(text: str) -> list[str]:
    pattern = re.compile(r"https?://\S+")
    return [match.group(0).rstrip(").,]>") for match in pattern.finditer(text)]


def issue_summary_for_prompt(issue_request: IssueRequest) -> str:
    lines = [
        f"Issue title: {issue_request.title}",
        f"Requested category: {issue_request.requested_category or 'none'}",
        f"Issue author: {issue_request.author}",
        f"Request details:\n{issue_request.request_details}",
    ]
    if issue_request.additional_instructions:
        lines.append(f"Additional instructions:\n{issue_request.additional_instructions}")
    if issue_request.reference_links:
        lines.append("Reference links:\n" + "\n".join(f"- {link}" for link in issue_request.reference_links))
    return "\n\n".join(lines)
