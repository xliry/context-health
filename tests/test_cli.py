from __future__ import annotations

import json
import subprocess
import sys

from tests.conftest import FIXTURES, ROOT


def run_cli(*args: str):
    return subprocess.run([sys.executable, "-m", "context_health.cli", *args], cwd=ROOT, text=True, capture_output=True)


def test_help():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "context readiness" in result.stdout


def test_json_markdown_and_fail_under(tmp_path):
    md = tmp_path / "blocked.md"
    result = run_cli(str(FIXTURES / "blocked_node"), "--json", "--markdown", str(md), "--fail-under", "80")
    assert result.returncode == 1
    assert md.exists()
    assert json.loads(result.stdout)["score"] < 80


def test_invalid_path_exits_2():
    result = run_cli(str(FIXTURES / "missing"))
    assert result.returncode == 2
