from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.config import AppConfig, STATE_LABEL_FAILED, STATE_LABEL_NEEDS_REVIEW, STATE_LABEL_RETRY_REQUESTED, STATE_LABEL_REVIEW_COMPLETE
from app.handlers import handle_issue_opened, handle_retry_requested, handle_review_complete
from app.models import GeneratedDocument


class FakeGitHub:
    def __init__(self) -> None:
        self.added: list[tuple[int, list[str]]] = []
        self.removed: list[tuple[int, str]] = []
        self.comments: list[tuple[int, str]] = []
        self.comment_history: dict[int, list[dict[str, str]]] = {}

    def add_labels(self, issue_number: int, labels: list[str]) -> None:
        self.added.append((issue_number, labels))

    def remove_label(self, issue_number: int, label: str) -> None:
        self.removed.append((issue_number, label))

    def post_comment(self, issue_number: int, body: str) -> None:
        self.comments.append((issue_number, body))
        self.comment_history.setdefault(issue_number, []).append({"body": body})

    def list_comments(self, issue_number: int):
        return self.comment_history.get(issue_number, [])


class FakePublisher:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.calls: list[list[Path]] = []

    def commit_and_push(self, paths: list[Path], message: str, push: bool = True) -> bool:
        self.calls.append(paths)
        return True


class FakeOpenAI:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate_document(self, issue_request):
        return GeneratedDocument(
            title=issue_request.title,
            slug="generated-doc",
            category=issue_request.requested_category or "정보 요약",
            summary="summary",
            tags=["generated"],
            markdown="# Generated\n\nHello",
        )


class HandlerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.config = AppConfig(
            repo="example/repo",
            docs_root=Path(self.temp_dir.name) / "docs",
            github_token="token",
            openai_api_key="key",
            reviewer_pool=frozenset({"admin"}),
        )
        self.issue_opened_payload = {
            "issue": {
                "number": 1,
                "title": "[doc] 문서화 요청",
                "body": "### 분류\n개념정리\n\n### 참고 링크\nhttps://example.com\n\n### 요청사항\n설명해주세요.\n",
                "user": {"login": "alice"},
                "labels": [{"name": "doc-request"}],
                "html_url": "https://github.com/example/repo/issues/1",
            }
        }
        self.review_payload = {
            "issue": {
                "number": 1,
                "title": "[doc] 문서화 요청",
                "body": "### 분류\n개념정리\n\n### 요청사항\n설명해주세요.\n",
                "user": {"login": "alice"},
                "labels": [{"name": "doc-request"}, {"name": STATE_LABEL_REVIEW_COMPLETE}],
                "html_url": "https://github.com/example/repo/issues/1",
            },
            "sender": {"login": "admin"},
        }
        self.retry_payload = {
            "issue": {
                "number": 1,
                "title": "[doc] 문서화 요청",
                "body": "### 분류\n정보 요약\n\n### 요청사항\n다시 생성해주세요.\n",
                "user": {"login": "alice"},
                "labels": [{"name": "doc-request"}, {"name": STATE_LABEL_RETRY_REQUESTED}],
                "html_url": "https://github.com/example/repo/issues/1",
            }
        }

    def test_issue_opened_applies_needs_review(self) -> None:
        github = FakeGitHub()
        result = handle_issue_opened(self.issue_opened_payload, self.config, github)
        self.assertEqual(result, "needs-review-applied")
        self.assertIn((1, [STATE_LABEL_NEEDS_REVIEW]), github.added)

    def test_issue_opened_ignores_non_doc_issue(self) -> None:
        github = FakeGitHub()
        payload = {
            "issue": {
                "number": 2,
                "title": "일반 이슈",
                "body": "plain issue",
                "user": {"login": "alice"},
                "labels": [],
                "html_url": "https://github.com/example/repo/issues/2",
            }
        }
        result = handle_issue_opened(payload, self.config, github)
        self.assertEqual(result, "ignored-non-doc-request")
        self.assertEqual(github.added, [])

    def test_retry_requested_resets_state(self) -> None:
        github = FakeGitHub()
        result = handle_retry_requested(self.retry_payload, self.config, github)
        self.assertEqual(result, "retry-reset-to-needs-review")
        self.assertIn((1, STATE_LABEL_RETRY_REQUESTED), github.removed)
        self.assertIn((1, [STATE_LABEL_NEEDS_REVIEW]), github.added)

    def test_review_complete_requires_reviewer_pool(self) -> None:
        github = FakeGitHub()
        config = AppConfig(repo="example/repo", docs_root=self.config.docs_root, github_token="token", openai_api_key="key")
        result = handle_review_complete(self.review_payload, config, github, Path.cwd())
        self.assertEqual(result, "reviewer-pool-missing")
        self.assertTrue(any("REVIEWER_POOL" in body for _, body in github.comments))

    def test_review_complete_requires_authorized_admin(self) -> None:
        github = FakeGitHub()
        payload = dict(self.review_payload)
        payload["sender"] = {"login": "outsider"}
        result = handle_review_complete(payload, self.config, github, Path.cwd())
        self.assertEqual(result, "reviewer-not-allowed")

    def test_review_complete_generates_document(self) -> None:
        github = FakeGitHub()
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            with patch("app.handlers.build_generator", return_value=FakeOpenAI("key", "gpt-5.4")), patch("app.handlers.GitPublisher", FakePublisher):
                result = handle_review_complete(self.review_payload, self.config, github, repo_root)
        self.assertEqual(result, "document-generated")
        self.assertTrue(any("문서를 생성했습니다" in body for _, body in github.comments))

    def test_review_complete_failure_marks_failed(self) -> None:
        github = FakeGitHub()
        with patch("app.handlers.build_generator", side_effect=RuntimeError("boom")):
            result = handle_review_complete(self.review_payload, self.config, github, Path.cwd())
        self.assertEqual(result, "generation-failed")
        self.assertIn((1, [STATE_LABEL_FAILED]), github.added)
        self.assertFalse(any("boom" in body for _, body in github.comments))


if __name__ == "__main__":
    unittest.main()
