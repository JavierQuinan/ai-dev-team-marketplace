# Database migration safety reference (PostgreSQL / Supabase)

Deep patterns for `managing-database-migrations`, loaded only when actually authoring or reviewing a migration. Scope is PostgreSQL-first and Supabase-aware, per the project's database migration safety model (ADR 0005) — for any other persistence layer, `managing-database-migrations` states the scope limitation instead of guessing an equivalent from this content.

## Expand/contract as the default pattern

Prefer a multi-step, backward-compatible sequence over a single migration that changes shape and meaning at once:

1. **Expand** — add the new column/table/constraint alongside the old one; both old and new application code keep working.
2. **Migrate data** — backfill in batches (see below), dual-write if the rollout window is long.
3. **Cut over** — deploy application code that reads/writes only the new shape.
4. **Contract** — once no code path depends on the old shape, drop it in a separate, later migration.

A single migration that renames a column, changes its type, or moves data and drops the old shape in one step is the shape of change most likely to break a rolling deploy, because it assumes application code updates atomically with the schema — it never does.

## Adding a column safely

- **Nullable column, no default**: safe, metadata-only change on modern Postgres (11+) — no table rewrite, no long lock.
- **Nullable column with a default**: Postgres 11+ handles a constant default as metadata-only (no rewrite). A *non-constant* default (e.g. `now()`, a function call, a sequence) still forces a rewrite — check the actual default expression, not just "does it have a default."
- **`NOT NULL` column**: never add `NOT NULL` directly to a populated table in one step. Sequence: add nullable → backfill in batches → add a `NOT VALID` check constraint for `NOT NULL` semantics → `VALIDATE CONSTRAINT` (takes a lesser lock, scans without blocking writes) → only then convert to a real `NOT NULL` once validated, or leave the validated check constraint as the enforcement mechanism.

## Indexes and constraints

- **Always `CREATE INDEX CONCURRENTLY`** for an index on an existing table with meaningful row count — a plain `CREATE INDEX` takes a lock that blocks writes for the build's duration. `CONCURRENTLY` cannot run inside the same transaction as other DDL — it needs its own migration step, and the migration tooling must support running it outside a transaction wrapper.
- **Foreign keys**: adding one to an existing table takes `SHARE ROW EXCLUSIVE` and validates all existing rows by default. Add it `NOT VALID` first (fast, doesn't scan), then `VALIDATE CONSTRAINT` in a separate step (scans but doesn't block writes as heavily).
- **Check constraints**: same `NOT VALID` → `VALIDATE CONSTRAINT` two-step pattern for large tables.
- **Dropping a constraint or index**: generally cheap and fast, but confirm no application code or query plan silently depends on it (a unique constraint enforcing app-level invariants, an index a hot query relies on).

## Locking and long transactions

- Most `ALTER TABLE` variants take `ACCESS EXCLUSIVE` (blocks all reads and writes) for at least a brief instant, even for a metadata-only change — the risk is the *duration* of that hold, not whether a lock is taken at all.
- A long-running transaction elsewhere (an open `BEGIN`, a slow report query) can make even a fast `ALTER TABLE` wait indefinitely for its lock while queuing every subsequent query behind it — check for long-running transactions/statements before a migration that needs a strong lock on a hot table.
- Set a `lock_timeout` for migration statements against production-sized or hot tables so a blocked migration fails fast and visibly instead of silently queuing behind other traffic and taking the table down when it finally acquires the lock.

## Large tables and backfills

- A full-table rewrite (e.g. changing a column's type incompatibly, adding a non-constant default pre-Postgres-11 behavior) scales with table size and holds a strong lock for the duration — treat this as a required-considerations flag, not an afterthought.
- **Batch backfills**: update in bounded batches (by primary key range or a fixed row count per statement) with a brief pause between batches, not one `UPDATE` touching every row — an unbatched mass update on a large table holds locks and generates WAL/replication load proportional to the whole table at once.
- State an estimate of row count / table size when known, and flag when it isn't known but the table is likely to be large (based on what it stores).

## Rollback realities

- A rollback migration that only reverses schema shape does not restore data that a forward migration deleted or transformed — state this explicitly rather than presenting a down-migration as a full undo when it isn't.
- Prefer additive, forward-only steps precisely because they don't need a destructive rollback at all — the "rollback" for an expand step is often just "stop deploying the code that uses the new column," not a schema reversal.
- For a genuinely destructive forward step, state what a rollback can and cannot restore before authoring it, not after.

## Backward compatibility and rollout ordering

- Decide and state explicitly whether the migration deploys **before**, **after**, or **interleaved with** the application code change — for expand/contract, migrate-then-deploy is usually correct for the expand step (new column exists before code reads/writes it) and deploy-then-contract is correct for the contract step (no code depends on the old shape before it's dropped).
- During any rolling deploy window, both the previous and next application release may run against the same schema simultaneously — a migration must not break the release that hasn't rolled out yet.

## RLS and tenant isolation (Postgres RLS / Supabase)

Checklist for any migration touching a table with row-level security or tenant-scoped access:

- Does the new/changed table have RLS enabled (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`)? A tenant-scoped table with RLS left disabled is a full cross-tenant exposure, not a partial one.
- Does every policy (`SELECT`/`INSERT`/`UPDATE`/`DELETE`) filter by the tenant/ownership column, not just the `SELECT` policy? A missing `UPDATE` or `DELETE` policy can leave those operations open even when reads are correctly scoped.
- For Supabase specifically: does the policy correctly use `auth.uid()` (or the project's equivalent claim) against the row's owner/tenant column, rather than a client-supplied value that could be spoofed?
- Any function marked `SECURITY DEFINER` runs with the privileges of its owner, not the caller — a schema change that adds or touches one needs its own explicit tenant-scoping check, since RLS on the underlying tables doesn't automatically constrain what a `SECURITY DEFINER` function does internally.
- A new table storing tenant-scoped data needs a policy from the moment it's created — there is no "add the table now, add RLS later" safe sequencing once real writes can happen.
- This checklist covers *authoring*-time review. A build-time/attacker-angle verification of the same policies is `auditing-security`'s job, not a duplicate of this one — cross-link, don't merge.

## Enum and type changes

- Adding a value to a Postgres native `enum` type is fast but **cannot run inside the same transaction as its own use** in that transaction — a migration that adds an enum value and immediately inserts a row using it in the same transaction will fail; split into two migrations or two transactions.
- Removing an enum value, or narrowing a column's type, is destructive if any existing row uses the value/wider type being removed — treat as LEVEL 5 (destructive), not a routine type tweak.
- Prefer a `text` column with a `CHECK` constraint over a native `enum` when the set of values is expected to change — a check constraint can be altered without the enum's transactional restrictions.

## Migration tooling conventions

Detect and follow whatever migration tool the project already uses — don't introduce a second one:

| Evidence | Tool | Notes |
|---|---|---|
| `supabase/migrations/*.sql` | Supabase CLI migrations | Sequential timestamped `.sql` files; `supabase db diff`/`db push` conventions |
| `prisma/migrations/` | Prisma Migrate | `schema.prisma` is the source of truth; migrations are generated, not usually hand-authored |
| `drizzle/` + `drizzle.config.*` | Drizzle ORM | Generated SQL migrations from a TypeScript schema |
| `db/migrate/` (Rails-style) or a `knex`/`typeorm`/`sequelize` migrations directory | Framework-native migration tool | Follow the existing up/down file pairing convention |
| Plain numbered/timestamped `.sql` files with no framework | Hand-rolled | Match the existing naming and up/down (or forward-only) convention exactly |

## Application rollout ordering summary

| Migration type | Safe ordering |
|---|---|
| Additive (new nullable column/table) | Migrate first, deploy code second |
| Contract (drop old column/table) | Deploy code first (stop using it), migrate second |
| Rename | Never in one step — expand (add new) → dual-write/backfill → deploy reads-from-new → contract (drop old) |
| Type change, backward-compatible | Migrate first if the old type still round-trips through the new one; otherwise treat as a rename |
