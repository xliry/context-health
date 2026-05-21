from __future__ import annotations

import json

from context_health.models import ScanConfig
from context_health.rules import agent_instructions
from context_health.scanner import scan

from tests.conftest import FIXTURES


def test_healthy_agent_instructions_clean():
    assert agent_instructions.run(scan(ScanConfig(FIXTURES / "healthy_node"))) == []


def test_blocked_missing_agent_instructions():
    findings = agent_instructions.run(scan(ScanConfig(FIXTURES / "blocked_node")))
    assert "agent.missing_instructions" in {f.id for f in findings}


def test_vague_agent_instructions_report_missing_quality_hints(tmp_path):
    findings = agent_instructions.run(scan(ScanConfig(FIXTURES / "vague_agent_instructions")))
    ids = {f.id for f in findings}

    assert "agent.instructions_missing_setup" in ids
    assert "agent.instructions_missing_run" in ids
    assert "agent.instructions_missing_tests" in ids


def test_complete_agent_instructions_have_no_quality_findings(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"dev": "vite", "test": "vitest run"}}),
        encoding="utf-8",
    )
    (tmp_path / "AGENTS.md").write_text(
        "Install with `pnpm install`.\nRun with `pnpm dev`.\nVerify with `pnpm test`.\n",
        encoding="utf-8",
    )

    findings = agent_instructions.run(scan(ScanConfig(tmp_path)))

    assert not {f.id for f in findings} & {
        "agent.instructions_missing_setup",
        "agent.instructions_missing_run",
        "agent.instructions_missing_tests",
    }
