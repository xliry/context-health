from __future__ import annotations

from context_health.models import Finding, RepoSnapshot
from context_health.rules import finding


ROOT_FILES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md"}
SETUP_HINTS = ("install", "pip install", "npm install", "pnpm install", "yarn install", "uv sync")
RUN_HINTS = ("run", "dev", "start", "serve", "python -m", "npm run", "pnpm dev", "yarn dev")
TEST_HINTS = ("test", "verify", "pytest", "vitest", "jest", "npm test", "pnpm test", "yarn test", "uv run pytest")


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
    if combined:
        instruction_path = instruction_paths[0] if instruction_paths else readme_path
        lower = combined.lower()
        if _has_project_metadata(snapshot) and not _has_hint(lower, SETUP_HINTS):
            findings.append(finding(
                id="agent.instructions_missing_setup",
                title="Agent instructions omit setup commands",
                severity="low",
                category="agent",
                path=instruction_path,
                evidence="Project metadata was found, but agent instructions do not mention setup or install commands",
                recommendation="Add exact install/setup commands to AGENTS.md or the root agent instruction file",
            ))
        runnable_signal = _runnable_signal(snapshot)
        if runnable_signal and not _has_hint(lower, RUN_HINTS):
            findings.append(finding(
                id="agent.instructions_missing_run",
                title="Agent instructions omit run commands",
                severity="low",
                category="agent",
                path=instruction_path,
                evidence=f"{runnable_signal} was found, but agent instructions do not mention run/dev commands",
                recommendation="Add exact run/dev commands to AGENTS.md or the root agent instruction file",
            ))
        test_signal = _test_signal(snapshot)
        if test_signal and not _has_hint(lower, TEST_HINTS):
            findings.append(finding(
                id="agent.instructions_missing_tests",
                title="Agent instructions omit test commands",
                severity="low",
                category="agent",
                path=instruction_path,
                evidence=f"{test_signal} was found, but agent instructions do not mention test or verification commands",
                recommendation="Add exact test/verification commands to AGENTS.md or the root agent instruction file",
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


def _has_hint(text: str, hints: tuple[str, ...]) -> bool:
    return any(hint in text for hint in hints)


def _has_project_metadata(snapshot: RepoSnapshot) -> bool:
    return any(snapshot.has_file(path) for path in ("package.json", "pyproject.toml", "requirements.txt"))


def _runnable_signal(snapshot: RepoSnapshot) -> str | None:
    for name in ("dev", "start", "serve"):
        if name in snapshot.profile.scripts:
            return f"package script `{name}`"
    if "python" in snapshot.profile.ecosystems:
        return "Python project metadata"
    return None


def _test_signal(snapshot: RepoSnapshot) -> str | None:
    for name in snapshot.profile.scripts:
        if name == "test" or name.startswith("test:"):
            return f"package script `{name}`"
    haystack = "\n".join(snapshot.texts.get(path, "") for path in ("pyproject.toml", "requirements.txt"))
    for word in ("pytest", "unittest", "tox", "nox"):
        if word in haystack.lower():
            return f"Python test tool `{word}`"
    return None
