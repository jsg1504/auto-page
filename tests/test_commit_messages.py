from __future__ import annotations

import unittest

from app.commit_messages import build_generated_doc_commit_message


class CommitMessageTests(unittest.TestCase):
    def test_generated_commit_message_uses_lore_format(self) -> None:
        message = build_generated_doc_commit_message(12, "OAuth", "개념정리")
        self.assertIn("Constraint:", message)
        self.assertIn("Confidence:", message)
        self.assertIn("Scope-risk:", message)
        self.assertIn("Related: issue #12", message)


if __name__ == "__main__":
    unittest.main()
