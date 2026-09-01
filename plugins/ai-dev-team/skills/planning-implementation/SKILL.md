---
name: planning-implementation
description: Converts a feature or change request into a right-sized, executable technical plan covering scope, affected files, DB/API/frontend impact, tests, security, backwards compatibility, rollout and rollback. Use before implementing anything beyond a trivial, single-file change.
when_to_use: Use when a request needs a plan before code — non-trivial features, cross-cutting changes, anything touching data or contracts — including a plain request for the plan itself: "dame un plan de implementación", "necesito un plan antes de implementar esto", "give me an implementation plan", "how would you implement this". Skip for one-line fixes or trivial edits; go straight to implementing-features instead.
---

# Planning implementation

Turn a request into a plan sized to the actual change — not a template filled out regardless of scope. A one-file bug fix gets a sentence, not a document.

## Workflow

1. **Confirm scope with evidence.** Use the output of `analyzing-codebase` if it already ran this session; otherwise gather just enough context (affected module, existing patterns) to plan accurately — don't re-run a full codebase analysis for a small change.
2. **Size the change** before writing anything further:
   - Trivial (single file, no contract/schema change, no new dependency) → skip the rest of this workflow, note the one-line approach, proceed to `implementing-features`.
   - Non-trivial → continue with the full plan below.
3. **Draft the plan**, covering only the sections that actually apply:
   - **Scope** — what's in, what's explicitly out.
   - **Affected files/modules** — named, not "various files."
   - **Dependencies** — new packages, version constraints, why each is needed.
   - **Database impact** — schema changes, migration strategy, whether it's backwards-compatible with the currently-deployed code.
   - **API impact** — new/changed endpoints or contracts, versioning/compatibility.
   - **Frontend impact** — new UI, state changes, affected components.
   - **Tests** — what needs new/updated coverage (unit, integration, E2E).
   - **Security** — auth/authorization changes, tenant isolation impact, input validation surface (flag for `auditing-security` if non-trivial).
   - **Backwards compatibility** — what could break for existing users/data/integrations.
   - **Rollout** — order of operations if multi-step (e.g. migrate → deploy backend → deploy frontend).
   - **Rollback** — how to undo if something goes wrong, especially for migrations.
4. **Surface risk and open questions** explicitly rather than picking silently among ambiguous options — ask the user when a decision materially changes scope or risk.
5. **Hand off** to `implementing-features` with the plan as the contract for what "done" means.

## Decisions

- Request is vague about behavior in an edge case that changes design → ask, don't assume, before planning further.
- Plan would require a destructive migration or breaking API change → flag explicitly and note it needs explicit confirmation before execution (see [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md)).
- Change is trivial → do not produce a multi-section plan; a one-line description of the approach is the plan.

## Exit criteria

- The plan is sized to the change — no gigantic plan for a trivial fix, no missing risk section for a schema change.
- Every section present in the plan is actionable (names files, commands, or concrete steps), not generic advice.
- Rollback is defined for anything that touches persisted data or public contracts.
