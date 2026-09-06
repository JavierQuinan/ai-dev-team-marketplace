# Changelog

All notable changes to this repository are documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.1] - 2026-09-06

### Added

- Directional API-contract compatibility guidance for `reviewing-code` and `planning-implementation`, via a new shared reference (`plugins/ai-dev-team/references/api-contract-review.md`): request/response asymmetry, evidence-driven OpenAPI/Swagger detection with a valid source-based fallback when no formal spec exists, enum/path/status-code compatibility rules, and explicit false-positive guardrails. Not a new skill and not a new agent — an extension of the two existing skills' Decisions sections.
- API breaking-change rollout/versioning/deprecation planning guidance in `planning-implementation`'s existing API-impact section (additive rollout, deprecate-then-remove, dual-field transition, parallel versions, or a coordinated rollout only with evidence every affected consumer can migrate in lockstep).
- `NOTICE` with project attribution for Apache-2.0 distributions.
- `.github/CODEOWNERS` with explicit ownership for repository-wide and security/release-sensitive paths.
- `.github/dependabot.yml` for weekly GitHub Actions dependency updates.
- Structured GitHub Discussions Q&A form for reproducible support requests and safer evidence sharing.

### Changed

- Runtime-verified that delegating a stage's specialist synchronously (`run_in_background: false`) prevents the duplicate specialist-stage execution observed in earlier testing of `orchestrating-development-team`, for the cases tested — not a claim of guaranteed deterministic model behavior.
- `orchestrating-development-team`'s task-packet correctness is now judged by material content (goal, scope, relevant files, expected output) rather than requiring literal template headings, matching what real usage actually showed.
- Added worked Small/Medium/Large delegation right-sizing examples and boundary evals to `orchestrating-development-team`'s budget reference, based on a corrected reading of prior runtime evidence.
- Restored the canonical Apache License 2.0 text and moved project attribution to `NOTICE`.
- Clarified inbound contribution licensing, third-party material expectations, and the current no-CLA/no-DCO contribution model.
- Updated `SECURITY.md` support to the current 0.2.x line and tightened coordinated-disclosure guidance.
- Improved README/contribution discoverability and community entry points.
- Protected the default branch with repository rules requiring pull requests, the `validate` status check, up-to-date branches, conversation resolution, linear history, squash-only merges, and blocking branch deletion/force-pushes.
- Repository-local Claude attribution disabled so Git authorship and PR attribution remain explicitly human-controlled.

## [0.2.0] - 2026-09-04

Scope and rationale: [docs/V0.2.0_MASTER_PLAN.md](docs/V0.2.0_MASTER_PLAN.md), [ADR 0004](docs/adr/0004-v0.2.0-scope-and-consolidation.md), [ADR 0005](docs/adr/0005-database-migration-safety-model.md).

### Added

- `managing-database-migrations` skill (→ `database-engineer`) — PostgreSQL/Supabase-aware migration authoring/review and RLS review, with a five-level safety model (ADR 0005).
- `writing-automated-tests` skill (→ `qa-engineer`) — unit/integration test authoring and gap analysis, distinct from the existing E2E-only `testing-with-playwright`.
- `reviewing-architecture` skill (→ `solution-architect`) — ADR generation, module-boundary and tech-debt review.
- `planning-deployment` skill (→ `release-manager`) — platform-aware deploy/rollback/health-check planning; never executes a deploy.
- `auditing-security` DevSecOps extension — dependency/SCA, supply-chain and CI-security checks using real ecosystem tooling (`npm audit`, `pip-audit`, `osv-scanner`, `cargo audit`) where available.
- `continuing-project-work` extension — module/PR/sanitization-scoped continuation routing.
- `orchestrating-development-team` extension — role-coverage matrix and explicit token-budget rule for full-team orchestration.
- New eval sets for all four new skills under `tests/evals/`.

### Changed

- `marketplace.json` and `plugin.json` version bumped to 0.2.0; plugin description now reflects the four new skill families.
- PRs #3–#6 (database, engineering-quality, security-continuity, orchestration-deployment) were originally merged into a `release/v0.2.0` branch that had not been promoted to `main`; this release closes that gap.

## [0.1.0] - 2026-09-01

### Added

- Initial `ai-dev-team-marketplace` with `.claude-plugin/marketplace.json` registering one plugin: `ai-dev-team`.
- `ai-dev-team` plugin v0.1.0 with ten user-facing skills: `continuing-project-work`, `orchestrating-development-team`, `analyzing-codebase`, `planning-implementation`, `implementing-features`, `debugging-systematically`, `testing-with-playwright`, `reviewing-code`, `auditing-security`, `preparing-releases`.
- An eleventh, internal skill, `enforcing-safety-baseline` (`user-invocable: false`), carrying the evidence/safety policy so it can be preloaded into every agent and linked from every workflow skill.
- Ten specialized agents: `solution-architect`, `repository-explorer`, `frontend-engineer`, `backend-engineer`, `database-engineer`, `qa-engineer`, `security-reviewer`, `code-reviewer`, `debugger`, `release-manager`. Each preloads `enforcing-safety-baseline` and gets `Skill`-tool access to its mapped workflow skill.
- Shared plugin references: `stack-detection.md`, `context-recovery.md`.
- Local validator (`scripts/validate.py`), now multi-plugin (reads `.claude-plugin/marketplace.json` and validates every declared local plugin, not just `ai-dev-team`), plus official `claude plugin validate` in CI.
- GitHub Actions CI (`.github/workflows/validate.yml`), pinned to current, non-deprecated action versions by commit SHA.
- Evaluation matrix (`tests/evals/`) with scenario-based evals for every skill, including the new safety-baseline skill and a small-repository context-recovery case.
- Architecture documentation: `docs/adr/0001-marketplace-architecture.md`, `docs/adr/0002-agent-safety-baseline.md`, `docs/architecture/token-efficiency.md` (corrected subagent-context model), `ROADMAP.md`.
- Open-source project hygiene: `LICENSE` (Apache-2.0), `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, issue/PR templates.

### Fixed

- Agents no longer silently depend on a parent skill's safety discipline — see ADR 0002.
- `analyzing-codebase`, `debugging-systematically`, `reviewing-code` now link the safety baseline, matching the other seven workflow skills.
- `scripts/validate.py` validates every plugin declared in `marketplace.json`, not just a hardcoded `ai-dev-team` path, and now checks each skill's frontmatter `name` (format, uniqueness, match with its directory).
- `context-recovery.md` and `continuing-project-work` no longer assume `HEAD~5`-style history exists; they scale to whatever history is actually available.
