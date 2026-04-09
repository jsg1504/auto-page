from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class IssueRequest:
    issue_number: int
    title: str
    body: str
    author: str
    requested_category: str | None
    reference_links: list[str]
    request_details: str
    additional_instructions: str | None = None
    labels: list[str] = field(default_factory=list)
    html_url: str | None = None


@dataclass(frozen=True)
class GeneratedDocument:
    title: str
    slug: str
    category: str
    summary: str
    tags: list[str]
    markdown: str


@dataclass(frozen=True)
class DocWriteResult:
    markdown_path: Path
    category_index_path: Path
    root_index_path: Path
