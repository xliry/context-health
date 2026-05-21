from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


Severity = str
Verdict = str


@dataclass(frozen=True)
class ScanConfig:
    root: Path
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    max_file_kb: int = 512
    verbose: bool = False
    config_file: str | None = None


@dataclass(frozen=True)
class FileInfo:
    path: str
    size_bytes: int
    suffix: str
    is_text: bool
    preview: str = ""


@dataclass(frozen=True)
class RepoProfile:
    ecosystems: tuple[str, ...] = ()
    package_manager: str | None = None
    workspaces: tuple[str, ...] = ()
    config_file: str | None = None
    has_readme: bool = False
    has_env_example: bool = False
    has_ci: bool = False
    scripts: dict[str, str] = field(default_factory=dict)
    important_files: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ecosystems": list(self.ecosystems),
            "package_manager": self.package_manager,
            "workspaces": list(self.workspaces),
            "config_file": self.config_file,
            "has_readme": self.has_readme,
            "has_env_example": self.has_env_example,
            "has_ci": self.has_ci,
            "scripts": dict(self.scripts),
            "important_files": list(self.important_files),
        }


@dataclass(frozen=True)
class Finding:
    id: str
    title: str
    severity: Severity
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
class RepoSnapshot:
    root: Path
    config: ScanConfig
    files: tuple[FileInfo, ...]
    profile: RepoProfile
    texts: dict[str, str] = field(default_factory=dict)

    def has_file(self, path: str) -> bool:
        return any(file.path == path for file in self.files)

    def find_text(self, *names: str) -> tuple[str | None, str]:
        lowered = {name.lower() for name in names}
        for path, text in self.texts.items():
            if path.lower() in lowered:
                return path, text
        return None, ""


@dataclass(frozen=True)
class Report:
    score: int
    verdict: Verdict
    findings: tuple[Finding, ...]
    summary: dict[str, dict[str, int]]
    profile: RepoProfile
    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "verdict": self.verdict,
            "summary": self.summary,
            "repo_profile": self.profile.to_dict(),
            "recommendations": list(self.recommendations),
            "findings": [finding.to_dict() for finding in self.findings],
        }
