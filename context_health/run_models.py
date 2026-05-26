from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunAuditConfig:
    root: Path
    repo: Path | None = None
    max_file_kb: int = 512
    verbose: bool = False


@dataclass(frozen=True)
class RunArtifact:
    path: str
    size_bytes: int
    suffix: str
    kind: str
    is_text: bool
    preview: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "size_bytes": self.size_bytes,
            "suffix": self.suffix,
            "kind": self.kind,
            "is_text": self.is_text,
        }


@dataclass(frozen=True)
class RunProfile:
    artifact_count: int = 0
    markdown_count: int = 0
    json_count: int = 0
    log_count: int = 0
    diff_count: int = 0
    has_handoff: bool = False
    has_transcript: bool = False
    has_diff: bool = False
    has_context_health_report: bool = False
    detected_sections: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_count": self.artifact_count,
            "markdown_count": self.markdown_count,
            "json_count": self.json_count,
            "log_count": self.log_count,
            "diff_count": self.diff_count,
            "has_handoff": self.has_handoff,
            "has_transcript": self.has_transcript,
            "has_diff": self.has_diff,
            "has_context_health_report": self.has_context_health_report,
            "detected_sections": list(self.detected_sections),
        }


@dataclass(frozen=True)
class RunCostRisk:
    estimated_tokens: int = 0
    transcript_chars: int = 0
    command_markers: int = 0
    failed_command_markers: int = 0
    diff_files_changed: int = 0
    diff_added_lines: int = 0
    diff_removed_lines: int = 0
    suspicious_paths: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "estimated_tokens": self.estimated_tokens,
            "transcript_chars": self.transcript_chars,
            "command_markers": self.command_markers,
            "failed_command_markers": self.failed_command_markers,
            "diff_files_changed": self.diff_files_changed,
            "diff_added_lines": self.diff_added_lines,
            "diff_removed_lines": self.diff_removed_lines,
            "suspicious_paths": list(self.suspicious_paths),
        }


@dataclass(frozen=True)
class RunFinding:
    id: str
    title: str
    severity: str
    category: str
    evidence: str
    recommendation: str
    path: str | None = None
    line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "category": self.category,
            "path": self.path,
            "line": self.line,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
        }


@dataclass(frozen=True)
class RunSnapshot:
    root: Path
    config: RunAuditConfig
    artifacts: tuple[RunArtifact, ...]
    profile: RunProfile
    cost_risk: RunCostRisk
    texts: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RunAuditReport:
    score: int
    verdict: str
    findings: tuple[RunFinding, ...]
    summary: dict[str, dict[str, int]]
    profile: RunProfile
    cost_risk: RunCostRisk
    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "verdict": self.verdict,
            "summary": self.summary,
            "run_profile": self.profile.to_dict(),
            "cost_risk": self.cost_risk.to_dict(),
            "recommendations": list(self.recommendations),
            "findings": [finding.to_dict() for finding in self.findings],
        }
