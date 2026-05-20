from __future__ import annotations

from context_health.models import Finding, RepoSnapshot
from context_health.rules import finding


ROOT_FILES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md"}
VERIFY_HINTS = ("test", "verify", "pytest", "npm", "pnpm", "run", "uv")


def run(snapshot: RepoSnapshot) -> list[Finding]:
    findings: list[Finding] = []
    instruction_paths = _instruction_paths(snapshot)
    readme_path, readme = snapshot.find_text("README.md", "readme.md", "README")
    readme_has_agent = any(word in readme.lower() for word in ("agent", "codex", "claude", "ai assistant"))
    if not instruction_paths and not readme_has_agent:
        findings.append(finding(
            id="agent.missing_instructions",
            title="Agent instructions are missing",
            severity="medium",
            category="agent",
            evidence="No AGENTS.md, CLAUDE.md, GEMINI.md, tool instruction folder, or README agent section was found",
            recommendation="Add AGENTS.md or a README agent section with run and verification commands",
        ))
        return findings
    root_pointer = any(path in ROOT_FILES for path in instruction_paths) or readme_has_agent
    tool_specific = [path for path in instruction_paths if path.startswith((".agents/", ".claude/", ".codex/"))]
    if tool_specific and not root_pointer:
        findings.append(finding(
            id="agent.instructions_hidden",
            title="Agent instructions are hidden in tool-specific folders",
            severity="low",
            category="agent",
            path=tool_specific[0],
            evidence=f"Only tool-specific instructions were found: {', '.join(tool_specific[:3])}",
            recommendation="Add a root AGENTS.md or README pointer to the tool-specific instructions",
        ))
    if len(instruction_paths) > 5:
        findings.append(finding(
            id="agent.instructions_too_fragmented",
            title="Agent instructions are fragmented",
            severity="low",
            category="agent",
            evidence=f"{len(instruction_paths)} agent instruction files were found",
            recommendation="Consolidate agent instructions or link a clear hierarchy from AGENTS.md",
        ))
    combined = "\n".join(snapshot.texts.get(path, "") for path in instruction_paths)
    if readme_has_agent:
        combined += "\n" + readme
    if combined and not any(hint in combined.lower() for hint in VERIFY_HINTS):
        findings.append(finding(
            id="agent.instructions_no_verification",
            title="Agent instructions omit verification commands",
            severity="low",
            category="agent",
            path=instruction_paths[0] if instruction_paths else readme_path,
            evidence="Agent instruction text does not mention test, verify, run, npm, pnpm, pytest, or uv",
            recommendation="Add test/build verification commands to the agent instructions",
        ))
    return findings


def _instruction_paths(snapshot: RepoSnapshot) -> list[str]:
    paths = []
    for path in snapshot.texts:
        if path in ROOT_FILES:
            paths.append(path)
        elif path.startswith((".agents/", ".claude/", ".codex/")):
            paths.append(path)
    return sorted(paths)
