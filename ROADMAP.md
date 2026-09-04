# Roadmap

`ai-dev-team-marketplace` v0.1.0 shipped one plugin, `ai-dev-team`, with ten user-facing skills, one internal safety-baseline skill, and ten agents (see [README.md](README.md)). v0.2.0 has shipped — scope and rationale are recorded in [docs/V0.2.0_MASTER_PLAN.md](docs/V0.2.0_MASTER_PLAN.md), [ADR 0004](docs/adr/0004-v0.2.0-scope-and-consolidation.md) (scope & consolidation) and [ADR 0005](docs/adr/0005-database-migration-safety-model.md) (database migration safety model). Everything below that isn't marked as shipped is not implemented yet — inclusion is not a commitment to a specific release, and each family goes through the same design/eval bar as the v0.1.0 skills before shipping (see [CONTRIBUTING.md](CONTRIBUTING.md)).

## SHIPPED IN v0.2.0 (P0 — see ADR 0004)

- `managing-database-migrations` (new skill → `database-engineer`) — PostgreSQL/Supabase-aware migration authoring and review, RLS review, safety model per [ADR 0005](docs/adr/0005-database-migration-safety-model.md). Supersedes the former DATABASE roadmap line "PostgreSQL/Supabase migration authoring skill with online-migration patterns."
- `writing-automated-tests` (new skill → `qa-engineer`) — unit/integration test authoring and gap analysis, distinct from `testing-with-playwright` (E2E only). Supersedes the former QA roadmap line "Unit/integration test authoring skill."
- `reviewing-architecture` (new skill → `solution-architect`) — ADR generation, module-boundary and tech-debt review.
- `planning-deployment` (new skill → `release-manager`) — **promoted from P1 to P0** per v0.2.0 plan review. Platform-aware deploy/rollback/health-check planning; never executes a deploy.
- `auditing-security` DevSecOps extension — dependency/SCA, supply-chain, CI-security. Automation stays limited to deterministic checks; dependency-vulnerability detection uses real ecosystem tooling (`npm audit`, `pip-audit`, `osv-scanner`, `cargo audit`, etc.) where available, reporting evidence and limitations rather than a home-grown scanner — see ADR 0004. Supersedes the former DEVSECOPS roadmap line "Dependency vulnerability scanning (SCA)."
- `continuing-project-work` extension — module/PR/sanitization-scoped continuation routing. Partially supersedes the former CORE roadmap line "Deeper project-continuity heuristics" (multi-repo continuity remains open, see P2 below).
- `orchestrating-development-team` extension — role-coverage matrix naming all requested hats against existing agents, explicit token-budget rule.
- ADR 0004 (scope & consolidation) and ADR 0005 (database migration safety model).

## P1 (v0.2.x, next)

- API-contract review extension to `reviewing-code`/`planning-implementation` — narrow slice (OpenAPI diffing, breaking-change detection) of the former FULL STACK roadmap line "API contract design/versioning skill"; a Decisions-section addition, not a new skill.
- Advanced-E2E extension to `testing-with-playwright` — regression-suite patterns, API testing via Playwright's request context (partial QA family coverage).
- CI-failure-diagnosis reference for `debugging-systematically` — reading `gh run view --log-failed` output as evidence, not a new skill.
- `references/backend-patterns.md`, `references/frontend-patterns.md` — opt-in, framework-agnostic-where-possible reference material (queues/caching/multi-tenancy patterns; accessibility/performance/component-architecture heuristics). Reframes the former FULL STACK roadmap lines "Frontend-framework-specific deep dives" and "Backend performance profiling" as references, explicitly not new skills, per ADR 0001.

## P2 (v0.3+)

- Accessibility testing (axe-core/WCAG), visual regression, performance/load testing — remainder of the QA family; needs its own eval bar before it's more than a reference.
- Framework-specific *opt-in* reference packs for React/Next.js/Angular — remainder of the FULL STACK family; never top-level skills, per ADR 0001/ADR 0004.
- Vertical reference packs (SaaS/e-commerce/LegalTech/ERP/automotive/fitness) — unchanged, see below.
- Multi-repo project continuity, cross-agent conflict resolution for larger parallel orchestrations — remainder of the CORE family.
- Refactoring-specific skill (distinct from `implementing-features`, for large-scale structural change) — remainder of the CORE family.
- Issue-triage/labeling automation — remainder of the GITHUB family; revisit once there's evidence of real demand beyond direct `gh issue` usage.
- Query performance optimization, RLS policy authoring/testing as a standalone concern beyond what `managing-database-migrations` covers at authoring time — remainder of the DATABASE family.

## DO NOT BUILD YET (with reason — see ADR 0004)

- **Dedicated PR-description-authoring skill** — duplicates a Claude Code harness built-in (the "Creating pull requests" convention already in the system prompt).
- **Mobile (React Native/Expo) skill family** — a genuinely new stack family belongs in a new marketplace plugin, not bolted onto `ai-dev-team`.
- **Standalone "API/Backend" mega-skill** covering queues/caching/multi-tenancy/auth as one skill — too broad to write a tight, evaluable Decisions section for; kept as reference material only (P1 `backend-patterns.md`), not a skill.
- **New dedicated agents** (`github-engineer`, `devops-engineer`, `mobile-engineer`, etc.) — every v0.2.0 family maps onto one of the existing 10 agents; a new agent is a bigger structural commitment than a new skill, per ADR 0002/ADR 0004.
- **Docker/container hardening as its own skill** — folds into the `auditing-security` DevSecOps extension instead; splitting it out would review overlapping supply-chain surface twice.

## NOT YET TRIAGED (untouched by the v0.2.0 plan, still candidate future work)

- CI/CD pipeline authoring and review (DEVSECOPS)
- Secrets-management integration (Vault, cloud secret managers) beyond the current hygiene checks (DEVSECOPS)
- PR review automation (posting inline comments, not just producing findings) (GITHUB)
- Release/branch management automation (GITHUB)
- Changelog generation from conventional commits (GITHUB)
- Production sanitization skill (dedicated, beyond the checks in `preparing-releases`) (DELIVERY)
- Incident-response support skill (DELIVERY)
- Rollback execution (with explicit confirmation gating, per the safety policy) (DELIVERY)

## VERTICAL REFERENCE PACKS (future, opt-in, never hardcoded into core skills)

Domain-specific *reference* add-ons (not new mandatory skills) for common verticals — SaaS, e-commerce, LegalTech, ERP, automotive, fitness/gym, multi-tenant B2B — that a project can optionally layer on top of the core skills without the core skills themselves ever assuming a vertical.

## Non-goals

- Growing past a small number of excellent, composable skills per plugin. New families should become new plugins in this marketplace (or new opt-in references) rather than bloating `ai-dev-team` into a monolith. Reaffirmed for v0.2.0 in ADR 0004: mega-skills are prohibited absent concrete future evidence of real-world friction from the split, not design-time convenience.
- Hardcoding any specific customer/project's domain model, naming, or infrastructure into shared skill content.
