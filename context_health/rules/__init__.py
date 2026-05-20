from __future__ import annotations

from context_health.models import Finding


def finding(
    *,
    id: str,
    title: str,
    severity: str,
    category: str,
    evidence: str,
    recommendation: str,
    path: str | None = None,
    line: int | None = None,
) -> Finding:
    return Finding(
        id=id,
        title=title,
        severity=severity,
        category=category,
        evidence=evidence,
        recommendation=recommendation,
        path=path,
        line=line,
    )


def find_line(text: str, needle: str) -> int | None:
    for index, line in enumerate(text.splitlines(), start=1):
        if needle.lower() in line.lower():
            return index
    return None
