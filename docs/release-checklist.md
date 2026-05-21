# Release Checklist

For a local release-candidate check:

- Install dev dependencies: `python -m pip install -e ".[dev]"`
- Run tests: `pytest -q`
- Run package smoke: `python scripts/package_smoke.py`
- Run dogfood scan: `context-health . --fail-under 95`
- Review the current dogfood pack and record any release-blocking findings.
- Confirm known limitations are documented for v0.2 users.
- Inspect git status: `git status --short --ignored`
- Confirm no tag or publish happens before manual approval.
- Tag and publish steps are manual and out of scope for this checklist.
