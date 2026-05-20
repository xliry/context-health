from __future__ import annotations

from context_health.models import ScanConfig
from context_health.rules import docs
from context_health.scanner import scan

from tests.conftest import FIXTURES


def ids(name: str) -> set[str]:
    return {f.id for f in docs.run(scan(ScanConfig(FIXTURES / name)))}


def test_healthy_docs_clean():
    assert ids("healthy_node") == set()


def test_blocked_missing_readme():
    assert "docs.missing_readme" in ids("blocked_node")
