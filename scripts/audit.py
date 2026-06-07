#!/usr/bin/env python3
"""
audit.py — Free static audit. No LLM, no Docker, no API calls.

Runs at Claude Code session start via hook. Checks for drift between
code and documentation, counts tests, finds TODOs, then appends findings
to STATUS.md and commits it. Skips if already run today.

Cost: $0.00
"""

import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"
STATUS = ROOT / "STATUS.md"
TESTS_DIR = BACKEND / "tests"
SCRIPTS_DIR = ROOT / "scripts"


def run(cmd: str, cwd=ROOT) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip()


def already_ran_today() -> bool:
    today = str(date.today())
    if not STATUS.exists():
        return False
    content = STATUS.read_text()
    return f"### {today}" in content


def count_tests() -> int:
    total = 0
    for f in TESTS_DIR.glob("test_*.py"):
        total += f.read_text().count("\ndef test_")
    return total


def find_todos() -> list[str]:
    findings = []
    for f in BACKEND.rglob("*.py"):
        for i, line in enumerate(f.read_text().splitlines(), 1):
            if "TODO" in line or "FIXME" in line:
                rel = f.relative_to(ROOT)
                findings.append(f"{rel}:{i}: {line.strip()}")
    return findings


def check_commands_md() -> list[str]:
    commands_md = (ROOT / "COMMANDS.md").read_text()
    missing = []
    for script in SCRIPTS_DIR.glob("*.sh"):
        if script.name not in commands_md:
            missing.append(script.name)
    return missing


def check_stale_google_key() -> bool:
    readme = (BACKEND / "README.md")
    if not readme.exists():
        return False
    content = readme.read_text()
    return "GOOGLE_API_KEY" in content and "required" in content.lower()


def check_status_test_count() -> tuple[int, int]:
    """Returns (actual_count, documented_count)."""
    actual = count_tests()
    documented = 0
    if STATUS.exists():
        for line in STATUS.read_text().splitlines():
            if "**Total**" in line and "|" in line:
                parts = [p.strip() for p in line.split("|")]
                for p in parts:
                    if p.isdigit():
                        documented = int(p)
                        break
    return actual, documented


def recent_git_log() -> str:
    return run("git log --oneline -5")


def build_findings() -> list[str]:
    findings = []

    # Test count drift
    actual, documented = check_status_test_count()
    if actual != documented and documented > 0:
        findings.append(
            f"TEST COUNT DRIFT: {actual} tests found, STATUS.md says {documented} — update STATUS.md"
        )

    # TODOs
    todos = find_todos()
    if todos:
        for t in todos[:5]:  # cap at 5 so STATUS.md doesn't explode
            findings.append(f"TODO: {t}")
        if len(todos) > 5:
            findings.append(f"... and {len(todos) - 5} more TODOs")

    # COMMANDS.md gaps
    missing_scripts = check_commands_md()
    if missing_scripts:
        findings.append(f"COMMANDS.md missing scripts: {', '.join(missing_scripts)}")

    # Stale GOOGLE_API_KEY
    if check_stale_google_key():
        findings.append("README still marks GOOGLE_API_KEY as required — it was removed")

    return findings


def append_to_status(findings: list[str]) -> None:
    today = str(date.today())
    git_log = recent_git_log()

    if findings:
        body = "\n".join(f"- {f}" for f in findings)
    else:
        body = "No issues found."

    entry = f"\n### {today}\n{body}\n\nRecent commits:\n```\n{git_log}\n```\n"

    content = STATUS.read_text()
    marker = "## Daily Audit Log"
    if marker in content:
        content = content.replace(marker, f"{marker}\n{entry}", 1)
    else:
        content += f"\n{marker}\n{entry}"

    STATUS.write_text(content)


def commit_status() -> None:
    run("git add STATUS.md")
    today = str(date.today())
    run(f'git commit -m "chore: daily audit {today}"')


def main():
    if already_ran_today():
        print(f"[audit] Already ran today — skipping.")
        sys.exit(0)

    print("[audit] Running static checks...")
    findings = build_findings()

    if findings:
        print(f"[audit] {len(findings)} finding(s):")
        for f in findings:
            print(f"  • {f}")
    else:
        print("[audit] No issues found.")

    append_to_status(findings)
    commit_status()
    print("[audit] STATUS.md updated and committed.")


if __name__ == "__main__":
    main()
