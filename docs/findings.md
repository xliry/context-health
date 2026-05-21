# Finding Catalog

This catalog lists the current deterministic finding IDs emitted by Context Health.

## Agent

### `agent.missing_instructions`

- Category: `agent`
- Severity: `medium`
- Fires when: no root agent instruction file, tool-specific instruction folder, or README agent section is found.
- Recommended fix: add `AGENTS.md` or a README agent section with run and verification commands.

### `agent.instructions_hidden`

- Category: `agent`
- Severity: `low`
- Fires when: instructions exist only in tool-specific folders such as `.agents/`, `.claude/`, or `.codex/`.
- Recommended fix: add a root `AGENTS.md` or README pointer to the tool-specific instructions.

### `agent.instructions_too_fragmented`

- Category: `agent`
- Severity: `low`
- Fires when: more than five agent instruction files are found.
- Recommended fix: consolidate instructions or link a clear hierarchy from `AGENTS.md`.

### `agent.instructions_missing_setup`

- Category: `agent`
- Severity: `low`
- Fires when: agent instructions exist, project metadata exists, and no setup/install hint is present.
- Recommended fix: add exact install/setup commands to `AGENTS.md` or the root agent instruction file.

### `agent.instructions_missing_run`

- Category: `agent`
- Severity: `low`
- Fires when: agent instructions exist, the repo appears runnable, and no run/dev hint is present.
- Recommended fix: add exact run/dev commands to `AGENTS.md` or the root agent instruction file.

### `agent.instructions_missing_tests`

- Category: `agent`
- Severity: `low`
- Fires when: agent instructions exist, test evidence exists, and no test/verification hint is present.
- Recommended fix: add exact test/verification commands to `AGENTS.md` or the root agent instruction file.

## Context

### `context.large_file`

- Category: `context`
- Severity: `medium`
- Fires when: a scanned text file exceeds the configured large-file threshold.
- Recommended fix: ignore, split, or document why the large file is needed for agent context.

### `context.generated_artifact_in_repo`

- Category: `context`
- Severity: `low`
- Fires when: generated output such as a bundle, minified file, or coverage HTML remains in scanned paths.
- Recommended fix: add generated output to ignore rules or keep only source files in agent context.

### `context.too_many_unignored_files`

- Category: `context`
- Severity: `high`
- Fires when: more than 5000 files remain after default ignores.
- Recommended fix: add ignores or remove generated files so agents see a smaller context.

## Consistency

### `consistency.conflicting_package_manager`

- Category: `consistency`
- Severity: `medium`
- Fires when: lockfiles for multiple Node package managers are present.
- Recommended fix: pick one package manager and remove stale lockfiles.

### `consistency.docs_script_mismatch`

- Category: `consistency`
- Severity: `low`
- Fires when: README mentions a different package manager than the detected lockfile/package manager.
- Recommended fix: align README install/run/test commands with the detected package manager.

### `consistency.agent_readme_command_mismatch`

- Category: `consistency`
- Severity: `low`
- Fires when: root README and root `AGENTS.md` mention different recognizable verification commands.
- Recommended fix: align README and `AGENTS.md` on the exact commands agents should use.

### `consistency.multiple_agent_instructions_possible_conflict`

- Category: `consistency`
- Severity: `medium`
- Fires when: root `AGENTS.md` and `CLAUDE.md` imply different verification commands.
- Recommended fix: consolidate verification commands into one source of truth.

## Docs

### `docs.missing_readme`

- Category: `docs`
- Severity: `high`
- Fires when: no root README file is found.
- Recommended fix: add README with purpose, install, run, and test commands.

### `docs.readme_missing_run_command`

- Category: `docs`
- Severity: `medium`
- Fires when: the repo appears runnable but README has no recognizable run command.
- Recommended fix: add the exact run command to `README.md` or `AGENTS.md`.

### `docs.readme_missing_test_command`

- Category: `docs`
- Severity: `medium`
- Fires when: `package.json` contains a test script but README does not document a test command.
- Recommended fix: add the exact test command to `README.md` or `AGENTS.md`.

### `docs.package_scripts_not_documented`

- Category: `docs`
- Severity: `low`
- Fires when: multiple package scripts exist but README does not mention the detected package manager.
- Recommended fix: document the main package scripts and package manager in README.

## Env

### `env.secret_file_present`

- Category: `env`
- Severity: `high`
- Fires when: a `.env` file is present in the repository scan.
- Recommended fix: remove `.env` from the repo and keep only `.env.example` with fake values.

### `env.missing_example`

- Category: `env`
- Severity: `high`
- Fires when: code references environment variables but no `.env.example` or `.env.sample` exists.
- Recommended fix: add `.env.example` with required key names and fake values.

### `env.example_missing_required_keys`

- Category: `env`
- Severity: `medium`
- Fires when: an env example exists but omits inferred environment keys used by code.
- Recommended fix: add fake placeholder values for every required environment key.

## Tests

### `tests.no_test_command`

- Category: `tests`
- Severity: `medium`
- Fires when: no package test script or Python test tool evidence is detected.
- Recommended fix: add a test command or document why the repo has no automated tests.

### `tests.test_command_not_documented`

- Category: `tests`
- Severity: `medium`
- Fires when: a test command exists but README does not document it.
- Recommended fix: document the exact test command in README or `AGENTS.md`.

### `tests.no_ci_evidence`

- Category: `tests`
- Severity: `low`
- Fires when: no `.github/workflows` files are found.
- Recommended fix: add CI or document local verification commands.
