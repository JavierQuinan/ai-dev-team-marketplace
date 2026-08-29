---
name: reviewing-code
description: Performs a professional code review of a diff, branch, or PR, classifying findings as BLOCKER, HIGH, MEDIUM, LOW or NIT across correctness, architecture, security, concurrency, transactions, authorization, tenancy, migrations, API contracts and test coverage. Use when asked to review code, check a PR, or evaluate a diff before merge.
when_to_use: Use for the REVIEW stage of a change, or whenever asked to "review this PR", "review this diff", "check this code".
---

# Reviewing code

Review with the goal of catching real defects, not generating volume. A review full of nitpicks buries the finding that matters. See [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md) — a finding is reported confirmed only once actually verified against the code, and a secret spotted in a diff is flagged by location, never quoted in full.

## What to check

- **Correctness** — does the code do what it claims; edge cases, off-by-ones, null/undefined handling, error paths actually handled (not just caught and swallowed).
- **Architecture** — fits existing layering/conventions; no unnecessary new abstraction; no duplicated logic that already exists elsewhere.
- **Readability/maintainability** — clear naming, no dead code, no misleading comments.
- **Performance** — obvious N+1 queries, unbounded loops over unbounded data, missing pagination/indexes on new hot paths.
- **Security** — see `auditing-security` for a full audit; a code review still flags obvious injection, missing authz checks, secrets in code, or unsafe deserialization inline.
- **Concurrency** — race conditions, missing locks/atomicity where two writers can interleave, unsafe shared state.
- **Transactions** — multi-step DB writes that should be atomic but aren't; missing rollback on partial failure.
- **Validation & authorization** — input validated at the boundary; every new endpoint/action checks the caller is allowed to do it, not just authenticated.
- **Tenancy** — every new query scoped to the right tenant; no code path that can leak cross-tenant data.
- **Migrations** — reversible where feasible, safe to run against production-sized data, backwards-compatible with the currently-deployed code during rollout.
- **API contracts** — breaking changes are visible and intentional, not incidental.
- **Test coverage** — new/changed behavior has tests; a bug fix has a regression test.
- **Regressions** — the diff doesn't silently remove or weaken existing checks (validation, auth, tests) to make something pass.

## Workflow

1. Read the actual diff, not just the final files — intent matters (what was removed/changed, not only what exists now).
2. For each finding, classify severity:
   - **BLOCKER** — breaks functionality, security hole, data loss/corruption risk, must not merge as-is.
   - **HIGH** — significant bug or risk, should be fixed before merge.
   - **MEDIUM** — real issue, could ship with a tracked follow-up if genuinely time-boxed.
   - **LOW** — minor correctness/maintainability issue.
   - **NIT** — style/preference, non-blocking, clearly labeled as optional.
3. For every finding, state the concrete failure scenario (what input/state causes what wrong behavior) — not just "this could be better."
4. Skip findings that are unverified speculation ("this might be slow") unless you can point to a concrete mechanism.
5. Report findings most-severe first. If nothing survives scrutiny, say so — an empty findings list is a valid, useful result.

## Decisions

- A pattern repeats across many lines but is consistent with existing codebase convention → note it once, don't repeat the same finding per occurrence.
- A finding is plausible but unverified (couldn't confirm without running code) → label it explicitly as unverified rather than stating it as fact.

## Exit criteria

- Every reported finding has a concrete failure scenario and a severity.
- No BLOCKER/HIGH finding is left unmentioned to keep the review short.
- The review distinguishes confirmed issues from plausible-but-unverified ones.
