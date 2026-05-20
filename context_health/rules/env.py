from __future__ import annotations

import re

from context_health.models import Finding, RepoSnapshot
from context_health.rules import finding


PATTERNS = (
    re.compile(r"process\.env\.([A-Z0-9_]+)"),
    re.compile(r"import\.meta\.env\.([A-Z0-9_]+)"),
    re.compile(r"os\.environ\[['\"]([A-Z0-9_]+)['\"]\]"),
    re.compile(r"os\.getenv\(['\"]([A-Z0-9_]+)['\"]\)"),
    re.compile(r"getenv\(['\"]([A-Z0-9_]+)['\"]\)"),
)
IGNORED_PREFIXES = ("NODE_", "PYTHON", "npm_")


def run(snapshot: RepoSnapshot) -> list[Finding]:
    findings: list[Finding] = []
    keys = _env_keys(snapshot)
    if snapshot.has_file(".env"):
        findings.append(finding(
            id="env.secret_file_present",
            title="Environment secret file is present",
            severity="high",
            category="env",
            path=".env",
            evidence=".env exists in the repository scan",
            recommendation="Remove .env from the repo and keep only .env.example with fake values",
        ))
    if keys and not snapshot.profile.has_env_example:
        findings.append(finding(
            id="env.missing_example",
            title="Environment example file is missing",
            severity="high",
            category="env",
            evidence=f"Code references env vars ({', '.join(sorted(keys))}) but no .env.example or .env.sample exists",
            recommendation="Add .env.example with required key names and fake values",
        ))
        return findings
    example_path, example = snapshot.find_text(".env.example", ".env.sample")
    if keys and example_path:
        documented = {line.split("=", 1)[0].strip() for line in example.splitlines() if "=" in line}
        missing = sorted(keys - documented)
        if missing:
            findings.append(finding(
                id="env.example_missing_required_keys",
                title="Environment example omits inferred keys",
                severity="medium",
                category="env",
                path=example_path,
                evidence=f"{example_path} is missing inferred keys: {', '.join(missing)}",
                recommendation="Add fake placeholder values for every required environment key",
            ))
    return findings


def _env_keys(snapshot: RepoSnapshot) -> set[str]:
    keys: set[str] = set()
    for path, text in snapshot.texts.items():
        if "/fixtures/" in f"/{path}":
            continue
        if path.startswith(".") and not path.startswith((".github/", ".agents/", ".claude/", ".codex/")):
            continue
        for pattern in PATTERNS:
            for match in pattern.findall(text):
                if not match.startswith(IGNORED_PREFIXES):
                    keys.add(match)
    return keys
