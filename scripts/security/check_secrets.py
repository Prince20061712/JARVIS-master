#!/usr/bin/env python3
"""Scan staged files for likely secrets before commit."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Conservative high-signal patterns; avoids noisy generic words.
SECRET_PATTERNS = [
    ("Groq API key", re.compile(r"gsk_[A-Za-z0-9]{20,}")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z_\-]{20,}")),
    ("OpenAI API key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("GitHub token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("Slack token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("Private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
]

# Paths allowed to contain dummy examples.
ALLOWLIST_PATHS = {
    ".env.example",
    "jarvis-system/backend/.env.example",
}

# Lines allowed to contain empty placeholders.
PLACEHOLDER_LINE = re.compile(r"^[A-Z0-9_]+\s*=\s*$")


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def staged_files() -> list[str]:
    output = _run_git("diff", "--cached", "--name-only", "--diff-filter=ACMRT")
    return [line.strip() for line in output.splitlines() if line.strip()]


def staged_content(path: str) -> str:
    return _run_git("show", f":{path}")


def scan() -> list[str]:
    findings: list[str] = []

    for rel_path in staged_files():
        # Skip binary files and vendored deps if they somehow get staged.
        if rel_path.startswith((".venv/", "venv/", "node_modules/", "test_env/")):
            continue

        try:
            content = staged_content(rel_path)
        except subprocess.CalledProcessError:
            continue

        for idx, line in enumerate(content.splitlines(), start=1):
            # Allow empty env placeholders in the example file.
            if rel_path in ALLOWLIST_PATHS and PLACEHOLDER_LINE.match(line.strip()):
                continue

            for label, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(f"{rel_path}:{idx} -> {label}")

    return findings


def main() -> int:
    try:
        findings = scan()
    except subprocess.CalledProcessError as exc:
        print(f"[secrets-check] Unable to inspect staged files: {exc}")
        return 1

    if not findings:
        print("[secrets-check] OK: no high-signal secrets detected in staged changes.")
        return 0

    print("[secrets-check] Blocked commit: possible secrets found in staged content:")
    for finding in findings:
        print(f"  - {finding}")
    print("\nRemove/rotate leaked keys, keep real values in untracked .env files, and try again.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
