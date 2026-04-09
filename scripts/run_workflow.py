#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import AppConfig
from app.github_api import GitHubApi
from app.handlers import handle_issue_opened, handle_retry_requested, handle_review_complete


def load_event_payload(path: str | None = None) -> dict:
    event_path = path or os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise SystemExit("GITHUB_EVENT_PATH is required")
    return json.loads(Path(event_path).read_text(encoding="utf-8"))


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        raise SystemExit("usage: run_workflow.py <issue-opened|review-complete|retry-requested> [event-path]")
    action = argv[1]
    payload = load_event_payload(argv[2] if len(argv) > 2 else None)
    config = AppConfig.from_env()
    github = GitHubApi(config.repo, config.github_token)

    if action == "issue-opened":
        result = handle_issue_opened(payload, config, github)
    elif action == "review-complete":
        result = handle_review_complete(payload, config, github, REPO_ROOT)
    elif action == "retry-requested":
        result = handle_retry_requested(payload, config, github)
    else:
        raise SystemExit(f"unknown action: {action}")

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
