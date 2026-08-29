# Roadmap

`ai-dev-team-marketplace` v0.1.0 ships one plugin, `ai-dev-team`, with ten foundational skills and ten agents (see [README.md](README.md)). This roadmap lists future skill/agent families under consideration. Nothing below is implemented yet — inclusion here is not a commitment to a specific release, and each family will go through the same design/eval bar as the v0.1.0 skills before shipping (see [CONTRIBUTING.md](CONTRIBUTING.md)).

## CORE (extends v0.1.0)

- Deeper project-continuity heuristics (issue/PR trackers beyond `gh`, multi-repo continuity)
- Cross-agent conflict resolution for larger parallel orchestrations
- Refactoring-specific skill (distinct from `implementing-features`, for large-scale structural change)

## FULL STACK

- Frontend-framework-specific deep dives (component library conventions, state management patterns) as opt-in references, not new top-level skills
- API contract design/versioning skill
- Backend performance profiling

## QA

- Unit/integration test authoring skill (distinct from `testing-with-playwright`, for non-E2E suites)
- Accessibility testing (axe-core / WCAG checks)
- Visual regression testing
- Performance/load testing

## DEVSECOPS

- Dependency vulnerability scanning (SCA) as a dedicated skill or script bundled into `auditing-security`
- CI/CD pipeline authoring and review
- Docker/container hardening
- Secrets-management integration (Vault, cloud secret managers) beyond the current hygiene checks

## DATABASE

- PostgreSQL/Supabase migration authoring skill with online-migration patterns
- Query performance optimization
- RLS policy authoring and testing

## GITHUB

- Issue triage and labeling
- PR review automation (posting inline comments, not just producing findings)
- Release/branch management automation
- Changelog generation from conventional commits

## DELIVERY

- Production sanitization skill (dedicated, beyond the checks in `preparing-releases`)
- Incident-response support skill
- Rollback execution (with explicit confirmation gating, per the safety policy)

## VERTICAL REFERENCE PACKS (future, opt-in, never hardcoded into core skills)

Domain-specific *reference* add-ons (not new mandatory skills) for common verticals — SaaS, e-commerce, LegalTech, ERP, automotive, fitness/gym, multi-tenant B2B — that a project can optionally layer on top of the ten core skills without the core skills themselves ever assuming a vertical.

## Non-goals

- Growing past a small number of excellent, composable skills per plugin. New families should become new plugins in this marketplace (or new opt-in references) rather than bloating `ai-dev-team` into a monolith.
- Hardcoding any specific customer/project's domain model, naming, or infrastructure into shared skill content.
