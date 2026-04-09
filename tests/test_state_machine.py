from __future__ import annotations

import unittest

from app.config import STATE_LABEL_FAILED, STATE_LABEL_NEEDS_REVIEW, STATE_LABEL_RETRY_REQUESTED, STATE_LABEL_REVIEW_COMPLETE, STATE_LABELS
from app.state_machine import can_transition, inspect_state, replacement_plan


class StateMachineTests(unittest.TestCase):
    def test_inspect_state_detects_multi_state(self) -> None:
        inspection = inspect_state([STATE_LABEL_NEEDS_REVIEW, STATE_LABEL_FAILED], STATE_LABELS)
        self.assertFalse(inspection.is_valid)
        self.assertIsNone(inspection.current)

    def test_replacement_plan_removes_previous_state(self) -> None:
        to_remove, to_add = replacement_plan([STATE_LABEL_FAILED], STATE_LABEL_NEEDS_REVIEW, STATE_LABELS)
        self.assertEqual(to_remove, [STATE_LABEL_FAILED])
        self.assertEqual(to_add, [STATE_LABEL_NEEDS_REVIEW])

    def test_transition_rules(self) -> None:
        self.assertTrue(can_transition(None, STATE_LABEL_NEEDS_REVIEW))
        self.assertTrue(can_transition(STATE_LABEL_NEEDS_REVIEW, STATE_LABEL_REVIEW_COMPLETE))
        self.assertTrue(can_transition(STATE_LABEL_FAILED, STATE_LABEL_RETRY_REQUESTED))
        self.assertFalse(can_transition(STATE_LABEL_REVIEW_COMPLETE, STATE_LABEL_NEEDS_REVIEW))


if __name__ == "__main__":
    unittest.main()
