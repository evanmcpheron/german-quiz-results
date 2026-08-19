#!/usr/bin/env python3
"""Advisory, dependency-free check: warn when a commit touches tracker data
alongside files outside the assessment agent's write scope (see AGENTS.md's
"Write scope" section). This check never fails the build; it only warns.
"""

from __future__ import annotations

import os
import subprocess
import sys

DATA_PREFIX = "data/"

NON_WRITABLE_PREFIXES = (
    "QUIZ.md",
    "AGENTS.md",
    "README.md",
    "manifest.json",
    "config/",
    "schemas/",
    "tools/",
    ".github/",
)

NULL_SHA = "0000000000000000000000000000000000000000"


def is_non_writable(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in NON_WRITABLE_PREFIXES)


def find_violations(changed_files: list[str]) -> list[str]:
    touches_data = any(path.startswith(DATA_PREFIX) for path in changed_files)
    if not touches_data:
        return []
    return sorted(path for path in changed_files if is_non_writable(path))


def get_changed_files(base_sha: str, head_sha: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", base_sha, head_sha],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def main() -> int:
    base_sha = os.environ.get("BASE_SHA", "")
    head_sha = os.environ.get("HEAD_SHA", "")

    if not base_sha or base_sha == NULL_SHA or not head_sha:
        print("check_write_scope: no prior commit to diff against, skipping.")
        return 0

    changed_files = get_changed_files(base_sha, head_sha)
    violations = find_violations(changed_files)

    if violations:
        print(
            "WARNING: this change touches tracker data alongside files outside the "
            "assessment agent's write scope (see AGENTS.md 'Write scope'):"
        )
        for path in violations:
            print(f"  - {path}")
        print("This is advisory only and does not fail the build. Confirm this was intentional.")
    else:
        print("check_write_scope: no write-scope violations found.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
