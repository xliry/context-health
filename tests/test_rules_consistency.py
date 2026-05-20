from __future__ import annotations

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
