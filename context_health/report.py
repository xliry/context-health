from __future__ import annotations

import json

from context_health.models import Report


def render_json(report: Report) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"


def render_terminal(report: Report) -> str:
    lines = [f"Context Health: {report.score}/100 - {report.verdict}", ""]
    if report.findings:
        lines.append("Top findings:")
        for finding in report.findings[:8]:
            lines.append(f"  [{finding.severity}] {finding.id}")
            lines.append(f"    {finding.evidence}")
            lines.append(f"    fix: {finding.recommendation}")
            lines.append("")
    else:
        lines.extend(["No context blockers found.", ""])
    if report.recommendations:
        lines.append("Next actions:")
        for index, recommendation in enumerate(report.recommendations, start=1):
            lines.append(f"  {index}. {recommendation}")
    return "\n".join(lines).rstrip() + "\n"


def render_markdown(report: Report) -> str:
    lines = [
        "# Context Health Report",
        "",
        f"- Score: `{report.score}/100`",
        f"- Verdict: `{report.verdict}`",
        f"- Ecosystems: `{', '.join(report.profile.ecosystems)}`",
        f"- Package manager: `{report.profile.package_manager or 'unknown'}`",
        "",
        "## Findings",
        "",
    ]
    if not report.findings:
        lines.append("No findings.")
    for finding in report.findings:
        lines.extend(
            [
                f"### [{finding.severity}] {finding.id}",
                "",
                f"- Title: {finding.title}",
                f"- Category: `{finding.category}`",
                f"- Path: `{finding.path or 'repo'}`",
                f"- Line: `{finding.line or 'n/a'}`",
                f"- Evidence: {finding.evidence}",
                f"- Recommendation: {finding.recommendation}",
                "",
            ]
        )
    lines.extend(["## Next Actions", ""])
    if report.recommendations:
        for index, recommendation in enumerate(report.recommendations, start=1):
            lines.append(f"{index}. {recommendation}")
    else:
        lines.append("No action needed.")
    return "\n".join(lines).rstrip() + "\n"
