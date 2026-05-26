# What I built

- Added a deterministic run-audit command.
- Kept the existing repository scan command behavior intact.

# Files changed

- context_health/run_models.py
- context_health/run_audit.py
- context_health/run_report.py

# Verification results

- [x] `pytest -q` passed.
- [x] `context-health . --fail-under 95` passed.

# What did not work

- No failures remained. Not run: packaging smoke in this small fixture.

# Next steps

- Review the CLI output wording.

# Sample output

```text
Context Health Run Audit: 100/100 - handoff_ready
```
