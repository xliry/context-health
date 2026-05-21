# Context Health Report

- Score: `59/100`
- Verdict: `needs_context_work`
- Ecosystems: `node, vite`
- Package manager: `unknown`
- Workspaces: `none`

## Findings

### [high] docs.missing_readme

- Title: README is missing
- Category: `docs`
- Path: `repo`
- Line: `n/a`
- Evidence: No root README.md, readme.md, or README file was found
- Recommendation: Add README with purpose, install, run, and test commands

### [high] env.missing_example

- Title: Environment example file is missing
- Category: `env`
- Path: `repo`
- Line: `n/a`
- Evidence: Code references env vars (API_KEY) but no .env.example or .env.sample exists
- Recommendation: Add .env.example with required key names and fake values

### [medium] agent.missing_instructions

- Title: Agent instructions are missing
- Category: `agent`
- Path: `repo`
- Line: `n/a`
- Evidence: No AGENTS.md, CLAUDE.md, GEMINI.md, tool instruction folder, or README agent section was found
- Recommendation: Add AGENTS.md or a README agent section with run and verification commands

### [low] tests.no_ci_evidence

- Title: No CI evidence found
- Category: `tests`
- Path: `repo`
- Line: `n/a`
- Evidence: No .github/workflows files were found
- Recommendation: Add CI or document local verification commands

## Next Actions

1. Add README with purpose, install, run, and test commands
2. Add .env.example with required key names and fake values
3. Add AGENTS.md or a README agent section with run and verification commands
