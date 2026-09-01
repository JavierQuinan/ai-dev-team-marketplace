# ADR 0005: Database migration safety model

## Status

Accepted — 2026-09-01 (human review of `docs/V0.2.0_MASTER_PLAN.md`, approved with adjustments)

## Context

`managing-database-migrations` (P0, mapped to the `database-engineer` agent) is the highest-risk new skill in v0.2.0: schema and data changes are the least reversible category of action this plugin touches. The master plan's original draft folded "author" and "apply" together under one coarse rule inherited from [`enforcing-safety-baseline`](../../plugins/ai-dev-team/skills/enforcing-safety-baseline/SKILL.md) ("destructive database migrations against anything but a disposable local/test database" require confirmation).

Human review found that framing insufficiently precise for a skill whose entire job is to *author* migrations: an agent that has to stop and ask for confirmation before writing or editing a migration file — a reversible, local, git-tracked change — would be unusable, and would train users to rubber-stamp confirmation prompts, weakening the gate for when it actually matters. The review's explicit instruction: **never confuse "author migration" with "apply migration."** This ADR replaces the coarse rule with a five-level model that separates the two cleanly, and states the additional design considerations a migration must address regardless of level.

## Decision

### Five safety levels

**LEVEL 1 — READ / ANALYZE.** Permitted without confirmation: schema inspection, migration-history inspection, RLS policy review, `EXPLAIN`/read-only evidence gathering where the underlying query is provably non-mutating. No state changes; this level exists to let the skill build an accurate picture before proposing anything.

**LEVEL 2 — AUTHOR LOCAL CHANGE.** Permitted without additional confirmation: creating a migration file, editing a migration file that has not been applied anywhere shared, creating a rollback/down-migration file, creating a SQL script that is not executed, adding or updating tests. This is git-tracked, reversible-by-deletion, and affects no running system. This is the default mode `managing-database-migrations` operates in for the large majority of requests ("design a migration for X", "review this schema change").

**LEVEL 3 — EXECUTION AGAINST A DISPOSABLE LOCAL/TEST ENVIRONMENT.** May be executed without a human-confirmation pause **only when the environment has been demonstrated, not assumed, to be disposable/local/test and to contain no real data** — e.g. a project-local Docker Postgres, a CI ephemeral database, a Supabase local dev stack. "Demonstrated" means the skill states what evidence establishes disposability (connection target, absence of production credentials, a fresh/seeded-only dataset) before running anything; if that evidence can't be produced, treat the target as LEVEL 4 by default rather than assuming safety.

**LEVEL 4 — SHARED / STAGING / PRODUCTION EXECUTION.** Requires explicit human confirmation before execution, every time, regardless of how safe the migration looks. This includes any environment reachable by other developers, any staging environment gating a real release, and production without exception. This is a stop-and-ask gate per [`enforcing-safety-baseline`](../../plugins/ai-dev-team/skills/enforcing-safety-baseline/SKILL.md#irreversible-or-high-blast-radius-actions-require-explicit-confirmation), not a warning the skill can talk itself past.

**LEVEL 5 — DESTRUCTIVE / HIGH-BLAST-RADIUS.** Always requires explicit human confirmation, on top of and regardless of the LEVEL 3/4 environment classification — a destructive operation against even a claimed-disposable environment still needs the pause, because "disposable" claims are themselves sometimes wrong. Operations in this level: `DROP`, `TRUNCATE`, destructive `ALTER` (column/type narrowing, dropping a column or constraint with live dependents), irreversible backfill, RLS policy changes in production, mass `UPDATE`/`DELETE` without a scoped, reviewed predicate, schema reset, and migration rollback that causes data loss. This is gated by [`enforcing-safety-baseline`](../../plugins/ai-dev-team/skills/enforcing-safety-baseline/SKILL.md) directly — `managing-database-migrations` does not get its own weaker version of this gate.

### The core distinction

"Author migration" (LEVEL 2) and "apply migration" (LEVEL 3/4/5) are never the same action and must never be described or logged as if they were. A migration file existing in the repository, reviewed and even merged, has not been executed against anything — the skill must not imply otherwise, and must not claim "migration successful" without having actually run it against the specific target and inspected the result, per the evidence rule already in `enforcing-safety-baseline`.

### Required considerations for every authored migration, regardless of level

`managing-database-migrations` must address each of the following in its output, or explicitly state why it doesn't apply to the migration at hand — silence on any of these is treated as an incomplete review, not an implicit "not applicable":

- **Rollback strategy** — a concrete down-migration or documented manual rollback path, not "roll back by restoring a backup" as the only answer.
- **Forward-only alternative** — whether an additive, forward-only change (e.g. add-column-then-backfill-then-drop-old-column across releases) is safer than a single reversible-looking migration that is actually risky to reverse once data has changed underneath it.
- **Transaction implications** — whether the migration runs inside a single transaction, whether the target database/DDL supports transactional DDL for the operations used, and what happens on partial failure.
- **Lock / table-scan risk** — whether the operation takes a lock that blocks reads/writes for the migration's duration, and for how long that's expected to hold.
- **Large-table consideration** — whether the operation's cost scales with table size (a full table rewrite, an index build without `CONCURRENTLY`, a backfill) and what the plan is if the table is large in the target environment.
- **Backward compatibility** — whether application code from the *previous* release can still run correctly against the *new* schema, and vice versa, during a rolling deploy window.
- **Application/migration rollout ordering** — the explicit sequencing between deploying application code and applying the migration (migrate-then-deploy vs. deploy-then-migrate vs. expand/contract), stated, not left implicit.
- **RLS/tenant isolation review, when applicable** — any migration touching a table with row-level security or tenant-scoped access must state whether existing policies still hold correctly against the new schema shape.
- **Evidence of target environment before execution** — before any LEVEL 3+ execution, the skill states what evidence it has for which environment it's about to touch; "I assume this is local" is not evidence.

## Consequences

- **Positive:** `managing-database-migrations` can operate fluidly at LEVEL 1/2 (the large majority of "design/review a migration" requests) without training users to reflexively approve confirmation prompts, while LEVEL 4/5 keeps the exact same hard stop `enforcing-safety-baseline` already establishes for every other irreversible action.
- **Positive:** the required-considerations list gives the skill's eval scenarios (data-loss-risk migration, RLS leak, clean additive migration) concrete, checkable criteria instead of a vague "be careful" standard.
- **Trade-off:** the model is more complex than the single coarse rule it replaces, which means the skill's Decisions section has to state the level-classification logic explicitly rather than deferring to a one-line policy reference — accepted, since the alternative (the original coarse rule) is precisely what this review found insufficiently precise.
- **Follow-up:** `enforcing-safety-baseline`'s own irreversible-action list should, when `managing-database-migrations` ships (PR #3 in the consolidated sequence — see [ADR 0004](0004-v0.2.0-scope-and-consolidation.md)), be cross-checked against LEVEL 4/5 here to confirm the baseline's existing "destructive database migrations" phrase is read as covering exactly LEVEL 4 and LEVEL 5, not LEVEL 3.
