# Release Checklist

For a local release-candidate check:

- Install dev dependencies: `python -m pip install -e ".[dev]"`
- Run tests: `pytest -q`
- Run package smoke: `python scripts/package_smoke.py`
- Run dogfood scan: `context-health . --fail-under 95`
- Inspect git status: `git status --short --ignored`
- Tag and publish steps are manual and out of scope for this checklist.
