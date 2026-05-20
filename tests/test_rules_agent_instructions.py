from __future__ import annotations

from context_health.models import ScanConfig
from context_health.rules import agent_instructions
from context_health.scanner import scan

from tests.conftest import FIXTURES


def test_healthy_agent_instructions_clean():
    assert agent_instructions.run(scan(ScanConfig(FIXTURES / "healthy_node"))) == []


def test_blocked_missing_agent_instructions():
    findings = agent_instructions.run(scan(ScanConfig(FIXTURES / "blocked_node")))
    assert "agent.missing_instructions" in {f.id for f in findings}
