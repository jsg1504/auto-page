from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request


class GitHubApiError(RuntimeError):
    pass


class GitHubApi:
    def __init__(self, repo: str, token: str | None) -> None:
        self.repo = repo
        self.token = token

    def add_labels(self, issue_number: int, labels: list[str]) -> None:
        if not labels:
            return
        self._request(
            f"/repos/{self.repo}/issues/{issue_number}/labels",
            method="POST",
            payload={"labels": labels},
        )

    def remove_label(self, issue_number: int, label: str) -> None:
        encoded = urllib.parse.quote(label, safe="")
        try:
            self._request(f"/repos/{self.repo}/issues/{issue_number}/labels/{encoded}", method="DELETE")
        except GitHubApiError as exc:
            if "404" not in str(exc):
                raise

    def list_comments(self, issue_number: int) -> list[dict]:
        response = self._request(f"/repos/{self.repo}/issues/{issue_number}/comments", method="GET")
        return response or []

    def post_comment(self, issue_number: int, body: str) -> None:
        self._request(
            f"/repos/{self.repo}/issues/{issue_number}/comments",
            method="POST",
            payload={"body": body},
        )

    def _request(self, path: str, method: str = "GET", payload: dict | None = None):
        if not self.token:
            raise GitHubApiError("GITHUB_TOKEN is required")
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            f"https://api.github.com{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else None
        except urllib.error.HTTPError as exc:  # pragma: no cover - network path
            error_body = exc.read().decode("utf-8", errors="replace")
            raise GitHubApiError(f"GitHub API request failed ({exc.code}): {error_body}") from exc
