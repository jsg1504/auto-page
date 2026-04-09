from __future__ import annotations


def sanitize_single_line(value: str) -> str:
    return " ".join(value.split())


def build_generated_doc_commit_message(issue_number: int, title: str, category: str) -> str:
    safe_title = sanitize_single_line(title)
    safe_category = sanitize_single_line(category)
    return (
        "Archive approved issue research as a retrievable knowledge page\n\n"
        f"The workflow generated a categorized documentation page from issue #{issue_number} "
        "so the requested material can be rediscovered later through the Pages archive.\n\n"
        "Constraint: Generated content must land in the Pages-backed docs tree\n"
        "Constraint: Commit is produced by GitHub Actions after review-complete state\n"
        "Confidence: medium\n"
        "Scope-risk: narrow\n"
        f"Directive: Review generated {safe_category} pages before broadening automatic publication rules\n"
        "Tested: Workflow generation path and git staging logic\n"
        f"Related: issue #{issue_number} | {safe_title}"
    )
