---
name: analyzing-codebase
description: Produces a verifiable technical map of a repository — stack, architecture, persistence, auth/tenancy, testing, CI/CD, and conventions — detected from actual evidence rather than assumed from the project's domain. Use when asked to "analyze this project", "understand this codebase", or before planning/implementing in an unfamiliar repo.
when_to_use: Use at the start of work in an unfamiliar repo, when the user asks to analyze/map/understand the codebase, or as the DISCOVER stage of orchestrating-development-team.
---

# Analyzing the codebase

Build a technical map of the repository grounded in evidence: every claim traces to a file, dependency, or config entry actually found. See [references/stack-detection.md](../../references/stack-detection.md) for the detection patterns this skill applies across frontend, backend, database, testing, and infrastructure, and [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md) for the evidence and secret-hygiene rules this skill follows — a config file scanned during discovery may contain a real credential; it gets flagged by location, never reproduced in full.

## Workflow

1. **Survey structure fast.** `Glob` for manifest/config files (package.json, composer.json, requirements.txt, angular.json, playwright.config.*, docker-compose.yml, etc.) before reading full source trees. Determine monorepo vs. single-app from workspace/package manager signals.
2. **Detect the stack.** Apply `stack-detection.md` patterns for frontend, backend, database/persistence, testing, and infrastructure. Report only technologies with actual evidence; when evidence is ambiguous, read the specific config to disambiguate rather than guessing.
3. **Map architecture.** Identify layering (e.g. controllers/services/repositories, feature-based modules, monorepo packages), how frontend and backend communicate (REST/GraphQL/RPC contracts), and where cross-cutting concerns live (auth, validation, error handling).
4. **Identify persistence and tenancy.** Locate schema/migrations, ORM/query layer, and any multi-tenancy mechanism (row-level security, tenant_id columns, separate schemas/databases). This feeds `auditing-security` later — don't skip it even if not explicitly asked.
5. **Identify verification surface.** Locate test suites and what they cover, lint/typecheck/build commands (from `package.json` scripts, `Makefile`, CI config), and existing CI/CD pipelines.
6. **Extract conventions.** Naming patterns, folder structure rules, existing ADRs or style guides (`CONTRIBUTING.md`, `docs/`), commit message conventions from `git log`.
7. **Produce the map** as a structured summary: Stack, Architecture, Persistence & Tenancy, Testing & CI, Conventions, Open Questions (things that couldn't be determined from evidence).

## Decisions

- Two frameworks show partial evidence (e.g. both `express` and `fastify` as dependencies) → read the actual server entrypoint to see which is wired up, don't report both as active.
- No test suite found → report that explicitly as a gap, don't infer testing practices from the codebase's apparent quality.
- Domain suggests a stack (e.g. "this looks like an e-commerce app so it probably uses Stripe") but no evidence found → do not report it; only report what's verified.

## Exit criteria

- Every entry in the technical map cites the evidence that produced it (file path, dependency name, config value).
- The map explicitly lists what could not be determined, rather than omitting it silently.
- Output is reusable as input to `planning-implementation`, `implementing-features`, and `auditing-security` without re-discovery.
