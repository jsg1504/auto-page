from __future__ import annotations

import sys
from pathlib import Path

from app.category_manager import write_document
from app.commit_messages import build_generated_doc_commit_message
from app.config import (
    AppConfig,
    STATE_LABEL_FAILED,
    STATE_LABEL_NEEDS_REVIEW,
    STATE_LABEL_RETRY_REQUESTED,
    STATE_LABEL_REVIEW_COMPLETE,
    is_in_pool,
)
from app.git_ops import GitPublisher
from app.github_api import GitHubApi
from app.issue_parser import has_doc_request_label, parse_issue
from app.provider import build_generator
from app.state_machine import inspect_state, replacement_plan
from app.state_markers import build_state_comment


def handle_issue_opened(event_payload: dict, config: AppConfig, github: GitHubApi) -> str:
    issue = parse_issue(event_payload)
    if not has_doc_request_label(issue.labels):
        return "ignored-non-doc-request"
    if config.enforce_requester_pool and not is_in_pool(issue.author, config.requester_pool):
        github.post_comment(
            issue.issue_number,
            "이 저장소는 현재 허용된 요청자만 자동 문서화 흐름을 사용할 수 있습니다. 관리자에게 문의해주세요.",
        )
        return "requester-not-allowed"

    inspection = inspect_state(issue.labels, config.state_labels)
    if not inspection.is_valid:
        return "invalid-multi-state"

    to_remove, to_add = replacement_plan(issue.labels, STATE_LABEL_NEEDS_REVIEW, config.state_labels)
    for label in to_remove:
        github.remove_label(issue.issue_number, label)
    github.add_labels(issue.issue_number, to_add)
    github.post_comment(
        issue.issue_number,
        build_state_comment(
            STATE_LABEL_NEEDS_REVIEW,
            "문서화 요청을 접수했습니다. 검수 후 `state:review-complete` 라벨을 추가하면 생성이 시작됩니다.",
        ),
    )
    return "needs-review-applied"


def handle_retry_requested(event_payload: dict, config: AppConfig, github: GitHubApi) -> str:
    issue = parse_issue(event_payload)
    if not has_doc_request_label(issue.labels):
        return "ignored-non-doc-request"

    inspection = inspect_state(issue.labels, config.state_labels)
    if not inspection.is_valid:
        return "invalid-multi-state"

    if inspection.current != STATE_LABEL_RETRY_REQUESTED:
        return "retry-state-missing"

    to_remove, to_add = replacement_plan(issue.labels, STATE_LABEL_NEEDS_REVIEW, config.state_labels)
    for label in to_remove:
        github.remove_label(issue.issue_number, label)
    github.add_labels(issue.issue_number, to_add)
    github.post_comment(
        issue.issue_number,
        build_state_comment(STATE_LABEL_NEEDS_REVIEW, "재시도 요청을 확인했습니다. 이슈를 다시 검수해주세요."),
    )
    return "retry-reset-to-needs-review"


def handle_review_complete(
    event_payload: dict,
    config: AppConfig,
    github: GitHubApi,
    repo_root: Path,
) -> str:
    issue = parse_issue(event_payload)
    if not has_doc_request_label(issue.labels):
        return "ignored-non-doc-request"

    inspection = inspect_state(issue.labels, config.state_labels)
    if not inspection.is_valid:
        return "invalid-multi-state"

    if inspection.current != STATE_LABEL_REVIEW_COMPLETE:
        return "review-state-missing"

    actor = event_payload.get("sender", {}).get("login", "")
    if not config.reviewer_pool:
        github.post_comment(issue.issue_number, "REVIEWER_POOL 설정이 없어 문서 생성을 시작할 수 없습니다.")
        return "reviewer-pool-missing"
    if not is_in_pool(actor, config.reviewer_pool):
        github.post_comment(issue.issue_number, f"`{actor}` 는 문서 생성 권한이 없습니다.")
        return "reviewer-not-allowed"

    try:
        generator = build_generator(config)
        document = generator.generate_document(issue)
        write_result = write_document(config.docs_root, issue, document)
        publisher = GitPublisher(repo_root)
        changed = publisher.commit_and_push(
            [write_result.markdown_path, write_result.category_index_path, write_result.root_index_path],
            message=build_generated_doc_commit_message(issue.issue_number, document.title, document.category),
        )
        comment = (
            f"문서를 생성했습니다: `{write_result.markdown_path}`\n\n"
            f"카테고리: **{document.category}**\n"
            f"커밋 {'완료' if changed else '생략(no-op)'}"
        )
        github.post_comment(issue.issue_number, build_state_comment(STATE_LABEL_REVIEW_COMPLETE, comment))
        return "document-generated"
    except Exception as exc:  # pragma: no cover - failure path exercised with mocks in tests
        print(f"generation failed for issue #{issue.issue_number}: {exc}", file=sys.stderr)
        to_remove, to_add = replacement_plan(issue.labels, STATE_LABEL_FAILED, config.state_labels)
        for label in to_remove:
            github.remove_label(issue.issue_number, label)
        github.add_labels(issue.issue_number, to_add)
        github.post_comment(
            issue.issue_number,
            build_state_comment(STATE_LABEL_FAILED, "문서 생성에 실패했습니다. Actions 로그를 확인한 뒤 내용을 수정하고 `state:retry-requested` 라벨을 추가해주세요."),
        )
        return "generation-failed"
