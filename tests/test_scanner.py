from __future__ import annotations

from context_health.models import Finding, ScanConfig
from context_health.scanner import scan

from tests.conftest import FIXTURES


def test_finding_serializes_required_fields():
    data = Finding("x.y", "Title", "low", "docs", "evidence", "fix").to_dict()
    assert {"id", "title", "severity", "category", "evidence", "recommendation"} <= data.keys()


def test_detects_node_profile_and_ignores_dependencies():
    snapshot = scan(ScanConfig(FIXTURES / "healthy_node"))
    assert "node" in snapshot.profile.ecosystems
    assert snapshot.profile.package_manager == "pnpm"
    assert "node_modules/ignored.js" not in {file.path for file in snapshot.files}


def test_detects_python_profile():
    snapshot = scan(ScanConfig(FIXTURES / "python_missing_env"))
    assert "python" in snapshot.profile.ecosystems
    assert snapshot.profile.has_readme
