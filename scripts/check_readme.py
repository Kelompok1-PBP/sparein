"""Fail CI when the documentation the course requires drifts out of the repo.

The midterm brief names seven things the README must carry, plus the
supporting documents this team agreed to keep. Run it with
`python scripts/check_readme.py` from the repository root.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Section heading -> what the course brief is asking for.
README_SECTIONS = {
    "## Overview": "application description",
    "## Team & Module PIC": "member names and NPM",
    "## Module Map": "module list and per-member split",
    "## Public API & Mock API": "public or mock API source",
    "## User Roles": "user roles",
    "## Links": "PWS deployment and Figma links",
}

# Every member must appear with their NPM, or the submission is incomplete.
MEMBERS = {
    "2506534876": "Muhammad Sultan Zidan",
    "2506612266": "Kevin Fauzan Arjuna",
    "2506594692": "Hanna Zerlina Razaq Putri Wicaksono",
    "2506586236": "Muhamad Ayrazhan",
    "2506537606": "Marsya Rizka Aulia",
}

REQUIRED_FILES = [
    "README.md",
    "CONTRIBUTING.md",
    "docs/MODULES.md",
    "docs/DESIGN-SYSTEM.md",
    "docs/RISKS.md",
    "docs/brand/sparein-icon.svg",
    "docs/brand/sparein-wordmark.svg",
    "docs/brand/sparein-lockup.svg",
    "docs/brand/sparein-lockup-dark.svg",
    "docs/brand/palette.svg",
    ".github/workflows/ci.yml",
    ".github/workflows/pr-guard.yml",
    ".github/workflows/deploy-pws.yml",
]

# A credential that reaches a public repo is not recoverable by deleting it.
CREDENTIAL_PATTERN = re.compile(r"https://[^\s/:]+:[^\s/@]+@pws\.cs\.ui\.ac\.id")


def check() -> list[str]:
    problems: list[str] = []

    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            problems.append(f"missing file: {relative}")

    readme_path = ROOT / "README.md"
    if not readme_path.is_file():
        return problems

    readme = readme_path.read_text(encoding="utf-8")

    for heading, requirement in README_SECTIONS.items():
        if heading not in readme:
            problems.append(f"README.md is missing '{heading}' ({requirement})")

    for npm, name in MEMBERS.items():
        if npm not in readme:
            problems.append(f"README.md is missing NPM {npm} ({name})")
        if name not in readme:
            problems.append(f"README.md is missing member name: {name}")

    # The brief requires an external public API or a self-made mock API.
    if "ifixit.com/api" not in readme.lower():
        problems.append("README.md does not document the external public API endpoint")

    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.is_file() or path.suffix not in {".md", ".yml", ".yaml", ".py"}:
            continue
        if CREDENTIAL_PATTERN.search(path.read_text(encoding="utf-8")):
            problems.append(f"{relative} contains what looks like a PWS credential")

    return problems


def main() -> int:
    problems = check()
    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        print(f"\n{len(problems)} documentation problem(s) found.", file=sys.stderr)
        return 1
    print(f"Documentation contract OK: {len(REQUIRED_FILES)} files, "
          f"{len(README_SECTIONS)} README sections, {len(MEMBERS)} members.")
    return 0


def _self_test() -> None:
    """Prove the checker actually fails on bad input, not just on good input."""
    assert CREDENTIAL_PATTERN.search(
        "https://hanni.pham:abcd1234@pws.cs.ui.ac.id/hanni.pham/sparein"
    ), "credential pattern must catch an inline PWS URL"
    assert not CREDENTIAL_PATTERN.search(
        "https://pws.cs.ui.ac.id/hanni.pham/sparein"
    ), "credential pattern must not flag a plain PWS URL"
    assert check() == [], "repository must satisfy its own documentation contract"
    print("self-test OK")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        _self_test()
        raise SystemExit(0)
    raise SystemExit(main())
