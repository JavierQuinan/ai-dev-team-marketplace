# Changelog

All notable changes to this repository are documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-08-29

### Added

- Initial `ai-dev-team-marketplace` with `.claude-plugin/marketplace.json` registering one plugin: `ai-dev-team`.
- `ai-dev-team` plugin v0.1.0 with ten foundational skills: `continuing-project-work`, `orchestrating-development-team`, `analyzing-codebase`, `planning-implementation`, `implementing-features`, `debugging-systematically`, `testing-with-playwright`, `reviewing-code`, `auditing-security`, `preparing-releases`.
- Ten specialized agents: `solution-architect`, `repository-explorer`, `frontend-engineer`, `backend-engineer`, `database-engineer`, `qa-engineer`, `security-reviewer`, `code-reviewer`, `debugger`, `release-manager`.
- Shared plugin references: `evidence-and-safety.md`, `stack-detection.md`, `context-recovery.md`.
- Local validator (`scripts/validate.py`) and GitHub Actions CI (`.github/workflows/validate.yml`).
- Evaluation matrix (`tests/evals/`) with scenario-based evals for every skill.
- Architecture documentation: `docs/adr/0001-marketplace-architecture.md`, `docs/architecture/token-efficiency.md`, `ROADMAP.md`.
- Open-source project hygiene: `LICENSE` (Apache-2.0), `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, issue/PR templates.
