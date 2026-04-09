from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.config import (
    STATE_LABEL_FAILED,
    STATE_LABEL_NEEDS_REVIEW,
    STATE_LABEL_RETRY_REQUESTED,
    STATE_LABEL_REVIEW_COMPLETE,
)


@dataclass(frozen=True)
class StateInspection:
    state_labels: list[str]

    @property
    def is_valid(self) -> bool:
        return len(self.state_labels) <= 1

    @property
    def current(self) -> str | None:
        if len(self.state_labels) == 1:
            return self.state_labels[0]
        return None


STATE_FLOW = {
    STATE_LABEL_NEEDS_REVIEW: {STATE_LABEL_REVIEW_COMPLETE, STATE_LABEL_FAILED},
    STATE_LABEL_REVIEW_COMPLETE: {STATE_LABEL_FAILED},
    STATE_LABEL_FAILED: {STATE_LABEL_RETRY_REQUESTED},
    STATE_LABEL_RETRY_REQUESTED: {STATE_LABEL_NEEDS_REVIEW},
}


def extract_state_labels(labels: Iterable[str], allowed: Iterable[str]) -> list[str]:
    allowed_set = set(allowed)
    return [label for label in labels if label in allowed_set]


def inspect_state(labels: Iterable[str], allowed: Iterable[str]) -> StateInspection:
    return StateInspection(state_labels=extract_state_labels(labels, allowed))


def replacement_plan(labels: Iterable[str], target: str, allowed: Iterable[str]) -> tuple[list[str], list[str]]:
    state_labels = extract_state_labels(labels, allowed)
    to_remove = [label for label in state_labels if label != target]
    to_add: list[str] = []
    if target not in state_labels:
        to_add.append(target)
    return to_remove, to_add


def can_transition(current: str | None, target: str) -> bool:
    if current is None:
        return target == STATE_LABEL_NEEDS_REVIEW
    return target in STATE_FLOW.get(current, set())
