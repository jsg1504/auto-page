from __future__ import annotations

import re
from pathlib import Path

from app.config import CATEGORY_PATHS, DEFAULT_CATEGORY
from app.models import DocWriteResult, GeneratedDocument, IssueRequest


def canonical_category(requested_category: str | None, suggested_category: str | None, request_details: str = "") -> str:
    for candidate in (requested_category, suggested_category):
        if candidate and candidate in CATEGORY_PATHS:
            return candidate
    normalized = request_details.lower()
    if any(keyword in normalized for keyword in ("research", "paper", "survey", "benchmark", "비교", "리서치")):
        return "리서치 정리"
    if any(keyword in normalized for keyword in ("summary", "요약", "tl;dr")):
        return "정보 요약"
    return DEFAULT_CATEGORY


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9가-힣\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-") or "document"


def ensure_docs_layout(docs_root: Path) -> None:
    docs_root.mkdir(parents=True, exist_ok=True)
    config_path = docs_root / "_config.yml"
    if not config_path.exists():
        config_path.write_text(
            "title: Auto Page\n"
            "description: Issue-driven documentation archive\n"
            "theme: minima\n"
            "markdown: kramdown\n"
            "collections_dir: .\n",
            encoding="utf-8",
        )
    for category_name, directory in CATEGORY_PATHS.items():
        category_dir = docs_root / directory
        category_dir.mkdir(parents=True, exist_ok=True)
        index_path = category_dir / "index.md"
        if not index_path.exists():
            index_path.write_text(category_index_content(category_name, []), encoding="utf-8")
    root_index = docs_root / "index.md"
    if not root_index.exists():
        root_index.write_text(root_index_content(), encoding="utf-8")


def write_document(docs_root: Path, issue: IssueRequest, document: GeneratedDocument) -> DocWriteResult:
    ensure_docs_layout(docs_root)
    category_dir = docs_root / CATEGORY_PATHS[document.category]
    category_dir.mkdir(parents=True, exist_ok=True)
    doc_path = category_dir / f"{document.slug}.md"
    front_matter = [
        "---",
        f'title: "{escape_quotes(document.title)}"',
        f'category: "{document.category}"',
        f'issue_number: {issue.issue_number}',
        f'issue_url: "{issue.html_url or ""}"',
        f'tags: [{", ".join(f"\"{escape_quotes(tag)}\"" for tag in document.tags)}]',
        "layout: default",
        "---",
        "",
    ]
    doc_path.write_text("\n".join(front_matter) + document.markdown.strip() + "\n", encoding="utf-8")
    category_index_path = category_dir / "index.md"
    category_index_path.write_text(render_category_index(document.category, category_dir), encoding="utf-8")
    root_index_path = docs_root / "index.md"
    root_index_path.write_text(root_index_content(), encoding="utf-8")
    return DocWriteResult(markdown_path=doc_path, category_index_path=category_index_path, root_index_path=root_index_path)


def render_category_index(category_name: str, category_dir: Path) -> str:
    entries = []
    for path in sorted(category_dir.glob("*.md")):
        if path.name == "index.md":
            continue
        title = extract_title(path) or path.stem
        entries.append((title, path.name))
    return category_index_content(category_name, entries)


def category_index_content(category_name: str, entries: list[tuple[str, str]]) -> str:
    lines = ["---", f'title: "{escape_quotes(category_name)}"', "layout: default", "---", "", f"# {category_name}", ""]
    if not entries:
        lines.append("아직 문서가 없습니다.")
    else:
        for title, file_name in entries:
            lines.append(f"- [{title}](./{file_name})")
    lines.append("")
    lines.append("[전체 문서로 돌아가기](../index.html)")
    return "\n".join(lines)


def root_index_content() -> str:
    lines = ["---", 'title: "Auto Page"', "layout: default", "---", "", "# Auto Page", "", "이 사이트는 GitHub issue 기반으로 생성된 문서를 카테고리별로 정리합니다.", ""]
    for category_name, directory in CATEGORY_PATHS.items():
        lines.append(f"- [{category_name}](./{directory}/index.html)")
    return "\n".join(lines) + "\n"


def extract_title(path: Path) -> str | None:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("title:"):
            return line.split(":", 1)[1].strip().strip('"')
    return None


def escape_quotes(value: str) -> str:
    return value.replace('"', '\\"')
