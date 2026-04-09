from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.category_manager import canonical_category, ensure_docs_layout, write_document
from app.models import GeneratedDocument, IssueRequest


class CategoryManagerTests(unittest.TestCase):
    def test_requested_category_wins(self) -> None:
        self.assertEqual(canonical_category("개념정리", None), "개념정리")

    def test_fallback_category(self) -> None:
        self.assertEqual(canonical_category(None, None, "리서치 benchmark 비교"), "리서치 정리")

    def test_write_document_creates_indexes(self) -> None:
        issue = IssueRequest(
            issue_number=1,
            title="State machine notes",
            body="",
            author="tester",
            requested_category="개념정리",
            reference_links=[],
            request_details="state machine details",
        )
        document = GeneratedDocument(
            title="State Machine",
            slug="state-machine",
            category="개념정리",
            summary="summary",
            tags=["state"],
            markdown="# State Machine\n\n본문",
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            docs_root = Path(tmp_dir) / "docs"
            ensure_docs_layout(docs_root)
            result = write_document(docs_root, issue, document)
            self.assertTrue(result.markdown_path.exists())
            self.assertIn("State Machine", result.markdown_path.read_text(encoding="utf-8"))
            self.assertIn("개념정리", result.category_index_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
