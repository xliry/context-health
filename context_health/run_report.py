from __future__ import annotations

import json

from context_health.run_models import RunAuditReport


def render_run_json(report: RunAuditReport) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"


def render_run_terminal(report: RunAuditReport) -> str:
    lines = [f"Context Health Run Audit: {report.score}/100 - {report.verdict}", ""]
    lines.extend(
        [
            "Run profile:",
            f"  artifacts: {report.profile.artifact_count}",
            f"  handoff: {_yes_no(report.profile.has_handoff)}",
            f"  transcript: {_yes_no(report.profile.has_transcript)}",
            f"  diff: {_yes_no(report.profile.has_diff)}",
            f"  context health report: {_yes_no(report.profile.has_context_health_report)}",
            "",
            "Cost/risk estimate (heuristic):",
            f"  estimated tokens: {report.cost_risk.estimated_tokens}",
            f"  changed files: {report.cost_risk.diff_files_changed}",
            f"  added/removed lines: {report.cost_risk.diff_added_lines}/{report.cost_risk.diff_removed_lines}",
            f"  failed command markers: {report.cost_risk.failed_command_markers}",
            "",
        ]
    )
    if report.findings:
        lines.append("Top findings:")
        for finding in report.findings[:8]:
            lines.append(f"  [{finding.severity}] {finding.id}")
            lines.append(f"    {finding.evidence}")
            lines.append(f"    fix: {finding.recommendation}")
            lines.append("")
    else:
        lines.extend(["No handoff blockers found.", ""])
    if report.recommendations:
        lines.append("Next actions:")
        for index, recommendation in enumerate(report.recommendations, start=1):
            lines.append(f"  {index}. {recommendation}")
    return "\n".join(lines).rstrip() + "\n"


def render_run_markdown(report: RunAuditReport) -> str:
    lines = [
        "# Context Health Run Audit",
        "",
        f"- Score: `{report.score}/100`",
        f"- Verdict: `{report.verdict}`",
        "- Cost/risk estimate: `heuristic`",
        "",
        "## Run Profile",
        "",
        f"- Artifacts: `{report.profile.artifact_count}`",
        f"- Markdown files: `{report.profile.markdown_count}`",
        f"- JSON files: `{report.profile.json_count}`",
        f"- Logs/transcripts: `{report.profile.log_count}`",
        f"- Diffs/patches: `{report.profile.diff_count}`",
        f"- Handoff found: `{_yes_no(report.profile.has_handoff)}`",
        f"- Context Health report found: `{_yes_no(report.profile.has_context_health_report)}`",
        f"- Detected sections: `{', '.join(report.profile.detected_sections) or 'none'}`",
        "",
        "## Cost/Risk Estimate",
        "",
        f"- Estimated tokens: `{report.cost_risk.estimated_tokens}`",
        f"- Transcript characters: `{report.cost_risk.transcript_chars}`",
        f"- Command markers: `{report.cost_risk.command_markers}`",
        f"- Failed command markers: `{report.cost_risk.failed_command_markers}`",
        f"- Diff files changed: `{report.cost_risk.diff_files_changed}`",
        f"- Diff added lines: `{report.cost_risk.diff_added_lines}`",
        f"- Diff removed lines: `{report.cost_risk.diff_removed_lines}`",
        f"- Suspicious paths: `{', '.join(report.cost_risk.suspicious_paths) or 'none'}`",
        "",
        "## Findings",
        "",
    ]
    if not report.findings:
        lines.extend(["No findings.", ""])
    for finding in report.findings:
        lines.extend(
            [
                f"### [{finding.severity}] {finding.id}",
                "",
                f"- Title: {finding.title}",
                f"- Category: `{finding.category}`",
                f"- Path: `{finding.path or 'run artifacts'}`",
                f"- Line: `{finding.line or 'n/a'}`",
                f"- Evidence: {finding.evidence}",
                f"- Recommendation: {finding.recommendation}",
                "",
            ]
        )
    lines.extend(["## What To Review First", ""])
    if report.findings:
        for finding in report.findings[:3]:
            lines.append(f"- `{finding.id}`: {finding.evidence}")
    else:
        lines.append("- Review the diff and verification output using the handoff as the map.")
    lines.extend(["", "## Next Actions", ""])
    if report.recommendations:
        for index, recommendation in enumerate(report.recommendations, start=1):
            lines.append(f"{index}. {recommendation}")
    else:
        lines.append("No action needed.")
    return "\n".join(lines).rstrip() + "\n"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
