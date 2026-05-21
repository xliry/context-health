from __future__ import annotations

import json

from context_health.models import ScanConfig
from context_health.rules import consistency
from context_health.scanner import scan

from tests.conftest import FIXTURES


def test_conflicting_package_managers_and_agents():
    findings = consistency.run(scan(ScanConfig(FIXTURES / "conflicting_agents")))
    ids = {f.id for f in findings}
    assert "consistency.conflicting_package_manager" in ids
    assert "consistency.multiple_agent_instructions_possible_conflict" in ids


def test_healthy_has_no_consistency_mismatch():
    assert consistency.run(scan(ScanConfig(FIXTURES / "healthy_node"))) == []


def test_readme_agents_command_mismatch(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps({"packageManager": "pnpm@9.0.0"}),
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("Verify with `pnpm test`.\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("Verify with `npm test`.\n", encoding="utf-8")

    findings = consistency.run(scan(ScanConfig(tmp_path)))

    assert "consistency.agent_readme_command_mismatch" in {f.id for f in findings}
