from __future__ import annotations

from context_health.models import Finding, RepoSnapshot
from context_health.rules import find_line, finding


RUN_HINTS = ("npm run", "pnpm dev", "yarn dev", "python -m", "uv run")
TEST_HINTS = ("test", "pytest", "vitest", "jest", "npm test", "pnpm test", "yarn test")


def run(snapshot: RepoSnapshot) -> list[Finding]:
    findings: list[Finding] = []
    readme_path, readme = snapshot.find_text("README.md", "readme.md", "README")
    scripts = snapshot.profile.scripts
    if not readme_path:
        findings.append(finding(
            id="docs.missing_readme",
            title="README is missing",
            severity="high",
            category="docs",
            evidence="No root README.md, readme.md, or README file was found",
            recommendation="Add README with purpose, install, run, and test commands",
        ))
        return findings
    lower = readme.lower()
    runnable = any(name in scripts for name in ("dev", "start", "serve")) or "python" in snapshot.profile.ecosystems
    if runnable and not any(hint in lower for hint in RUN_HINTS):
        findings.append(finding(
            id="docs.readme_missing_run_command",
            title="Run command is not documented",
            severity="medium",
            category="docs",
            path=readme_path,
            evidence="Repository has runnable scripts or Python metadata, but README has no recognizable run command",
            recommendation="Add the exact run command to README.md or AGENTS.md",
        ))
    has_test_script = any(name == "test" or name.startswith("test:") for name in scripts)
    if has_test_script and not any(hint in lower for hint in TEST_HINTS):
        findings.append(finding(
            id="docs.readme_missing_test_command",
            title="Test command exists but is not documented",
            severity="medium",
            category="docs",
            path=readme_path,
            evidence='package.json contains a test script but README does not document a test command',
            recommendation="Add the exact test command to README.md or AGENTS.md",
        ))
    if len(scripts) > 1 and snapshot.profile.package_manager and snapshot.profile.package_manager not in lower:
        findings.append(finding(
            id="docs.package_scripts_not_documented",
            title="Package scripts are not documented",
            severity="low",
            category="docs",
            path=readme_path,
            line=find_line(readme, "#"),
            evidence=f"package.json defines {len(scripts)} scripts, but README does not mention {snapshot.profile.package_manager}",
            recommendation="Document the main package scripts and package manager in README.md",
        ))
    return findings
