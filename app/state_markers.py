from __future__ import annotations

import re

STATE_MARKER_RE = re.compile(r"<!--\s*auto-page:state=(?P<state>[a-z0-9:-]+)\s*-->")


def build_state_marker(state: str) -> str:
    return f"<!-- auto-page:state={state} -->"


def build_state_comment(state: str, message: str) -> str:
    return f"{build_state_marker(state)}\n{message}"


def extract_latest_state_marker(comments: list[str]) -> str | None:
    latest: str | None = None
    for body in comments:
        match = STATE_MARKER_RE.search(body)
        if match:
            latest = match.group("state")
    return latest
