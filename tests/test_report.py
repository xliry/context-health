from __future__ import annotations

import json

from context_health.models import ScanConfig
from context_health.report import render_json, render_markdown
from context_health.scanner import run_rules, scan
from context_health.scoring import build_report

from tests.conftest import FIXTURES


def test_json_and_markdown_render():
    snapshot = scan(ScanConfig(FIXTURES / "blocked_node"))
    report = build_report(run_rules(snapshot), snapshot.profile)
    parsed = json.loads(render_json(report))
    assert parsed["score"] < 80
    md = render_markdown(report)
    assert "# Context Health Report" in md
    assert "docs.missing_readme" in md
