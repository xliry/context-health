from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import ROOT


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-m", "context_health.cli", *args], cwd=ROOT, text=True, capture_output=True)


def write_basic_node_repo(root: Path) -> None:
    (root / "README.md").write_text("Run with `npm run dev`.\nTest with `npm test`.\n", encoding="utf-8")
    (root / "AGENTS.md").write_text(
        "Install with `npm install`.\nRun with `npm run dev`.\nVerify with `npm test`.\n",
        encoding="utf-8",
    )
    (root / "package.json").write_text(
        json.dumps({"scripts": {"dev": "vite", "test": "vitest run"}}),
        encoding="utf-8",
    )
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "test.yml").write_text("name: test\n", encoding="utf-8")


def remove_ci(root: Path) -> None:
    (root / ".github" / "workflows" / "test.yml").unlink()
    (root / ".github" / "workflows").rmdir()
    (root / ".github").rmdir()


def finding_ids(result: subprocess.CompletedProcess[str]) -> set[str]:
    return {finding["id"] for finding in json.loads(result.stdout)["findings"]}


def test_no_config_profile_marks_config_file_null(tmp_path):
    write_basic_node_repo(tmp_path)

    result = run_cli(str(tmp_path), "--json")

    assert result.returncode == 0
    assert json.loads(result.stdout)["repo_profile"]["config_file"] is None


def test_config_exclude_suppresses_generated_artifact_finding(tmp_path):
    write_basic_node_repo(tmp_path)
    (tmp_path / "app.bundle.js").write_text("console.log('generated');\n", encoding="utf-8")

    without_config = run_cli(str(tmp_path), "--json")
    (tmp_path / ".context-health.toml").write_text('exclude = ["app.bundle.js"]\n', encoding="utf-8")
    with_config = run_cli(str(tmp_path), "--json")

    assert "context.generated_artifact_in_repo" in finding_ids(without_config)
    assert "context.generated_artifact_in_repo" not in finding_ids(with_config)
    assert json.loads(with_config.stdout)["repo_profile"]["config_file"] == ".context-health.toml"


def test_cli_max_file_kb_overrides_config(tmp_path):
    write_basic_node_repo(tmp_path)
    (tmp_path / "large.md").write_text("x" * 2048, encoding="utf-8")
    (tmp_path / ".context-health.toml").write_text("max_file_kb = 1\n", encoding="utf-8")

    from_config = run_cli(str(tmp_path), "--json")
    from_cli = run_cli(str(tmp_path), "--json", "--max-file-kb", "10")

    assert "context.large_file" in finding_ids(from_config)
    assert "context.large_file" not in finding_ids(from_cli)


def test_cli_include_and_exclude_extend_config(tmp_path):
    write_basic_node_repo(tmp_path)
    api_key = "API" + "_KEY"
    secret_key = "SECRET" + "_KEY"
    (tmp_path / "src" / "generated").mkdir(parents=True)
    (tmp_path / "src" / "app.py").write_text(f"import os\nos.getenv('{api_key}')\n", encoding="utf-8")
    (tmp_path / "src" / "generated" / "app.py").write_text(f"import os\nos.getenv('{secret_key}')\n", encoding="utf-8")
    (tmp_path / ".context-health.toml").write_text('include = ["README.md"]\n', encoding="utf-8")

    result = run_cli(str(tmp_path), "--json", "--include", "src/**", "--exclude", "src/generated/**")
    evidence = "\n".join(finding["evidence"] for finding in json.loads(result.stdout)["findings"])

    assert "env.missing_example" in finding_ids(result)
    assert api_key in evidence
    assert secret_key not in evidence


def test_config_fail_under_affects_exit_code(tmp_path):
    write_basic_node_repo(tmp_path)
    remove_ci(tmp_path)
    (tmp_path / ".context-health.toml").write_text("fail_under = 99\n", encoding="utf-8")

    result = run_cli(str(tmp_path))

    assert result.returncode == 1


def test_cli_fail_under_overrides_config(tmp_path):
    write_basic_node_repo(tmp_path)
    remove_ci(tmp_path)
    (tmp_path / ".context-health.toml").write_text("fail_under = 99\n", encoding="utf-8")

    result = run_cli(str(tmp_path), "--fail-under", "80")

    assert result.returncode == 0


@pytest.mark.parametrize(
    "config_text",
    (
        'include = "src/**"\n',
        "unknown = true\n",
        "max_file_kb = 0\n",
        "fail_under = 101\n",
    ),
)
def test_invalid_config_exits_2(tmp_path, config_text: str):
    write_basic_node_repo(tmp_path)
    (tmp_path / ".context-health.toml").write_text(config_text, encoding="utf-8")

    result = run_cli(str(tmp_path))

    assert result.returncode == 2
    assert ".context-health.toml" in result.stderr
