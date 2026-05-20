from __future__ import annotations

from context_health.models import Finding, RepoSnapshot
from context_health.rules import finding


DOC_TEST_HINTS = ("test", "pytest", "vitest", "jest", "npm test", "pnpm test", "yarn test")


def run(snapshot: RepoSnapshot) -> list[Finding]:
    findings: list[Finding] = []
    has_tests = _has_test_command(snapshot)
    readme_path, readme = snapshot.find_text("README.md", "readme.md", "README")
    docs_tests = bool(readme and any(hint in readme.lower() for hint in DOC_TEST_HINTS))
    if not has_tests:
        findings.append(finding(
            id="tests.no_test_command",
            title="No test command evidence found",
            severity="medium",
            category="tests",
            evidence="No package test script, pytest/unittest/tox/nox metadata, or test dependency was detected",
            recommendation="Add a test command or document why this repo has no automated tests",
        ))
    elif readme and not docs_tests:
        findings.append(finding(
            id="tests.test_command_not_documented",
            title="Test command is not documented",
            severity="medium",
            category="tests",
            path=readme_path,
            evidence="A test command exists, but README does not document it",
            recommendation="Document the exact test command in README.md or AGENTS.md",
        ))
    if not snapshot.profile.has_ci:
        findings.append(finding(
            id="tests.no_ci_evidence",
            title="No CI evidence found",
            severity="low",
            category="tests",
            evidence="No .github/workflows files were found",
            recommendation="Add CI or document local verification commands",
        ))
    return findings


def _has_test_command(snapshot: RepoSnapshot) -> bool:
    scripts = snapshot.profile.scripts
    if any(name == "test" or name.startswith("test:") for name in scripts):
        return True
    haystack = "\n".join(snapshot.texts.get(path, "") for path in ("pyproject.toml", "requirements.txt"))
    return any(word in haystack.lower() for word in ("pytest", "unittest", "tox", "nox"))
