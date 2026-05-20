# Context Health

![Context Health explainer](docs/assets/explainer.png)

`context-health` checks whether a repo gives coding agents enough context to work safely: run commands, test commands, env examples, agent instructions, and context bloat.

It does not judge code quality or guarantee agent success. It catches common context friction before you hand a repo to an agent.

## Install

From a local checkout:

```bash
python -m pip install -e ".[dev]"
```

## Scan A Repo

```bash
context-health .
```

Example terminal output:

```text
Context Health: 74/100 - needs_context_work

Top findings:
  [medium] docs.readme_missing_test_command
    package.json contains a test script but README does not document a test command
    fix: Add the exact test command to README.md or AGENTS.md
```

## JSON Output

```bash
context-health . --json
```

The JSON report includes `score`, `verdict`, `summary`, `repo_profile`, `recommendations`, and evidence-backed `findings`.

```json
{
  "score": 62,
  "verdict": "needs_context_work",
  "findings": [
    {
      "id": "env.missing_example",
      "title": "Environment example file is missing",
      "severity": "high",
      "category": "env",
      "path": null,
      "line": null,
      "evidence": "Code references env vars (API_KEY) but no .env.example or .env.sample exists",
      "recommendation": "Add .env.example with required key names and fake values"
    }
  ]
}
```

## Markdown Report

```bash
context-health . --markdown context-health-report.md
```

JSON stays valid when Markdown is also requested:

```bash
context-health . --json --markdown context-health-report.md
```

## CI Gate

Use `--fail-under` to turn a low score into exit code `1`:

```bash
context-health . --fail-under 80
```

Invalid paths and usage errors exit `2`.

## Options

```text
context-health [path] [--json] [--markdown PATH] [--fail-under SCORE]
               [--include GLOB] [--exclude GLOB] [--max-file-kb KB]
               [--verbose]
```

Default ignores include `.git`, `node_modules`, `.next`, `dist`, `build`, `coverage`, virtualenv folders, caches, and similar generated dependency paths.

## What v0.1 Checks

- README presence and run/test command documentation
- `.env.example` or `.env.sample` when code references env vars
- obvious `.env` files committed to the repo
- root or discoverable agent instructions
- conflicting package manager signals
- possible conflicts between agent instruction files
- large text files and generated artifacts that remain in scanned paths
- test command and CI evidence

## What v0.1 Does Not Do

- Web UI
- SaaS backend
- GitHub App
- Auto-fix mode
- LLM review
- MCP server
- dependency vulnerability scanning
- security review
- telemetry

## Development

```bash
python -m pip install -e ".[dev]"
context-health --help
pytest -q
```
