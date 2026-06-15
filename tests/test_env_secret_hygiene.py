"""Static secret-hygiene guards (0174CJ_A).

These tests fail closed if local environment secret files become tracked in git
again, or if the .gitignore guard patterns are removed. They never open or read
the contents of any .env file — only git index/ignore *state* and the
.gitignore pattern text are inspected.
"""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _git(*args):
    return subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )


def test_env_files_not_tracked():
    """.env and .env.local must not be tracked in the git index."""
    res = _git("ls-files", ".env", ".env.local")
    tracked = [line for line in res.stdout.splitlines() if line.strip()]
    assert tracked == [], (
        f"Secret env files are tracked in git: {tracked}. "
        "Untrack them with `git rm --cached <file>` and keep them ignored."
    )


def test_env_files_are_ignored():
    """.env and .env.local must be matched by .gitignore."""
    for name in (".env", ".env.local"):
        res = _git("check-ignore", name)
        # check-ignore exits 0 and echoes the path when the file is ignored.
        assert res.returncode == 0 and name in res.stdout, (
            f"{name} is not ignored by .gitignore. Add a guard pattern."
        )


def test_gitignore_has_secret_guard_patterns():
    """.gitignore must declare the core secret/env guard patterns (UTF-8)."""
    gitignore = REPO_ROOT / ".gitignore"
    assert gitignore.is_file(), ".gitignore is missing"
    text = gitignore.read_text(encoding="utf-8")
    for pattern in (".env", ".env.local", ".env.*"):
        assert pattern in text, f".gitignore missing guard pattern: {pattern}"


def test_no_raw_env_contents_in_this_tasks_committed_files():
    """The files authored by this task must not contain secret-like values."""
    import re

    secret_like = [
        re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}"),   # telegram bot token body
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        re.compile(r"AKIA[0-9A-Z]{16}"),
        re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    ]
    task_files = [
        REPO_ROOT / ".gitignore",
        REPO_ROOT / "docs" / "credential_readiness" / "0174CJ_A_SECRET_HYGIENE.md",
        REPO_ROOT / "tests" / "test_env_secret_hygiene.py",
    ]
    for f in task_files:
        if not f.is_file():
            continue
        blob = f.read_text(encoding="utf-8")
        for pat in secret_like:
            assert not pat.search(blob), f"secret-like value found in {f.name}"
