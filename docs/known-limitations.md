# Known Limitations

Context Health v0.2 is a context-readiness scanner. It checks whether a repo gives agents practical setup, run, test, environment, and instruction context. It is not a security scanner, dependency auditor, semantic reviewer, or guarantee that an agent will make the right change.

Env var inference is heuristic. In large mixed repositories it can be noisy when generated code, vendored dependencies, ComfyUI-style folders, or virtualenv-like folders are included in the scan. Treat long inferred env-key lists as a signal to narrow scan context before treating every key as a required app setting.

Default ignores cover common folders, but they do not catch every custom local environment folder. A repo-specific folder such as `dough-env` may need an explicit `.context-health.toml` exclude.

Local tool settings are not the same as root handoff instructions. Prefer a root `AGENTS.md` or a clear README section for agent-facing setup, run, test, and verification guidance.

For large repos, start by excluding generated, vendored, and virtualenv-like paths while keeping first-party source, tests, docs, and handoff files visible.
