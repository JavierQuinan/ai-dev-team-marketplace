---
name: orchestrating-development-team
description: Acts as tech lead for multi-part software delivery, coordinating architecture, frontend, backend, database, QA, security, release, and deployment-planning work through the plugin's specialized agents and skills. Invoke this skill FIRST, before any other reasoning about task size, whenever the user explicitly asks for full-team/whole-team delivery — "actúa como el equipo completo", "actúa como mi equipo de desarrollo", "act as the full dev team", "use the full development team", "orquesta el equipo", "trabaja como arquitecto + frontend + backend + QA" — even if the described task looks small; the skill itself decides, once loaded, whether to right-size or skip parts of the pipeline. Also use for requests spanning multiple disciplines or an end-to-end delivery ("build this feature and ship it").
when_to_use: An explicit full-team/whole-team request in any phrasing is always a trigger for this skill, regardless of how small the underlying task appears — do not let apparent task size override an explicit full-team request; that right-sizing happens inside the skill after it loads, not as a reason to skip loading it. Also use when a request needs more than one discipline (e.g. backend + frontend + tests). For a single-discipline task with no full-team language, invoke the specific skill directly instead.
---

# Orchestrating the development team

Coordinate the plugin's skills and agents (see [agents/](../../agents/)) through a fixed pipeline so multi-part work stays coherent, verifiable, and free of conflicting concurrent edits. This skill is the router for cross-cutting requests — it delegates depth to the other skills rather than duplicating their instructions. This skill itself follows [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md).

**Routing vs. execution — do not conflate the two.** Whether to *invoke* this skill is a routing decision: an explicit full-team request always invokes it, full stop, regardless of task size. Whether to *right-size* the pipeline once invoked (e.g. skip straight to `implementing-features` for a genuinely small change) is an internal execution decision this skill makes for itself, after it has already loaded — never a reason for the top-level router to skip loading it in the first place.

## Pipeline

```
DISCOVER → ARCHITECT → PLAN → IMPLEMENT → DATABASE → TEST → REVIEW → FIX → VERIFY → RELEASE → DEPLOY-PLAN → REPORT
```

Every stage is conditional on evidence — never run mechanically. See `references/orchestration-budget.md` for the stage policies (when REVIEW's security leg is mandatory, the test/database/architecture/release-deploy boundaries) referenced below.

| Stage | Delegates to | Produces | Runs when |
|---|---|---|---|
| DISCOVER | `analyzing-codebase`, optionally `ai-dev-team:repository-explorer` for a large/unfamiliar tree | Verified technical map | Always, right-sized to scope |
| ARCHITECT | `reviewing-architecture` (`ai-dev-team:solution-architect`) | Decision/ADR | Only a genuine structural design fork exists |
| PLAN | `planning-implementation`, optionally `ai-dev-team:solution-architect` | Scoped implementation plan | Non-trivial change |
| IMPLEMENT | `implementing-features`, delegating file-scoped work to `ai-dev-team:frontend-engineer`/`backend-engineer`/`database-engineer` | Working code, updated tests | Always for a build/change request |
| DATABASE | `managing-database-migrations` (`ai-dev-team:database-engineer`) | Safe migration, ADR 0005 safety-level classification | Schema/migration/RLS involved |
| TEST | `writing-automated-tests` (unit/integration) and/or `testing-with-playwright` (E2E), via `ai-dev-team:qa-engineer`; existing suite still run regardless | Executed results, not claims | Always some verification; both legs only when both apply |
| REVIEW | `reviewing-code` (`ai-dev-team:code-reviewer`), `auditing-security` (`ai-dev-team:security-reviewer`) when risk conditions require it | Classified findings (BLOCKER/HIGH/MEDIUM/LOW/NIT) | Non-trivial change; security leg is mandatory for auth/tenancy/payments/secrets/supply-chain, never optional there |
| FIX | `implementing-features`/`debugging-systematically`, optionally `ai-dev-team:debugger` | Findings addressed or explicitly deferred with reason | A REVIEW/TEST finding needs resolving |
| VERIFY | Re-run TEST and relevant REVIEW checks | Confirmation the fix didn't regress anything | After any FIX |
| RELEASE | `preparing-releases` (`ai-dev-team:release-manager`) | GO / CONDITIONAL GO / NO-GO | Request is release-scoped |
| DEPLOY-PLAN | `planning-deployment` (`ai-dev-team:release-manager`) | Deployment plan — never an executed deploy | Deploy/rollout/rollback planning was requested, and only once RELEASE readiness allows it |
| REPORT | this skill | What shipped, what's deferred, what needs human sign-off | Always, last |

Skip stages that don't apply. Never skip REVIEW's security leg for anything touching authorization, tenancy, payments, secrets, or supply-chain surface.

## Role coverage matrix (10 agents, 0 new)

| Agent | Primary skill | Secondary |
|---|---|---|
| `repository-explorer` | `analyzing-codebase` | — |
| `solution-architect` | `reviewing-architecture` | `planning-implementation` |
| `frontend-engineer` | `implementing-features` | — |
| `backend-engineer` | `implementing-features` | — |
| `database-engineer` | `managing-database-migrations` | `implementing-features` (generic DB-adjacent work with no schema/migration/RLS) |
| `qa-engineer` | `writing-automated-tests` | `testing-with-playwright` |
| `security-reviewer` | `auditing-security` | — |
| `code-reviewer` | `reviewing-code` | — |
| `debugger` | `debugging-systematically` | — |
| `release-manager` | `preparing-releases` | `planning-deployment` |

## Delegating to agents — budget, not fanout

Use the `ai-dev-team:<agent-name>` scoped identifier when delegating through the Agent tool, not the bare name — plugin agents are namespaced, and the scoped identifier is what disambiguates which one actually runs when another installed plugin or a project/user-level agent shares the bare name.

**"Full team" never means "launch all 10 agents."** Default to doing a step inline; spawn a subagent only when it earns its isolated-context cost (see `references/orchestration-budget.md` for the full model: task size bands from Tiny (0 agents) to Large (3–6), the inline-first principle, task packets, no-duplicate-discovery, one-executor-per-stage, and the one-writer-per-area ownership ledger). A ten-agent fanout for a small task is the failure mode this budget exists to prevent, not a sign of thoroughness. **A stage should run once, either inline or delegated, not both** — delegating `ai-dev-team:security-reviewer` and also running `auditing-security` inline over the same change is duplicated work, not extra safety; see `references/orchestration-budget.md#one-executor-per-stage` for the narrow exception, the `run_in_background: false` mitigation, why cross-checking a delegate's specific findings doesn't count as a second review, and the honest limits of what this can actually guarantee versus what must be disclosed when it doesn't hold.

## Full autonomous team contract

When the user says "actúa como el equipo completo" / "hazlo todo" / "full dev team" / "ejecuta todo el QA" / "orquesta todo", proceed autonomously through the relevant *reversible, repo-local* stages without asking for redundant approval between them (discover → plan → implement → tests → review → fix → verify may run in one continuous pass). Autonomy stops at the same safety boundaries as everywhere else — "full autonomous team" does not mean "ignore the safety baseline":

- production deploy — `planning-deployment` never executes one, regardless of confirmation;
- merge/close a PR;
- destructive git operations;
- real secret operations;
- a destructive/high-blast-radius DB operation — always confirmed, per ADR 0005's LEVEL 5, even in a full-team run;
- a shared/staging/production DB apply — never performed by `managing-database-migrations` itself.

## Coordination rules

- **One area of the codebase, one active writer at a time.** Partition by file/directory ownership before parallelizing; serialize specific files if genuine overlap is unavoidable. Never parallelize an architecture decision with implementation that depends on it, or a migration's design with backend work that needs the final schema.
- Each stage hands off a concrete artifact (a plan, a diff, a test result, a findings list) to the next — not a vague "looks good."
- Escalate to the user, don't silently proceed, when: the plan implies an irreversible action (see [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md)), the discovered scope is much larger than the request implied, or *fixing* a REVIEW/TEST finding would itself require one of the safety gates below. **A REVIEW BLOCKER by itself is not an escalation trigger** — a reversible, in-scope BLOCKER (a missing authorization check, a validation gap, a regression, a failing test) loops FIX→VERIFY autonomously instead, per Decisions below; only the *fix* needing an irreversible action, a destructive DB operation, a new dependency, or similar turns it into one.
- Use the agents in [agents/](../../agents/) for role-specific execution; use this skill's own reasoning for sequencing, budgeting, and conflict avoidance, not for doing the specialist work yourself.

## Decisions

- No explicit full-team request, and the change is small/single-file/single-discipline → don't invoke this skill at all; go straight to `implementing-features`. This is a routing decision made *before* loading this skill.
- Explicit full-team request, but once loaded the change turns out to be small/single-file/single-discipline → this skill stays invoked (routing already happened), but internally right-sizes: a lightweight DISCOVER→PLAN, 0 specialist agents normally, no architecture/security/release ceremony for a one-line change — and it says explicitly that the pipeline was right-sized rather than silently doing less than "full team" implied.
- Change touches multi-tenant data, auth, tenancy, or payments → the REVIEW stage's security leg is mandatory, no exceptions — satisfied by running `auditing-security` inline **or** by delegating `ai-dev-team:security-reviewer` (which itself runs `auditing-security`), never by both. "Mandatory" describes the stage, not a requirement to invoke the `auditing-security` skill name specifically in addition to whichever executor already covers it.
- Change touches schema/migration/RLS → DATABASE stage uses `managing-database-migrations`, never generic `implementing-features`; ADR 0005 stays authoritative regardless of "full team" framing.
- A stage fails (tests red, review finds a BLOCKER) and the fix is reversible and stays within the request's scope (an auth-check bug, a validation gap, a regression, a failing test) → loop FIX→VERIFY autonomously before REPORT, no redundant confirmation — the user already authorized this by saying "full team"/"hazlo todo"; don't report completion with known blockers outstanding.
- The *fix* for a BLOCKER would itself require an irreversible action, a destructive/high-blast-radius DB operation, a shared/staging/production DB apply, an actual production deployment, a real secret operation, a new dependency, material scope expansion, or an unresolved architectural decision → that's when a BLOCKER escalates — stop and ask, don't autonomously loop past one of these gates.
- Request is release-scoped and asks to "ship"/"deploy" → RELEASE (`preparing-releases`) first; DEPLOY-PLAN (`planning-deployment`) only if readiness allows, and it produces a plan, never an executed deployment — the report says "ready for human deployment," never "deployed," without actual external evidence.
- About to delegate to a specialist agent → check the budget model first (`references/orchestration-budget.md`): does this specific step actually need isolated context/tool restriction/real parallelism, or would inline work do it as well for less cost?
- A specialist agent was delegated for a stage (e.g. `ai-dev-team:security-reviewer`) → don't also run that stage's workflow skill inline over the same change as a default "just to be safe" second pass; reading the delegate's cited findings and verifying/fixing them is fine, re-running the whole stage a second way isn't, unless a specific evidenced reason for a genuine second independent review is stated in the report.
- A delegated agent is still running and there's a wait before its result → don't fill that wait by invoking the same stage's skill inline over the same files "meanwhile" — that's the duplication above wearing a different name (a "quick check while I wait" that actually calls `auditing-security`/`reviewing-code` etc. over the affected files is still a second executor for that stage). Spend the wait on something else, or just wait.
- Delegating a specialist as a stage's sole primary executor → invoke the Agent tool with `run_in_background: false` for that call, so it blocks until the result returns instead of leaving a background window that then invites the "meanwhile" duplicate above. This is a mitigation, not a guarantee — see `references/orchestration-budget.md`'s one-executor-per-stage section for the honest limits of what this can actually enforce.

## Exit criteria

- REPORT stage lists exactly what changed, what was verified (with evidence), what was deferred and why, and any action that still requires explicit human approval (deploy, merge, destructive migration).
- Every agent actually launched is justified by the budget model, not launched merely because the role exists — the report names, for a multi-agent run, why each agent was needed.
- No two agents held write access to the same file/area concurrently.
- A primary executor was identified for each specialist stage before delegating (see `references/orchestration-budget.md`); if a duplicate read-only specialist pass happened anyway, REPORT discloses it plainly as a budget/efficiency deviation rather than hiding it or presenting the duplicate pass as extra assurance it doesn't actually provide — cross-checking a delegate's cited findings is not a duplicate run and needs no disclosure. No duplicate *mutation* and no writer overlap ever occurred, regardless.
- No claim of "deployed" or "in production" appears without actual external evidence of it — a deployment plan is not a deployment.
