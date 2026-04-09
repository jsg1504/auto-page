from __future__ import annotations

import unittest

from app.issue_parser import extract_links, parse_issue_body


class IssueParserTests(unittest.TestCase):
    def test_parse_issue_body(self) -> None:
        body = """### 분류\n개념정리\n\n### 참고 링크\nhttps://example.com/doc\n\n### 요청사항\n이 개념을 자세히 설명해주세요.\n\n### 추가 요청사항\n표도 포함해주세요.\n"""
        parsed = parse_issue_body(body)
        self.assertEqual(parsed["category"], "개념정리")
        self.assertEqual(parsed["request_details"], "이 개념을 자세히 설명해주세요.")
        self.assertEqual(parsed["additional_instructions"], "표도 포함해주세요.")
        self.assertEqual(extract_links(parsed["reference_links"]), ["https://example.com/doc"])


if __name__ == "__main__":
    unittest.main()
