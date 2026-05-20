from __future__ import annotations

from context_health.models import Finding, RepoSnapshot
from context_health.rules import finding


LOCKFILES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "uv.lock"}


def run(snapshot: RepoSnapshot) -> list[Finding]:
    findings: list[Finding] = []
    threshold = snapshot.config.max_file_kb * 1024
    considered = [file for file in snapshot.files if "/fixtures/" not in f"/{file.path}"]
    for file in considered:
        if file.path in LOCKFILES:
            continue
        if file.is_text and file.size_bytes > threshold:
            findings.append(finding(
                id="context.large_file",
                title="Large text file may waste context",
                severity="medium",
                category="context",
                path=file.path,
                evidence=f"{file.path} is {file.size_bytes // 1024} KB, above the {snapshot.config.max_file_kb} KB threshold",
                recommendation="Ignore, split, or document why this large file is needed for agent context",
            ))
            break
    generated = next((f.path for f in considered if _generated_artifact(f.path)), None)
    if generated:
        findings.append(finding(
            id="context.generated_artifact_in_repo",
            title="Generated artifact appears in scanned paths",
            severity="low",
            category="context",
            path=generated,
            evidence=f"{generated} looks like generated output and was not excluded from the scan",
            recommendation="Add generated output to ignore rules or keep only source files in agent context",
        ))
    if len(snapshot.files) > 5000:
        findings.append(finding(
            id="context.too_many_unignored_files",
            title="Too many files remain after default ignores",
            severity="high",
            category="context",
            evidence=f"{len(snapshot.files)} files were scanned after default ignores",
            recommendation="Add ignores or remove generated files so agents see a smaller context",
        ))
    return findings


def _generated_artifact(path: str) -> bool:
    lower = path.lower()
    return lower.endswith(".min.js") or lower.endswith(".bundle.js") or lower.endswith("coverage/index.html")
