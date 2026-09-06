# Changelog — ai-dev-team plugin

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [Semantic Versioning](https://semver.org/).

## [0.2.1] - 2026-09-06

### Added

- API-contract compatibility guidance/reference integrated into `reviewing-code` and `planning-implementation` — directional request/response compatibility, evidence-based OpenAPI/Swagger detection, and API breaking-change rollout/versioning/deprecation planning. Not a new skill.

### Changed

- Runtime-verified that delegating a stage's specialist synchronously (`run_in_background: false`) prevents the duplicate specialist-stage execution observed in earlier testing of `orchestrating-development-team`, for the cases tested — not a claim of guaranteed deterministic model behavior.
- Task-packet correctness is judged by material content (goal, scope, relevant files, expected output) rather than requiring literal template headings.
- Delegation right-sizing worked examples (Small/Medium/Large) and boundary evals added to the orchestration budget reference.

## [0.2.0] - 2026-09-04

### Added

- `managing-database-migrations` skill (→ `database-engineer`) — PostgreSQL/Supabase-aware migration authoring/review and RLS review, with a five-level safety model.
- `writing-automated-tests` skill (→ `qa-engineer`) — unit/integration test authoring and gap analysis, distinct from the E2E-only `testing-with-playwright`.
- `reviewing-architecture` skill (→ `solution-architect`) — ADR generation, module-boundary and tech-debt review.
- `planning-deployment` skill (→ `release-manager`) — platform-aware deploy/rollback/health-check planning; never executes a deploy.
- `auditing-security` DevSecOps extension — dependency/SCA, supply-chain and CI-security checks using real ecosystem tooling where available.
- `continuing-project-work` extension — module/PR/sanitization-scoped continuation routing.
- `orchestrating-development-team` extension — role-coverage matrix and explicit token-budget rule for full-team orchestration.

## [0.1.0] - 2026-08-29

### Added

- Ten user-facing skills covering project continuity, orchestration, codebase analysis, planning, implementation, debugging, Playwright E2E testing, code review, security auditing, and release preparation, plus one internal `enforcing-safety-baseline` skill.
- Ten specialized agents for delegated, role-scoped execution, each preloading the safety baseline and holding `Skill`-tool access to its mapped workflow skill.
- Shared references for stack detection and context recovery, to keep skill bodies small and consistent. The evidence/safety policy lives in the preloadable `enforcing-safety-baseline` skill instead of a reference file — see [ADR 0002](https://github.com/JavierQuinan/ai-dev-team-marketplace/blob/main/docs/adr/0002-agent-safety-baseline.md) in the marketplace repository.
