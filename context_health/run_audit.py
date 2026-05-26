from __future__ import annotations

import fnmatch
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from context_health.run_models import (
    RunArtifact,
    RunAuditConfig,
    RunAuditReport,
    RunCostRisk,
    RunFinding,
    RunProfile,
    RunSnapshot,
)


WEIGHTS = {"critical": 25, "high": 15, "medium": 8, "low": 3}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
DEFAULT_IGNORES = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", "dist", "build", "coverage", ".cache"}
TEXT_SUFFIXES = {".md", ".txt", ".log", ".json", ".jsonl", ".patch", ".diff", ".yaml", ".yml", ".toml"}
HANDOFF_SECTION_HINTS = {"what i built", "verification results", "what didn't work", "what did not work", "files changed", "summary"}
VERIFICATION_TERMS = ("pytest", "npm test", "pnpm test", "context-health", "ruff", "mypy", "go test", "cargo test")
FAILURE_RE = re.compile(r"\b(FAILED|ERROR|Traceback|Command failed|npm ERR!)\b|Exit code:\s*[1-9]\d*|failed,?\s+\d+", re.IGNORECASE)
COMMAND_RE = re.compile(r"(?m)^\s*(?:\$|>)\s+\S+|\b(?:Command:|Running|Exit code:)\b")
SENSITIVE_PATTERNS = (
    ".env",
    ".env.*",
    ".ssh/*",
    ".aws/*",
    ".gnupg/*",
    "*id_rsa*",
    "*id_ed25519*",
    "*.pem",
    "*.key",
    "secrets.*",
    "*credentials*",
)
GENERATED_PATTERNS = ("node_modules/*", "dist/*", "build/*", "coverage/*", "*.min.js", "*.bundle.js")
LOCKFILES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "uv.lock", "Cargo.lock"}


@dataclass(frozen=True)
class DiffStats:
    files: frozenset[str]
    added: int
    removed: int


def scan_run_artifacts(config: RunAuditConfig) -> RunSnapshot:
    artifacts, texts = _walk_run_artifacts(config)
    profile = _profile_run(artifacts, texts)
    cost_risk = _cost_risk(texts)
    return RunSnapshot(config.root, config, tuple(artifacts), profile, cost_risk, texts)


def run_audit_rules(snapshot: RunSnapshot) -> list[RunFinding]:
    findings: list[RunFinding] = []
    findings.extend(_handoff_rules(snapshot))
    findings.extend(_verification_rules(snapshot))
    findings.extend(_diff_rules(snapshot))
    findings.extend(_cost_rules(snapshot))
    return _dedupe_and_sort(findings)


def build_run_audit_report(findings: list[RunFinding], profile: RunProfile, cost_risk: RunCostRisk) -> RunAuditReport:
    score = max(0, 100 - sum(WEIGHTS.get(finding.severity, 0) for finding in findings))
    verdict = "handoff_ready" if score >= 80 else "review_needed" if score >= 50 else "handoff_blocked"
    return RunAuditReport(score, verdict, tuple(findings), _summary(findings), profile, cost_risk, _recommendations(findings))


def _walk_run_artifacts(config: RunAuditConfig) -> tuple[list[RunArtifact], dict[str, str]]:
    root = config.root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"run artifact path does not exist: {root}")
    paths = [root] if root.is_file() else sorted(path for path in root.rglob("*") if path.is_file())
    base = root.parent if root.is_file() else root
    artifacts: list[RunArtifact] = []
    texts: dict[str, str] = {}
    for path in paths:
        try:
            rel = path.relative_to(base).as_posix()
        except ValueError:
            rel = path.name
        if _is_ignored_path(rel):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        is_text = _looks_text(path)
        text = ""
        if is_text and size <= config.max_file_kb * 1024:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                text = ""
            texts[rel] = text
        kind = _classify_artifact(rel, text)
        artifacts.append(RunArtifact(rel, size, path.suffix.lower(), kind, is_text, text[:2000]))
    return artifacts, texts


def _classify_artifact(path: str, text: str = "") -> str:
    name = Path(path).name.lower()
    suffix = Path(path).suffix.lower()
    lowered = text[:2000].lower()
    if suffix in {".diff", ".patch"}:
        return "diff"
    if suffix in {".log"} or any(marker in name for marker in ("transcript", "session", "terminal")):
        return "transcript"
    if suffix in {".md", ".txt"} and any(marker in name for marker in ("handoff", "run-report", "report")):
        return "handoff"
    if suffix in {".md", ".txt"} and _sections_from_text(text):
        return "handoff"
    if suffix in {".json", ".jsonl"} and _looks_context_health_report(name, lowered):
        return "context_health_report"
    if suffix == ".md" and _looks_context_health_report(name, lowered):
        return "context_health_report"
    if suffix == ".json" or suffix == ".jsonl":
        return "json"
    if suffix == ".md":
        return "markdown"
    return "text"


def _profile_run(artifacts: list[RunArtifact], texts: dict[str, str]) -> RunProfile:
    sections: set[str] = set()
    for path, text in texts.items():
        if _classify_artifact(path, text) == "handoff":
            sections.update(_sections_from_text(text))
    return RunProfile(
        artifact_count=len(artifacts),
        markdown_count=sum(1 for item in artifacts if item.suffix == ".md"),
        json_count=sum(1 for item in artifacts if item.suffix in {".json", ".jsonl"}),
        log_count=sum(1 for item in artifacts if item.suffix == ".log" or item.kind == "transcript"),
        diff_count=sum(1 for item in artifacts if item.kind == "diff"),
        has_handoff=any(item.kind == "handoff" for item in artifacts),
        has_transcript=any(item.kind == "transcript" for item in artifacts),
        has_diff=any(item.kind == "diff" for item in artifacts),
        has_context_health_report=any(item.kind == "context_health_report" for item in artifacts),
        detected_sections=tuple(sorted(sections)),
    )


def _cost_risk(texts: dict[str, str]) -> RunCostRisk:
    transcript_texts = {path: text for path, text in texts.items() if _classify_artifact(path, text) in {"transcript", "text"}}
    transcript_chars = sum(len(text) for text in transcript_texts.values())
    all_text = "\n".join(texts.values())
    diff = _combined_diff_stats(texts)
    suspicious = _suspicious_paths(diff.files, all_text)
    return RunCostRisk(
        estimated_tokens=max(1, sum(len(text) for text in texts.values()) // 4) if texts else 0,
        transcript_chars=transcript_chars,
        command_markers=sum(len(COMMAND_RE.findall(text)) for text in transcript_texts.values()),
        failed_command_markers=sum(len(FAILURE_RE.findall(text)) for text in transcript_texts.values()),
        diff_files_changed=len(diff.files),
        diff_added_lines=diff.added,
        diff_removed_lines=diff.removed,
        suspicious_paths=tuple(sorted(suspicious)),
    )


def _diff_stats(text: str) -> DiffStats:
    files: set[str] = set()
    added = 0
    removed = 0
    for line in text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                files.add(parts[3].removeprefix("b/"))
        elif line.startswith("+++") and line != "+++ /dev/null":
            files.add(line[4:].strip().removeprefix("b/"))
        elif line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return DiffStats(frozenset(files), added, removed)


def _handoff_rules(snapshot: RunSnapshot) -> list[RunFinding]:
    findings: list[RunFinding] = []
    handoff_path, handoff_text = _handoff_text(snapshot)
    if not snapshot.profile.has_handoff:
        findings.append(
            RunFinding(
                "handoff.missing_handoff",
                "No handoff summary found",
                "high",
                "handoff",
                "No markdown or text file is named like a handoff and no handoff-style headings were found",
                "Ask the agent for a handoff containing summary, changed files, verification, failures, and next steps",
            )
        )
        return findings
    if not _has_verification_evidence(handoff_text):
        findings.append(
            RunFinding(
                "handoff.missing_verification",
                "Handoff lacks verification evidence",
                "high",
                "handoff",
                f"{handoff_path} has no Verification heading, recognized test command, or checkbox result",
                "Ask for exact verification commands and results before merging",
                handoff_path,
            )
        )
    if _has_success_claim(handoff_text) and not _has_failure_disclosure(handoff_text):
        findings.append(
            RunFinding(
                "handoff.missing_failure_disclosure",
                "Handoff does not disclose failures or limits",
                "medium",
                "handoff",
                f"{handoff_path} contains success language but no failure, limitation, or not-run disclosure",
                "Require the agent to state what was not tested or did not work",
                handoff_path,
            )
        )
    if "files changed" not in snapshot.profile.detected_sections and not snapshot.profile.has_diff:
        findings.append(
            RunFinding(
                "handoff.missing_changed_files",
                "No changed-file evidence found",
                "medium",
                "handoff",
                f"{handoff_path} does not list a Files changed section and no diff artifact is present",
                "Ask for a file-level change summary or attach a diff",
                handoff_path,
            )
        )
    return findings


def _verification_rules(snapshot: RunSnapshot) -> list[RunFinding]:
    findings: list[RunFinding] = []
    joined = "\n".join(snapshot.texts.values())
    if not _has_verification_evidence(joined):
        findings.append(
            RunFinding(
                "verification.no_test_evidence",
                "No verification command evidence found",
                "high",
                "verification",
                "No artifact mentions recognized verification commands such as pytest, npm test, context-health, ruff, mypy, go test, or cargo test",
                "Run or request exact verification commands and results before trusting the handoff",
            )
        )
    if snapshot.cost_risk.failed_command_markers:
        path = _first_matching_path(snapshot.texts, FAILURE_RE)
        findings.append(
            RunFinding(
                "verification.failed_commands",
                "Transcript contains failed command markers",
                "high",
                "verification",
                f"{snapshot.cost_risk.failed_command_markers} likely failure marker(s) found; first match is in {path or 'run artifacts'}",
                "Inspect failed commands and require explicit resolution or risk acceptance",
                path,
            )
        )
    for path, data in _context_health_reports(snapshot.texts):
        score = data.get("score")
        verdict = str(data.get("verdict", ""))
        findings_data = data.get("findings", [])
        has_high = isinstance(findings_data, list) and any(isinstance(item, dict) and item.get("severity") in {"high", "critical"} for item in findings_data)
        if verdict == "context_blocked" or (isinstance(score, int) and score < 80) or has_high:
            findings.append(
                RunFinding(
                    "verification.context_health_blocked",
                    "Bundled Context Health report is blocked",
                    "high",
                    "verification",
                    f"{path} reports score {score} and verdict {verdict or 'unknown'}",
                    "Fix Context Health findings or explicitly accept the risk in the handoff",
                    path,
                )
            )
    return findings


def _diff_rules(snapshot: RunSnapshot) -> list[RunFinding]:
    findings: list[RunFinding] = []
    changed = snapshot.cost_risk.diff_files_changed
    if changed >= 15:
        severity = "high" if changed >= 40 else "medium"
        findings.append(
            RunFinding(
                "diff.too_many_files",
                "Diff touches many files",
                severity,
                "diff",
                f"Parsed diff artifacts touch {changed} changed files",
                "Split the work or request a focused review map",
            )
        )
    churn = snapshot.cost_risk.diff_added_lines + snapshot.cost_risk.diff_removed_lines
    if churn > 1000:
        findings.append(
            RunFinding(
                "diff.large_churn",
                "Diff has large line churn",
                "medium",
                "diff",
                f"Parsed diff artifacts include {snapshot.cost_risk.diff_added_lines} added and {snapshot.cost_risk.diff_removed_lines} removed lines",
                "Require a change-by-change review plan",
            )
        )
    if snapshot.cost_risk.suspicious_paths:
        evidence_paths = ", ".join(snapshot.cost_risk.suspicious_paths[:5])
        findings.append(
            RunFinding(
                "diff.sensitive_paths",
                "Sensitive path touched",
                "high",
                "diff",
                f"Diff or artifacts mention sensitive path(s): {evidence_paths}",
                "Review sensitive path changes manually and confirm no secrets or credentials were introduced",
            )
        )
    generated = _generated_paths(_combined_diff_stats(snapshot.texts).files)
    if generated:
        findings.append(
            RunFinding(
                "diff.generated_or_dependency_churn",
                "Generated or dependency files changed",
                "medium",
                "diff",
                f"Diff touches likely generated or dependency path(s): {', '.join(generated[:5])}",
                "Confirm generated files are intentional",
            )
        )
    return findings


def _cost_rules(snapshot: RunSnapshot) -> list[RunFinding]:
    findings: list[RunFinding] = []
    tokens = snapshot.cost_risk.estimated_tokens
    if tokens > 50000:
        findings.append(
            RunFinding(
                "cost.large_transcript",
                "Large transcript estimate",
                "medium" if tokens > 150000 else "low",
                "cost",
                f"Heuristic transcript/artifact estimate is {tokens} tokens",
                "Ask for a shorter reproduction path if review is difficult",
            )
        )
    if snapshot.cost_risk.command_markers >= 30:
        findings.append(
            RunFinding(
                "cost.many_command_markers",
                "Many command markers found",
                "low",
                "cost",
                f"Transcript artifacts contain {snapshot.cost_risk.command_markers} likely command/tool markers",
                "Ask for a shorter reproduction path if review is difficult",
            )
        )
    if snapshot.profile.artifact_count == 1 and snapshot.profile.has_transcript and not any(
        (snapshot.profile.has_handoff, snapshot.profile.has_diff, snapshot.profile.has_context_health_report)
    ):
        findings.append(
            RunFinding(
                "risk.no_artifact_diversity",
                "Run has only one transcript artifact",
                "low",
                "risk",
                "Only one transcript/log artifact was found and there is no handoff, diff, or Context Health report",
                "Ask the agent for a structured handoff and diff",
            )
        )
    return findings


def _summary(findings: list[RunFinding]) -> dict[str, dict[str, int]]:
    return {
        "by_severity": dict(Counter(finding.severity for finding in findings)),
        "by_category": dict(Counter(finding.category for finding in findings)),
    }


def _recommendations(findings: list[RunFinding]) -> tuple[str, ...]:
    seen: list[str] = []
    for finding in _dedupe_and_sort(findings):
        if finding.recommendation not in seen:
            seen.append(finding.recommendation)
        if len(seen) == 3:
            break
    return tuple(seen)


def _dedupe_and_sort(findings: list[RunFinding]) -> list[RunFinding]:
    deduped: list[RunFinding] = []
    seen: set[tuple[str, str | None, str]] = set()
    for finding in findings:
        key = (finding.id, finding.path, finding.evidence)
        if key not in seen:
            deduped.append(finding)
            seen.add(key)
    return sorted(deduped, key=lambda item: (SEVERITY_ORDER.get(item.severity, 9), item.id, item.path or ""))


def _is_ignored_path(rel: str) -> bool:
    return any(part in DEFAULT_IGNORES for part in Path(rel).parts)


def _looks_text(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES


def _sections_from_text(text: str) -> tuple[str, ...]:
    sections: list[str] = []
    for match in re.finditer(r"(?m)^\s{0,3}#{1,6}\s+(.+?)\s*$", text):
        section = re.sub(r"\s+", " ", match.group(1).strip().lower())
        sections.append(section)
    hinted = [section for section in sections if any(hint in section for hint in HANDOFF_SECTION_HINTS)]
    return tuple(dict.fromkeys(hinted))


def _looks_context_health_report(name: str, lowered_preview: str) -> bool:
    return (
        "context-health-report" in name
        or "context health" in lowered_preview
        or "context_blocked" in lowered_preview
        or "agent_ready" in lowered_preview
    )


def _combined_diff_stats(texts: dict[str, str]) -> DiffStats:
    files: set[str] = set()
    added = 0
    removed = 0
    for path, text in texts.items():
        if Path(path).suffix.lower() not in {".diff", ".patch"}:
            continue
        stats = _diff_stats(text)
        files.update(stats.files)
        added += stats.added
        removed += stats.removed
    return DiffStats(frozenset(files), added, removed)


def _suspicious_paths(diff_files: frozenset[str], all_text: str) -> set[str]:
    candidates = set(diff_files)
    for match in re.finditer(r"(?<![\w.-])(?:\.env(?:\.[\w.-]+)?|[\w./-]*(?:id_rsa|id_ed25519|credentials|secrets\.\w+|[\w.-]+\.(?:pem|key)))(?![\w.-])", all_text):
        candidates.add(match.group(0).replace("\\", "/"))
    return {path for path in candidates if _is_sensitive_path(path)}


def _is_sensitive_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.lstrip("/")
    name = Path(normalized).name
    if name in {".env.example", ".env.sample"}:
        return False
    if normalized == ".env" or name == ".env":
        return True
    if name.startswith(".env.") and name not in {".env.example", ".env.sample"}:
        return True
    return any(fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(name, pattern) for pattern in SENSITIVE_PATTERNS)


def _generated_paths(diff_files: frozenset[str]) -> list[str]:
    lock_ecosystems = sum(1 for path in diff_files if Path(path).name in LOCKFILES)
    generated = [
        path
        for path in sorted(diff_files)
        if any(fnmatch.fnmatch(path, pattern) for pattern in GENERATED_PATTERNS) or (lock_ecosystems > 1 and Path(path).name in LOCKFILES)
    ]
    return generated


def _handoff_text(snapshot: RunSnapshot) -> tuple[str | None, str]:
    for path, text in snapshot.texts.items():
        if _classify_artifact(path, text) == "handoff":
            return path, text
    return None, ""


def _has_verification_evidence(text: str) -> bool:
    lowered = text.lower()
    return bool(
        re.search(r"(?m)^#{1,6}\s+.*verification", lowered)
        or any(term in lowered for term in VERIFICATION_TERMS)
        or re.search(r"(?m)^\s*[-*]\s+\[[ xX]\]", text)
    )


def _has_failure_disclosure(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in ("what didn't work", "what did not work", "known issues", "limitations", "could not", "not run"))


def _has_success_claim(text: str) -> bool:
    return bool(re.search(r"\b(success|successful|passed|complete|completed|done|implemented|built)\b", text, re.IGNORECASE))


def _first_matching_path(texts: dict[str, str], pattern: re.Pattern[str]) -> str | None:
    for path, text in texts.items():
        if pattern.search(text):
            return path
    return None


def _context_health_reports(texts: dict[str, str]) -> list[tuple[str, dict[str, Any]]]:
    reports: list[tuple[str, dict[str, Any]]] = []
    for path, text in texts.items():
        if Path(path).suffix.lower() != ".json":
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "score" in data and "verdict" in data:
            reports.append((path, data))
    return reports
