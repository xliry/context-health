# Known Limitations

Context Health v0.2 is a context-readiness scanner. It checks whether a repo gives agents practical setup, run, test, environment, and instruction context. It is not a security scanner, dependency auditor, semantic reviewer, or guarantee that an agent will make the right change.

Env var inference is heuristic. Context Health skips common generated, vendored, dependency, cache, fixture, and virtualenv-like paths before inferring required keys, but large mixed repositories can still be noisy when unusual generated or third-party folders remain in the scan. Treat long inferred env-key lists as a signal to narrow scan context before treating every key as a required app setting.

Default ignores cover common folders and virtualenv-like names such as `.venv`, `venv`, `env`, `*-env`, and `*_env`, but they do not catch every custom local environment or generated folder. Repo-specific paths may still need explicit `.context-health.toml` excludes.

Local tool settings are not the same as root handoff instructions. Prefer a root `AGENTS.md` or a clear README section for agent-facing setup, run, test, and verification guidance.

For large repos, start by excluding generated, vendored, and virtualenv-like paths while keeping first-party source, tests, docs, and handoff files visible.
