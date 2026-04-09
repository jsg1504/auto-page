from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

STATE_LABEL_NEEDS_REVIEW = "state:needs-review"
STATE_LABEL_REVIEW_COMPLETE = "state:review-complete"
STATE_LABEL_FAILED = "state:failed"
STATE_LABEL_RETRY_REQUESTED = "state:retry-requested"
STATE_LABELS = (
    STATE_LABEL_NEEDS_REVIEW,
    STATE_LABEL_REVIEW_COMPLETE,
    STATE_LABEL_FAILED,
    STATE_LABEL_RETRY_REQUESTED,
)

CATEGORY_PATHS = {
    "개념정리": "concepts",
    "리서치 정리": "research",
    "정보 요약": "summaries",
}
DEFAULT_CATEGORY = "정보 요약"


@dataclass(frozen=True)
class AppConfig:
    repo: str
    docs_root: Path = Path("docs")
    default_branch: str = "main"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4"
    github_token: str | None = None
    reviewer_pool: frozenset[str] = field(default_factory=frozenset)
    requester_pool: frozenset[str] = field(default_factory=frozenset)
    enforce_requester_pool: bool = False
    state_labels: Sequence[str] = STATE_LABELS

    @classmethod
    def from_env(cls) -> "AppConfig":
        repo = os.environ.get("GITHUB_REPOSITORY", "")
        if not repo:
            raise ValueError("GITHUB_REPOSITORY is required")
        docs_root = Path(os.environ.get("DOCS_ROOT", "docs"))
        default_branch = os.environ.get("DEFAULT_BRANCH", "main")
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        openai_model = os.environ.get("OPENAI_MODEL", "gpt-5.4")
        github_token = os.environ.get("GITHUB_TOKEN")
        reviewer_pool = parse_identity_pool(os.environ.get("REVIEWER_POOL", ""))
        requester_pool = parse_identity_pool(os.environ.get("REQUESTER_POOL", ""))
        enforce_requester_pool = bool(requester_pool) and os.environ.get("ENFORCE_REQUESTER_POOL", "false").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        return cls(
            repo=repo,
            docs_root=docs_root,
            default_branch=default_branch,
            openai_api_key=openai_api_key,
            openai_model=openai_model,
            github_token=github_token,
            reviewer_pool=frozenset(reviewer_pool),
            requester_pool=frozenset(requester_pool),
            enforce_requester_pool=enforce_requester_pool,
        )


def parse_identity_pool(raw: str | None) -> list[str]:
    if not raw:
        return []
    cleaned = raw.replace("\n", ",").replace(";", ",")
    values = [value.strip().lstrip("@").lower() for value in cleaned.split(",")]
    return sorted({value for value in values if value})


def is_in_pool(login: str, pool: Iterable[str]) -> bool:
    normalized = login.strip().lstrip("@").lower()
    return normalized in {item.strip().lstrip("@").lower() for item in pool}
