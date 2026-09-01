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

**LEVEL 4 — SHARED / STAGING / PRODUCTION.** `managing-database-migrations` / `database-engineer` **does not execute** against a shared, staging, or production target — not "after confirmation," not ever, regardless of how safe the migration looks or how explicitly the human confirms. Wording of the form "after confirmation the skill may execute" is disallowed anywhere this level is described. At this level the skill's job is bounded to: inspecting the target, preparing the migration, preparing the rollback, validating risks against the Required Considerations below, producing the exact commands/statements a human would run when that's useful, identifying the target/environment explicitly, and requesting and recording human confirmation of the plan. Then it **stops**. The correct, unambiguous wording is: **"human execution required; the skill/agent stops before execution."** Actually applying the migration against shared/staging/production is a separate human action performed outside `managing-database-migrations`/`database-engineer` entirely — it is not a later step the skill itself carries out.

**LEVEL 5 — DESTRUCTIVE / HIGH-BLAST-RADIUS.** Always requires explicit human confirmation, on top of and regardless of the LEVEL 3/4 environment classification — a destructive operation against even a demonstrated-disposable environment still needs the pause, because "disposable" claims are themselves sometimes wrong. Operations in this level: `DROP`, `TRUNCATE`, destructive `ALTER` (column/type narrowing, dropping a column or constraint with live dependents), irreversible backfill, RLS policy changes in production, mass `UPDATE`/`DELETE` without a scoped, reviewed predicate, schema reset, and migration rollback that causes data loss.

**CURRENT v0.1.0 GAP — read before relying on this level.** [`enforcing-safety-baseline`](../../plugins/ai-dev-team/skills/enforcing-safety-baseline/SKILL.md#irreversible-or-high-blast-radius-actions-require-explicit-confirmation), as shipped in v0.1.0 and left **unmodified by this PR**, currently reads: "destructive database migrations against anything but a disposable local/test database" require confirmation. Read literally, that sentence *exempts* a destructive operation against a disposable local/test database from the confirmation gate — precisely the case LEVEL 5 says must always be gated. The v0.1.0 baseline does **not yet** enforce LEVEL 5 as specified here. This ADR does not claim otherwise: LEVEL 5 is the target contract this project is committing to, not a description of what `enforcing-safety-baseline` already does today.

**REQUIRED PR #3 CHANGE.** PR #3 (the `managing-database-migrations` delivery PR — see [ADR 0004](0004-v0.2.0-scope-and-consolidation.md)) MUST update `enforcing-safety-baseline` before this contract becomes runtime-enforced. Until PR #3 lands that change, do not state or imply that "LEVEL 5 is already gated by `enforcing-safety-baseline`" — it is not. The required baseline update replaces the disposable-local/test exemption with a rule that distinguishes:

- **non-destructive operation on a demonstrated disposable local/test target** (LEVEL 3): no extra confirmation required;
- **destructive/high-blast-radius DB operation** (LEVEL 5): explicit confirmation always required, including on a demonstrated disposable local/test target — the disposable-target exemption applies to non-destructive LEVEL 3 operations only, never to LEVEL 5 ones.

PR #3 must also add regression/eval coverage proving all four of the following hold once the baseline update lands:

1. an additive (non-destructive) migration against a demonstrated-disposable test database does **not** trigger a redundant confirmation prompt;
2. a `DROP`/`TRUNCATE`/destructive migration against a demonstrated-disposable test database **does** require confirmation;
3. a shared/staging/production apply request is **never executed** by the skill/agent, regardless of confirmation — it stops before execution every time (LEVEL 4);
4. authoring a migration file locally is allowed with **no confirmation at all** (LEVEL 2).

### The core distinction

"Author migration" (LEVEL 2) and "apply migration" (LEVEL 3/4/5) are never the same action and must never be described or logged as if they were. A migration file existing in the repository, reviewed and even merged, has not been executed against anything — the skill must not imply otherwise, and must not claim "migration successful" without having actually run it against the specific target and inspected the result, per the evidence rule already in `enforcing-safety-baseline`. At LEVEL 3, "apply" may be an action the skill/agent itself takes once disposability is demonstrated; at LEVEL 4, "apply" is categorically a human action taken outside the skill/agent — the skill/agent's own involvement ends at the confirmation request, never at a completed execution.

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
- **Evidence of target environment before execution** — before any LEVEL 3 execution the skill carries out itself, and before any LEVEL 4 confirmation request it hands to a human, the skill states what evidence it has for which environment it's about to touch; "I assume this is local" is not evidence.

## Consequences

- **Positive:** `managing-database-migrations` can operate fluidly at LEVEL 1/2 (the large majority of "design/review a migration" requests) without training users to reflexively approve confirmation prompts, while LEVEL 4 gives the skill/agent a single unambiguous stop-before-execution rule for every shared/staging/production target.
- **Positive:** the required-considerations list gives the skill's eval scenarios (data-loss-risk migration, RLS leak, clean additive migration) concrete, checkable criteria instead of a vague "be careful" standard.
- **Trade-off:** the model is more complex than the single coarse rule it replaces, which means the skill's Decisions section has to state the level-classification logic explicitly rather than deferring to a one-line policy reference — accepted, since the alternative (the original coarse rule) is precisely what this review found insufficiently precise.
- **Known gap, not yet closed:** LEVEL 5's "always gated, even in disposable local/test" requirement is **not yet runtime-enforced** — `enforcing-safety-baseline` still carries the v0.1.0 disposable-local/test exemption this ADR flags above. This PR is docs-only and does not close that gap. **PR #3 MUST update `enforcing-safety-baseline` before this contract becomes runtime-enforced**, per the REQUIRED PR #3 CHANGE above, including the four regression/eval cases listed there. `managing-database-migrations` must not be considered complete without that baseline change landing first.
