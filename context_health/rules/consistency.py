from __future__ import annotations

import re

from context_health.models import Finding, RepoSnapshot
from context_health.rules import finding


LOCKS = {"pnpm-lock.yaml": "pnpm", "package-lock.json": "npm", "yarn.lock": "yarn"}


def run(snapshot: RepoSnapshot) -> list[Finding]:
    findings: list[Finding] = []
    present = {path: manager for path, manager in LOCKS.items() if snapshot.has_file(path)}
    if len(set(present.values())) > 1:
        findings.append(finding(
            id="consistency.conflicting_package_manager",
            title="Multiple package manager lockfiles are present",
            severity="medium",
            category="consistency",
            evidence=f"Found lockfiles for multiple managers: {', '.join(sorted(present))}",
            recommendation="Pick one package manager and remove stale lockfiles",
        ))
    readme_path, readme = snapshot.find_text("README.md", "readme.md", "README")
    if readme and snapshot.profile.package_manager:
        mismatch = _readme_mismatch(readme, snapshot.profile.package_manager)
        if mismatch:
            findings.append(finding(
                id="consistency.docs_script_mismatch",
                title="README package manager command may mismatch lockfile",
                severity="low",
                category="consistency",
                path=readme_path,
                evidence=f"README mentions {mismatch}, but detected package manager is {snapshot.profile.package_manager}",
                recommendation="Align README install/run/test commands with the detected package manager",
            ))
    agent_texts = {path: snapshot.texts[path] for path in ("AGENTS.md", "CLAUDE.md") if path in snapshot.texts}
    if len(agent_texts) == 2:
        commands = {path: _command_hint(text) for path, text in agent_texts.items()}
        if commands["AGENTS.md"] and commands["CLAUDE.md"] and commands["AGENTS.md"] != commands["CLAUDE.md"]:
            findings.append(finding(
                id="consistency.multiple_agent_instructions_possible_conflict",
                title="Agent instruction files imply different verification commands",
                severity="medium",
                category="consistency",
                evidence=f"AGENTS.md mentions {commands['AGENTS.md']}, while CLAUDE.md mentions {commands['CLAUDE.md']}",
                recommendation="Consolidate verification commands into one source of truth",
            ))
    return findings


def _readme_mismatch(readme: str, manager: str) -> str | None:
    for other in {"npm", "pnpm", "yarn"} - {manager}:
        if re.search(rf"\b{other}\b", readme):
            return other
    return None


def _command_hint(text: str) -> str | None:
    lower = text.lower()
    for hint in ("pnpm test", "npm test", "yarn test", "pytest", "uv run pytest"):
        if hint in lower:
            return hint
    return None
