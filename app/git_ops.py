from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


class GitPublisher:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def commit_and_push(self, paths: list[Path], message: str, push: bool = True) -> bool:
        normalized_paths = [(self.repo_root / path).resolve() if not path.is_absolute() else path.resolve() for path in paths]
        relative_paths = [str(path.relative_to(self.repo_root.resolve())) for path in normalized_paths]
        self._run(["git", "config", "user.name", "github-actions[bot]"])
        self._run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"])
        self._run(["git", "add", *relative_paths])
        if not self._has_staged_changes():
            return False
        self._run(["git", "commit", "-m", message])
        if push:
            self._run(["git", "push"])
        return True

    def _has_staged_changes(self) -> bool:
        result = self._run(["git", "diff", "--cached", "--quiet"], check=False)
        return result.returncode != 0

    def _run(self, command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            command,
            cwd=self.repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode != 0:
            raise GitError(f"Command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
        return result
