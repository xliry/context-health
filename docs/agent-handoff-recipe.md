# Agent Handoff Recipe

Use Context Health before you hand a repository to Codex, Claude, Cursor, or another coding agent. It helps expose missing setup, run, test, environment, and instruction context before agent work starts.

Context Health does not guarantee agent success. It does not replace tests, code review, or security scanning.

## When To Run It

Run Context Health when:

- you are about to ask an agent to modify a repo
- you are preparing a handoff issue, task brief, or pull request
- you want to know whether the repo explains how to install, run, test, and verify changes
- you want a compact report to attach to an agent prompt

## Local Workflow

From the repository you want to hand off:

```bash
context-health .
context-health . --markdown context-health-report.md
context-health . --json > context-health-report.json
context-health . --fail-under 80
```

Use the Markdown report for human-readable handoff notes. Use the JSON report when you want structured data for an agent, orchestration script, or system prompt.

On Windows PowerShell 5.1, bare `>` redirection can write UTF-16 files. Prefer `cmd /c "context-health . --json > context-health-report.json"` or write stdout as UTF-8 before passing JSON to other tools.

## CI Gate

Use `--fail-under` when the repo should meet a minimum context readiness bar before agent work begins:

```bash
context-health . --fail-under 80
```

A score below the threshold exits with code `1`. Usage and path errors exit with code `2`.

## Decide What To Fix

Fix findings first when:

- the score is below your handoff threshold
- findings mention missing README, setup, run, test, or env example context
- the agent would need to guess package manager or verification commands

Proceed with the handoff when:

- the score meets your threshold
- remaining findings are low severity and already understood
- your prompt includes any missing context the agent still needs

## Attach Or Paste The Report

Attach `context-health-report.md` to the issue, pull request, or agent task. If you cannot attach files, paste the score, verdict, top findings, and recommended fixes into the prompt.

For automation-heavy agent workflows, include `context-health-report.json` so the agent or wrapper can read `score`, `verdict`, `repo_profile`, and `findings`.

## Example Handoff Prompt

```text
Please implement the requested change in this repo.

I ran Context Health before handoff:
- Score: 100/100
- Verdict: agent_ready
- Report: see attached context-health-report.md

Use the repo instructions for install, run, and test commands. Before finishing, run the documented verification command and summarize what passed.
```
