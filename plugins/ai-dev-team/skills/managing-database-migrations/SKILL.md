---
name: managing-database-migrations
description: Designs, authors, and reviews PostgreSQL/Supabase schema changes and migrations — safety-level classification, rollback strategy, expand/contract sequencing, and RLS/tenant-isolation review. Use when asked to create, design, review, or audit a migration or schema change, review RLS policies, or produce a safe migration for staging/production.
when_to_use: USE for schema/migration/RLS authoring, review, or safety classification — "crea una migration para...", "diseña la migración...", "revisa este schema change", "audita esta migration", "revisa RLS", "migration segura para producción", "añade esta columna", "cambia el schema", "Supabase migration", or any request to add/remove/alter a column, table, index, constraint, or RLS policy. NOT USE for query debugging with no schema change, pure query-performance tuning with no schema impact, general business logic, or generic backend implementation that touches no schema/migration/RLS — those stay with `debugging-systematically` or `implementing-features`.
---

# Managing database migrations

PostgreSQL-first, Supabase-aware — not a generic skill for any database. If the project's detected persistence layer (see `references/stack-detection.md`) isn't PostgreSQL or Supabase, say so explicitly and state the scope limitation; never invent an equivalent for a different engine. See [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md): the safety levels below are this skill's specific application of that policy to database execution, not a separate or weaker gate.

## Workflow

1. **Detect the database.** Read package manifests, environment variable *names* only (never values), `supabase/`, `migrations/` or equivalent directories, schema files, ORM config, Docker/CI config. Identify the engine, the migration framework in use, the migration directory, and whether RLS is in use. Never assume — if the evidence doesn't support a conclusion, say so.
2. **Inspect current state.** Read the actual current schema, existing migrations and their naming convention, tenant-scoping columns, RLS policies, and any application code that depends on the schema being changed.
3. **Classify the safety level** (see below) and state the classification whenever it's material — a trivial local authoring request doesn't need it called out every time, but anything touching execution or a destructive operation always does.
4. **Design the migration.** Before writing, work through: rollback strategy, forward-only/expand-contract alternative, transaction semantics, lock/table-scan risk, large-table impact, backward compatibility, application/migration rollout ordering, RLS/tenant isolation (when applicable), indexes/constraints, nullability/default behavior. Mark any point not applicable with a one-line reason — never skip one silently. `references/database-safety.md` holds the concrete patterns behind each of these.
5. **Author.** LEVEL 2 work — creating or editing a migration/rollback file — needs no confirmation. Follow the project's existing migration tool and naming convention exactly; never introduce a second migration framework alongside one that already exists.
6. **Verify.** Run what the project supports: syntax/static checks, the migration tool's dry-run/check mode, relevant tests, and — only at LEVEL 3 — actual execution against a demonstrated-disposable database. Never state "migration successful" without having actually run it and inspected the result.

## Safety levels

This skill's application of [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md) to database execution:

- **LEVEL 1 — Read/analyze.** Schema inspection, migration history, RLS review, read-only `EXPLAIN`. No confirmation.
- **LEVEL 2 — Author local change.** Create/edit a migration file, a rollback/down file, an unexecuted SQL script, or tests. No confirmation — the default mode for most requests.
- **LEVEL 3 — Execute against a demonstrated-disposable local/test target.** May execute only once disposability is demonstrated with evidence (connection target, absence of production credentials, a fresh/seeded-only dataset) — never assumed. No evidence → treat as LEVEL 4.
- **LEVEL 4 — Shared/staging/production.** Never executed by this skill, not even after the user confirms. Inspect, prepare the migration and rollback, validate risk, produce the exact command a human would run, identify the target explicitly, and request/record confirmation — then stop. **Human execution required; the skill/agent stops before execution.** Never run `supabase db push`/`migration up` against a remote project, `psql` against a shared host, `prisma migrate deploy`, `typeorm migration:run`, `sequelize db:migrate`, or any equivalent against a non-disposable target.
- **LEVEL 5 — Destructive/high-blast-radius.** `DROP`, `TRUNCATE`, a destructive `ALTER` (narrowing, dropping a column/constraint with live dependents), an irreversible backfill, a production RLS change, a mass `UPDATE`/`DELETE` without a scoped predicate, a schema reset, a rollback that loses data. Always requires explicit human confirmation — including against a demonstrated-disposable LEVEL 3 target. A destructive operation is never executed just because the target is local.

## Decisions

- The project doesn't use PostgreSQL or Supabase → state the detected engine and the scope limitation explicitly; don't reuse Postgres-specific advice (RLS syntax, `CONCURRENTLY`, expand/contract specifics from `references/database-safety.md`) as if it applied unchanged.
- A request only touches query performance with no schema/index change → that's `debugging-systematically`/`implementing-features` territory, not this skill; redirect rather than manufacturing a migration.
- Disposability can't be demonstrated for a target the user calls "local" → treat as LEVEL 4, state exactly what evidence is missing; the user's label alone is never proof.
- A migration mixes an additive and a destructive change in one file → split it if possible; if not, classify and gate the whole unit at LEVEL 5 — the destructive part sets the level for what ships together.
- The project's existing migrations show a specific naming/format convention → match it exactly, even where `references/database-safety.md` would suggest a different default.
- A schema/query change affects tenant isolation or access control → also invoke `ai-dev-team:auditing-security` for the attacker/verification-angle review; this skill's RLS checklist covers authoring-time review, not a substitute for that audit.

## Exit criteria

- Every migration's output addresses all of the required-considerations points from step 4, or states why each doesn't apply — never a silent omission.
- No LEVEL 4/5 action was executed by this skill; every LEVEL 4/5 case ends in an explicit human-confirmation request, not a completed execution.
- "Migration successful" is never stated without an actual LEVEL 3 execution and an inspected result in this session.
- The safety-level classification shown in the response matches the action actually taken, never a lower level chosen for convenience.
