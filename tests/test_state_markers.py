from __future__ import annotations

import unittest

from app.state_markers import build_state_comment, build_state_marker, extract_latest_state_marker


class StateMarkerTests(unittest.TestCase):
    def test_extract_latest_state_marker(self) -> None:
        comments = [
            build_state_comment("state:needs-review", "first"),
            "plain comment",
            build_state_comment("state:failed", "failed"),
        ]
        self.assertEqual(extract_latest_state_marker(comments), "state:failed")

    def test_build_state_marker(self) -> None:
        self.assertEqual(build_state_marker("state:needs-review"), "<!-- auto-page:state=state:needs-review -->")


if __name__ == "__main__":
    unittest.main()
