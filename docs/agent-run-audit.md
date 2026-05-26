# Agent Run Audit

Use `context-health run-audit` after a coding-agent run finishes. It reviews local run artifacts for handoff quality, verification evidence, diff risk, and heuristic cost/risk signals.

```bash
context-health run-audit runs/codex-2026-05-26
context-health run-audit runs/codex-2026-05-26 --markdown run-audit.md
context-health run-audit runs/codex-2026-05-26 --json > run-audit.json
context-health run-audit runs/codex-2026-05-26 --fail-under 80
```

## Artifact Folder

A useful run folder can contain any mix of:

```text
runs/codex-2026-05-26/
  handoff.md
  transcript.log
  changes.diff
  context-health-report.json
```

The command reads text-like local artifacts: Markdown, text, logs, JSON/JSONL, diffs, patches, YAML, and TOML. It ignores dependency, build, cache, virtualenv, and git metadata directories.

## Output

Terminal output is concise:

```text
Context Health Run Audit: 84/100 - handoff_ready

Run profile:
  artifacts: 4
  handoff: yes
  diff: yes
  context health report: yes

Cost/risk estimate (heuristic):
  estimated tokens: 12400
  changed files: 4
  failed command markers: 0
```

JSON output contains `score`, `verdict`, `summary`, `run_profile`, `cost_risk`, `recommendations`, and evidence-backed `findings`.

Markdown output writes a readable report to the path passed with `--markdown`.

## Score Meaning

- `handoff_ready`: score is 80 or higher.
- `review_needed`: score is 50-79.
- `handoff_blocked`: score is below 50.

Findings use the same simple severity weights as the repo scan: critical 25, high 15, medium 8, low 3.

## Privacy And Safety

Run audit is local and deterministic. It does not call an LLM, remote API, telemetry service, or billing system. It does not execute commands from transcripts or apply patches. The only write is the optional Markdown report path.

## Limitations

- Token counts are rough text-length estimates, not provider billing data.
- Sensitive-path checks are review-risk heuristics, not a security scanner.
- No finding is proof that a run is safe or correct.
- This does not replace tests, code review, or human judgment.
- Transcript support is intentionally broad and text-based in this version.
