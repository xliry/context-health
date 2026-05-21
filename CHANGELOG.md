# Changelog

All notable changes to Context Health will be documented in this file.

## Unreleased

- No changes yet.

## 0.2.0 - 2026-05-21

- Added detected monorepo workspace patterns to `repo_profile.workspaces`.
- Added deterministic agent instruction quality checks for setup, run, and test guidance.
- Added simple README/AGENTS command mismatch detection.
- Added lightweight output snapshot tests for terminal, JSON, and Markdown reports.
- Added package build smoke verification for wheel and sdist release artifacts.
- Hardened sdist manifest to include full test assets and exclude generated artifacts.
- Added finding catalog documentation and sync coverage.
- Added an agent handoff recipe for using Context Health before coding-agent work.
- Added optional `.context-health.toml` scan defaults.

## 0.1.0 - 2026-05-21

- Initial Python CLI for checking repository agent-context readiness.
- Added scoring, terminal, JSON, Markdown, and CI gate output.
- Added checks for README run/test guidance, env examples, agent instructions, package manager consistency, generated bloat, and CI/test evidence.
