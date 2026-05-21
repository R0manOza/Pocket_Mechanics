"""Run cross-user isolation checks and write terminal evidence for safety-audit.md."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "evidence" / "isolation-test-output.txt"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_session_service.py::TestSessionService::test_session_isolation",
        "-v",
        "--tb=short",
    ]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    body = (
        "# Cross-user session isolation (pytest)\n\n"
        f"Command: {' '.join(cmd)}\n\n"
        f"Exit code: {result.returncode}\n\n"
        "## stdout\n```\n"
        f"{result.stdout}\n```\n\n"
        "## stderr\n```\n"
        f"{result.stderr}\n```\n"
    )
    OUT.write_text(body, encoding="utf-8")
    print(body)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
