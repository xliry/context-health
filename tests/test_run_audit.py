from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from context_health.run_audit import _diff_stats, build_run_audit_report, run_audit_rules, scan_run_artifacts
from context_health.run_models import RunAuditConfig, RunCostRisk, RunFinding, RunProfile
from context_health.run_report import render_run_json, render_run_markdown

from tests.conftest import FIXTURES, ROOT


def run_cli(*args: str):
    return subprocess.run([sys.executable, "-m", "context_health.cli", *args], cwd=ROOT, text=True, capture_output=True)


def audit_fixture(name: str):
    snapshot = scan_run_artifacts(RunAuditConfig(FIXTURES / name))
    return build_run_audit_report(run_audit_rules(snapshot), snapshot.profile, snapshot.cost_risk)


def test_good_run_scores_ready():
    report = audit_fixture("agent_run_good")
    assert report.score >= 80
    assert report.verdict == "handoff_ready"
    assert report.profile.has_handoff
    assert report.profile.has_diff
    assert report.profile.has_context_health_report


def test_missing_handoff_emits_high_finding():
    report = audit_fixture("agent_run_missing_handoff")
    assert any(finding.id == "handoff.missing_handoff" and finding.severity == "high" for finding in report.findings)


def test_risky_run_flags_failed_commands_and_sensitive_paths():
    report = audit_fixture("agent_run_risky")
    ids = {finding.id for finding in report.findings}
    assert "verification.failed_commands" in ids
    assert "diff.sensitive_paths" in ids
    assert ".env.local" in report.cost_risk.suspicious_paths
    assert report.score < 80


def test_diff_stats_count_changed_files_and_lines():
    text = (FIXTURES / "agent_run_good" / "changes.diff").read_text(encoding="utf-8")
    stats = _diff_stats(text)
    assert stats.files == frozenset({"context_health/run_models.py", "context_health/run_report.py"})
    assert stats.added == 5
    assert stats.removed == 0


def test_json_renderer_is_parseable():
    report = audit_fixture("agent_run_good")
    data = json.loads(render_run_json(report))
    assert data["score"] == report.score
    assert data["run_profile"]["has_handoff"] is True
    assert "cost_risk" in data


def test_markdown_renderer_contains_findings():
    report = audit_fixture("agent_run_risky")
    markdown = render_run_markdown(report)
    assert "# Context Health Run Audit" in markdown
    assert "verification.failed_commands" in markdown
    assert "What To Review First" in markdown


def test_score_verdict_boundaries():
    profile = RunProfile()
    cost_risk = RunCostRisk()
    high = RunFinding("a", "A", "high", "test", "evidence", "fix")
    many = [RunFinding(str(index), "A", "critical", "test", f"evidence {index}", "fix") for index in range(3)]
    assert build_run_audit_report([], profile, cost_risk).verdict == "handoff_ready"
    assert build_run_audit_report([high, high], profile, cost_risk).verdict == "review_needed"
    assert build_run_audit_report(many, profile, cost_risk).verdict == "handoff_blocked"


def test_cli_run_audit_terminal():
    result = run_cli("run-audit", str(FIXTURES / "agent_run_good"))
    assert result.returncode == 0
    assert "Context Health Run Audit" in result.stdout
    assert "Cost/risk estimate" in result.stdout


def test_cli_run_audit_normal_fixture_still_works():
    result = run_cli("run-audit", str(FIXTURES / "agent_run_good"), "--fail-under", "80")
    assert result.returncode == 0
    assert "handoff_ready" in result.stdout


def test_cli_run_audit_json():
    result = run_cli("run-audit", str(FIXTURES / "agent_run_good"), "--json")
    assert result.returncode == 0
    assert json.loads(result.stdout)["verdict"] == "handoff_ready"


def test_cli_run_audit_markdown_and_fail_under(tmp_path):
    markdown = tmp_path / "run-audit.md"
    result = run_cli("run-audit", str(FIXTURES / "agent_run_risky"), "--markdown", str(markdown), "--fail-under", "80")
    assert result.returncode == 1
    assert markdown.exists()
    assert "diff.sensitive_paths" in markdown.read_text(encoding="utf-8")


def test_cli_run_audit_invalid_path_exits_2():
    result = run_cli("run-audit", str(FIXTURES / "missing-run"))
    assert result.returncode == 2
    assert "does not exist" in result.stderr


def test_cli_run_audit_rejects_sensitive_root_path():
    sensitive = _platform_sensitive_path()
    result = run_cli("run-audit", str(sensitive))
    assert result.returncode == 2
    assert "sensitive" in result.stderr.lower()


def test_cli_run_audit_rejects_sensitive_repo_path():
    sensitive = _platform_sensitive_path()
    result = run_cli("run-audit", str(FIXTURES / "agent_run_good"), "--repo", str(sensitive))
    assert result.returncode == 2
    assert "sensitive" in result.stderr.lower()


def _platform_sensitive_path() -> Path:
    if sys.platform == "win32":
        windows = Path("C:/Windows")
        return windows if windows.exists() else Path("C:/")
    return Path("/")
