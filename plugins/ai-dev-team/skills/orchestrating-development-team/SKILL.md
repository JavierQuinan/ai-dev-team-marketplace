---
name: orchestrating-development-team
description: Acts as tech lead for multi-part software delivery, coordinating architecture, frontend, backend, database, QA, security, DevOps, review and release work through the plugin's specialized agents and skills. Use for requests spanning multiple disciplines or an end-to-end delivery ("build this feature and ship it", "act as the full dev team").
when_to_use: Use when a request needs more than one discipline (e.g. backend + frontend + tests) or explicitly asks for full-team/end-to-end delivery. For a single-discipline task, invoke the specific skill directly instead.
---

# Orchestrating the development team

Coordinate the plugin's skills and agents (see [agents/](../../agents/)) through a fixed pipeline so multi-part work stays coherent, verifiable, and free of conflicting concurrent edits. This skill is the router for cross-cutting requests — it delegates depth to the other skills rather than duplicating their instructions. This skill itself follows [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md).

## Pipeline

```
DISCOVER → PLAN → IMPLEMENT → TEST → REVIEW → FIX → VERIFY → REPORT
```

| Stage | Delegates to | Produces |
|---|---|---|
| DISCOVER | `analyzing-codebase` skill, optionally the `ai-dev-team:repository-explorer` agent for a large/unfamiliar tree | Verified technical map of the affected area |
| PLAN | `planning-implementation` skill, optionally the `ai-dev-team:solution-architect` agent for a genuine design decision | Scoped, right-sized implementation plan |
| IMPLEMENT | `implementing-features` skill, delegating file-scoped work to `ai-dev-team:frontend-engineer`, `ai-dev-team:backend-engineer`, `ai-dev-team:database-engineer` as needed | Working code, updated tests |
| TEST | `testing-with-playwright` skill and/or the project's existing unit/integration suite, optionally via `ai-dev-team:qa-engineer` | Executed test results, not claims |
| REVIEW | `reviewing-code` skill (`ai-dev-team:code-reviewer` agent), `auditing-security` skill (`ai-dev-team:security-reviewer` agent) when the change touches auth/tenancy/data | Classified findings (BLOCKER/HIGH/MEDIUM/LOW/NIT) |
| FIX | `implementing-features` / `debugging-systematically` skill, optionally `ai-dev-team:debugger` | Findings addressed or explicitly deferred with reason |
| VERIFY | Re-run TEST and relevant REVIEW checks | Confirmation the fix didn't regress anything |
| REPORT | this skill, optionally `ai-dev-team:release-manager` when the request is release-scoped | Summary of what shipped, what's deferred, what needs human sign-off |

Skip stages that don't apply (e.g. no Playwright config and no E2E-relevant change → skip TEST's Playwright leg, but still run existing unit tests). Never skip REVIEW for anything touching authorization, tenancy, payments, or migrations.

## Delegating to agents

Use the `ai-dev-team:<agent-name>` scoped identifier (e.g. `ai-dev-team:backend-engineer`) when delegating through the Agent tool, not the bare name. Plugin agents are namespaced by their plugin, and another installed plugin — or a project/user-level agent — can define an agent with the same bare name; the scoped identifier is what disambiguates which one actually runs. This matters most when this skill is asked to "act as the full dev team": that request only becomes real DISCOVER→...→REPORT execution if delegation actually invokes `ai-dev-team:*` agents through the Agent tool, not just names them in prose.

Don't force a subagent for a step that's cheap to do inline. A subagent starts with a fresh, isolated context window (it doesn't see this conversation), so spawning one for a one-file, low-risk step costs more in latency and re-established context than doing it directly. Reserve agent delegation for steps where the role-scoped tool restriction, a large/verbose sub-task, or genuine parallelism actually pays for that cost.

## Coordination rules

- **One area of the codebase, one active writer at a time.** Before parallelizing work across agents, partition by file/directory ownership so two agents never edit the same files concurrently. If genuine overlap is unavoidable, serialize those specific files.
- Each stage hands off a concrete artifact (a plan, a diff, a test result, a findings list) to the next — not a vague "looks good."
- Escalate to the user, don't silently proceed, when: the plan implies an irreversible action (see [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md)), the discovered scope is much larger than the request implied, or REVIEW surfaces a BLOCKER.
- Use the agents in [agents/](../../agents/) for role-specific execution; use this skill's own reasoning for sequencing and conflict avoidance, not for doing the specialist work yourself.

## Decisions

- Small, single-file, single-discipline change → don't invoke the full pipeline; go straight to `implementing-features`.
- Change touches multi-tenant data, auth, or payments → REVIEW stage must include `auditing-security`, no exceptions.
- A stage fails (tests red, review finds a BLOCKER) → loop FIX→VERIFY before REPORT; don't report completion with known blockers outstanding.

## Exit criteria

- REPORT stage lists exactly what changed, what was verified (with evidence), what was deferred and why, and any action that still requires explicit human approval (deploy, merge, destructive migration).
