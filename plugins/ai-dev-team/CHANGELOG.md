# Changelog — ai-dev-team plugin

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-08-29

### Added

- Ten user-facing skills covering project continuity, orchestration, codebase analysis, planning, implementation, debugging, Playwright E2E testing, code review, security auditing, and release preparation, plus one internal `enforcing-safety-baseline` skill.
- Ten specialized agents for delegated, role-scoped execution, each preloading the safety baseline and holding `Skill`-tool access to its mapped workflow skill.
- Shared references for stack detection and context recovery, to keep skill bodies small and consistent. The evidence/safety policy lives in the preloadable `enforcing-safety-baseline` skill instead of a reference file — see [ADR 0002](https://github.com/JavierQuinan/ai-dev-team-marketplace/blob/main/docs/adr/0002-agent-safety-baseline.md) in the marketplace repository.
