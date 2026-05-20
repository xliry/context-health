from __future__ import annotations

from collections import Counter

from context_health.models import Finding, RepoProfile, Report


WEIGHTS = {"critical": 25, "high": 15, "medium": 8, "low": 3}


def build_report(findings: list[Finding], profile: RepoProfile) -> Report:
    score = max(0, 100 - sum(WEIGHTS.get(f.severity, 0) for f in findings))
    verdict = "agent_ready" if score >= 80 else "needs_context_work" if score >= 50 else "context_blocked"
    return Report(score, verdict, tuple(findings), _summary(findings), profile, _recommendations(findings))


def _summary(findings: list[Finding]) -> dict[str, dict[str, int]]:
    return {
        "by_severity": dict(Counter(f.severity for f in findings)),
        "by_category": dict(Counter(f.category for f in findings)),
    }


def _recommendations(findings: list[Finding]) -> tuple[str, ...]:
    ordered = sorted(findings, key=lambda f: ({"critical": 0, "high": 1, "medium": 2, "low": 3}.get(f.severity, 9), f.id))
    seen: list[str] = []
    for item in ordered:
        if item.recommendation not in seen:
            seen.append(item.recommendation)
        if len(seen) == 3:
            break
    return tuple(seen)
