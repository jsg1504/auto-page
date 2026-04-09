from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from app.git_ops import GitPublisher


class GitOpsTests(unittest.TestCase):
    def test_commit_and_push_without_changes_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            subprocess.run(["git", "init", "-b", "main"], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Tester"], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=repo_root, check=True, capture_output=True)
            file_path = repo_root / "README.md"
            file_path.write_text("hello\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True)
            publisher = GitPublisher(repo_root)
            self.assertFalse(publisher.commit_and_push([file_path], "noop", push=False))

    def test_commit_and_push_accepts_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            subprocess.run(["git", "init", "-b", "main"], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Tester"], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=repo_root, check=True, capture_output=True)
            file_path = repo_root / "docs" / "index.md"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("one\n", encoding="utf-8")
            subprocess.run(["git", "add", "docs/index.md"], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True)
            file_path.write_text("two\n", encoding="utf-8")
            publisher = GitPublisher(repo_root)
            self.assertTrue(publisher.commit_and_push([Path("docs/index.md")], "update", push=False))


if __name__ == "__main__":
    unittest.main()
