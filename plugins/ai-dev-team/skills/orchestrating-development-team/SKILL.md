---
name: orchestrating-development-team
description: Acts as tech lead for multi-part software delivery, coordinating architecture, frontend, backend, database, QA, security, DevOps, review and release work through the plugin's specialized agents and skills. Use for requests spanning multiple disciplines or an end-to-end delivery ("build this feature and ship it", "act as the full dev team").
when_to_use: Use when a request needs more than one discipline (e.g. backend + frontend + tests) or explicitly asks for full-team/end-to-end delivery. For a single-discipline task, invoke the specific skill directly instead.
---

# Orchestrating the development team

Coordinate the plugin's skills and agents (see [agents/](../../agents/)) through a fixed pipeline so multi-part work stays coherent, verifiable, and free of conflicting concurrent edits. This skill is the router for cross-cutting requests — it delegates depth to the other nine skills rather than duplicating their instructions.

## Pipeline

```
DISCOVER → PLAN → IMPLEMENT → TEST → REVIEW → FIX → VERIFY → REPORT
```

| Stage | Delegates to | Produces |
|---|---|---|
| DISCOVER | `analyzing-codebase` | Verified technical map of the affected area |
| PLAN | `planning-implementation` | Scoped, right-sized implementation plan |
| IMPLEMENT | `implementing-features` (+ `solution-architect`, `backend-engineer`, `frontend-engineer`, `database-engineer` agents as needed) | Working code, updated tests |
| TEST | `testing-with-playwright` and/or the project's existing unit/integration suite | Executed test results, not claims |
| REVIEW | `reviewing-code`, `auditing-security` (when the change touches auth/tenancy/data) | Classified findings (BLOCKER/HIGH/MEDIUM/LOW/NIT) |
| FIX | `implementing-features` / `debugging-systematically` | Findings addressed or explicitly deferred with reason |
| VERIFY | Re-run TEST and relevant REVIEW checks | Confirmation the fix didn't regress anything |
| REPORT | this skill | Summary of what shipped, what's deferred, what needs human sign-off |

Skip stages that don't apply (e.g. no Playwright config and no E2E-relevant change → skip TEST's Playwright leg, but still run existing unit tests). Never skip REVIEW for anything touching authorization, tenancy, payments, or migrations.

## Coordination rules

- **One area of the codebase, one active writer at a time.** Before parallelizing work across agents, partition by file/directory ownership so two agents never edit the same files concurrently. If genuine overlap is unavoidable, serialize those specific files.
- Each stage hands off a concrete artifact (a plan, a diff, a test result, a findings list) to the next — not a vague "looks good."
- Escalate to the user, don't silently proceed, when: the plan implies an irreversible action (see [references/evidence-and-safety.md](../../references/evidence-and-safety.md)), the discovered scope is much larger than the request implied, or REVIEW surfaces a BLOCKER.
- Use the agents in [agents/](../../agents/) for role-specific execution; use this skill's own reasoning for sequencing and conflict avoidance, not for doing the specialist work yourself.

## Decisions

- Small, single-file, single-discipline change → don't invoke the full pipeline; go straight to `implementing-features`.
- Change touches multi-tenant data, auth, or payments → REVIEW stage must include `auditing-security`, no exceptions.
- A stage fails (tests red, review finds a BLOCKER) → loop FIX→VERIFY before REPORT; don't report completion with known blockers outstanding.

## Exit criteria

- REPORT stage lists exactly what changed, what was verified (with evidence), what was deferred and why, and any action that still requires explicit human approval (deploy, merge, destructive migration).
