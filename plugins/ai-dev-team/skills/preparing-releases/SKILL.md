---
name: preparing-releases
description: Verifies release readiness — git state, build, typecheck, lint, tests, E2E, secrets, demo/tenant data contamination, migrations, docs, changelog and version — and issues a GO / CONDITIONAL GO / NO-GO verdict backed by evidence. Use when asked to prepare a release, sanitize a project for production, or confirm something is ready to ship.
when_to_use: Use before a release, deploy, or when asked "deja esto listo para producción" / "is this ready to ship".
---

# Preparing releases

Produce a release-readiness verdict backed by checks actually run in this session — never assert readiness from inspection alone. See [references/evidence-and-safety.md](../../references/evidence-and-safety.md): deploying to production always requires explicit human confirmation, this skill prepares and verifies, it does not deploy.

## Checklist

Run each applicable check and record its real result:

1. **Git state** — clean working tree or explicitly-reviewed pending changes; correct target branch; no accidental local-only commits.
2. **Build** — the project's actual build command, executed, output inspected.
3. **Typecheck** — if the stack has one (TS, mypy, etc.), executed.
4. **Lint** — executed, not assumed clean.
5. **Tests** — unit/integration suite executed; report pass/fail counts, not "should pass."
6. **E2E** — relevant Playwright/Cypress suite executed if one exists and the change touches user-facing flows.
7. **Secrets** — no `.env` with real values, no hardcoded credentials/API keys/tokens in the diff or tracked files; `.env.example` uses placeholders only.
8. **Demo/tenant data contamination** — no test/seed/demo data, debug flags, or hardcoded tenant-specific values left enabled for production.
9. **Migrations** — reviewed for safety (reversibility, lock behavior on large tables, backwards compatibility during rollout); not auto-applied to production by this skill.
10. **Env examples** — `.env.example` (or equivalent) reflects the actual required variables.
11. **Documentation** — README/docs updated for user-visible changes.
12. **CHANGELOG** — entry added describing the release's actual changes.
13. **Version** — bumped consistently across manifests (`package.json`, `plugin.json`, etc.) per the project's versioning scheme.
14. **Rollback plan** — documented for anything risky in this release (migrations, infra changes).

## Verdict

- **GO** — every applicable check passed with evidence; no BLOCKER/HIGH findings outstanding.
- **CONDITIONAL GO** — no BLOCKER, but specific HIGH/MEDIUM items remain, each named with owner/action needed; safe to proceed only if those are accepted knowingly.
- **NO-GO** — any BLOCKER (failing tests, secrets exposed, unsafe migration, broken build) — list exactly what must be fixed first.

Never issue GO because most checks passed — a single unresolved BLOCKER is a NO-GO regardless of how much else is clean.

## Decisions

- A check can't be run in this environment (no CI access, no staging DB) → mark it "not verified — manual check required," never assume pass.
- Version bump policy is ambiguous (no clear semver convention) → ask rather than guessing major/minor/patch.
- Migration looks destructive (drops a column with existing data) → flag as BLOCKER unless the user has already explicitly authorized it with a stated rollback plan.

## Exit criteria

- Verdict (GO/CONDITIONAL GO/NO-GO) is stated explicitly with the checklist results that produced it.
- No item is marked passed without having actually been run in this session.
- Production deployment itself is never performed by this skill without separate explicit confirmation.
