# Orchestration delegation budget

Deep detail for `orchestrating-development-team`'s agent-budget and coordination model, loaded only when actually running a multi-part delivery. The principle in one line: **a subagent starts with a fresh, isolated context window and therefore has a real, non-zero cost — spawn one because a specific task needs it, never because the plugin happens to have ten roles.**

## Inline-first

Default to doing a step directly (as this skill's own reasoning, or a workflow skill invoked in place) rather than delegating to a subagent. Spawn a subagent only when at least one of these actually holds:

- role-specific tool restriction is genuinely useful (e.g. a read-only reviewer shouldn't share context with a writer);
- the task is materially large or verbose enough that isolating it keeps the main thread's context clean;
- ownership can be isolated cleanly (a self-contained area of the codebase);
- real parallel execution provides a real benefit (independent areas, no ordering dependency);
- specialist independent review is itself the point (a second, uncontaminated read on the same change).

None of these are "the plugin has a `frontend-engineer` agent, so frontend work should use it." A one-file CSS tweak stays inline even in a full-team run.

## Task size bands

A practical budget, not a hard technical ceiling — used to catch the common failure mode (launching many agents for a small task) and to justify the uncommon case (launching several for a genuinely large one).

| Band | Shape | Normal agent count |
|---|---|---|
| **Tiny** | One file, one obvious change, one discipline | 0 |
| **Small** | A few files, one primary discipline, limited tests | 0–1 |
| **Medium** | Multiple related components, 2–3 disciplines, clear ownership boundaries | 1–3 |
| **Large / cross-cutting** | Multiple modules — DB + backend + frontend + QA/security, release concerns | 3–6 |
| **Exceptional** | Only when concrete evidence shows a real need beyond Large | State why in the plan/report |

A band is about the actual evidenced shape of the work, not the user's framing — "actúa como el equipo completo" on a one-line copy change is still Tiny once DISCOVER confirms it, and the orchestrator says so explicitly (right-sized, not silently doing less than "full team" implied).

## No token-count claims

Never state an exact token count ("this used 12,483 tokens") unless the runtime actually exposes that number in this session — that's a fabricated-precision claim, exactly what `enforcing-safety-baseline`'s evidence rule forbids. The budget model here is about *agent count and context duplication*, which is directly observable from what was actually launched, not about token arithmetic that isn't.

## No duplicate discovery

DISCOVER produces one concise, reusable map (stack, architecture, relevant files, existing conventions). Delegated agents receive that map plus their own scoped packet — they do not each re-run a full-repo `analyzing-codebase`-equivalent pass. A transcript showing `repository-explorer`, `backend-engineer`, `database-engineer`, and `qa-engineer` each independently mapping the entire repository is the failure mode this rule exists to prevent.

The one legitimate exception: a read-only independent reviewer (code review, security review) re-inspecting the *affected area* is fine and often valuable — independence is the point there. Even then, scope it to the affected area, not the whole repository.

## One executor per stage

Each specialist stage (REVIEW's security leg, REVIEW's code-review leg, TEST authoring, ARCHITECT) gets exactly one primary executor — either the relevant workflow skill run inline, or a delegated `ai-dev-team:<agent>` subagent that itself invokes that skill — never both by default. Deciding INLINE vs. DELEGATED is part of the same budget call as Task size bands above; once decided, execute the stage once and consume its artifact rather than re-running an equivalent pass a second way.

Concretely: if `auditing-security` runs inline, don't also delegate to `ai-dev-team:security-reviewer` over the same change; if `ai-dev-team:security-reviewer` is delegated, don't also run `auditing-security` inline over the same files. The same holds for `reviewing-code`/`code-reviewer`, `writing-automated-tests`/`testing-with-playwright` authorship, and `reviewing-architecture`/`solution-architect` — pick one executor per stage, not both.

**Exception — a genuine second, independent review.** Running both is justified only with a specific, evidenced reason for two independent passes (e.g. a high-risk auth/payment change where the request or the assessed risk explicitly warrants a second independent set of eyes) — and the report must state why the second review earned its cost, never run it silently by default.

**Cross-checking a delegated agent's findings is not duplication.** After a delegated reviewer returns findings, the orchestrator may — and should — read the cited file/line, confirm the finding, apply and verify a fix, and re-run relevant tests; that's ordinary FIX→VERIFY, not a second review. It should not re-run the same specialist's full workflow over the same files from scratch just because its own findings are being checked.

**Waiting on a delegated agent is not an opening to do its stage a second way.** A background agent takes real time; the instinct to stay useful while it runs is correct, but "meanwhile, let me also do a quick review myself" over the *same* affected files is the exact duplication this section forbids, even when it's framed as a lighter or different-sounding pass ("a quick consistency check," "just verifying while I wait") — if what actually gets invoked is that stage's own workflow skill (e.g. `auditing-security`) over the same files, it's a second executor for the same stage, full stop, regardless of the framing. While a delegated agent for a stage is in flight, spend the wait on something else entirely (an unrelated stage, idle wait, nothing) — never on that same stage.

**Concrete mechanism — delegate the primary specialist synchronously.** When the Agent tool is delegating the primary executor for a stage, pass `run_in_background: false` so the call blocks until the specialist's result returns, instead of leaving a background window open. This removes the opening the anti-pattern above depends on — there's no wait to fill with a redundant inline pass, because the next turn already has the delegate's result. Reserve `run_in_background: true` (the default) for genuinely independent, unrelated work that doesn't tempt a same-stage duplicate — not for a stage's sole specialist.

**This is a best-effort policy, not a guaranteed property.** One executor per stage is the intended behavior and should be followed, but it depends on the orchestrator's own judgment in the moment, not a mechanism this plugin can enforce outside of the `run_in_background: false` mitigation above. If a duplicate read-only specialist pass is observed anyway (the delegate plus an inline pass over the same files, with no stated reason), report it plainly as a budget/efficiency deviation in REPORT — it is not by itself a correctness or safety failure. It becomes one only if it also produces a concrete defect: conflicting writes, scope expansion nobody approved, fabricated/inflated evidence from treating the duplicate pass as extra assurance it doesn't actually provide, or a similar real consequence. Two independent read-only reviews finding the same thing is wasteful, not unsafe — say so honestly rather than either hiding the duplication or overstating it as a violation on its own.

*Verification note:* the `run_in_background: false` mitigation was runtime-verified (issue #7) across two independent fresh-process trials with genuine `ai-dev-team:security-reviewer` delegation — both correctly set the flag on their own and both showed zero duplicate inline pass; the delegate's own internal use of `auditing-security` (visible inline only because the call is synchronous) is the delegate doing its job, not a second executor. Earlier reports of duplication were all observed *before* this mechanism existed in the orchestrator's guidance, when the delegating call had no `run_in_background` value at all (defaulting to backgrounded) — that is the scenario this mitigation targets, and it held in every trial tested. This remains best-effort, not a hard guarantee, because nothing prevents a future run from omitting the flag or choosing to duplicate anyway — but it is no longer an untested claim.

## Task packets

Every delegated agent gets a short, concrete packet instead of the full conversation or the full repository pasted in:

```
GOAL: <one sentence — what this agent must produce>
SCOPE: <what's in, what's explicitly out>
OWNED AREA: <files/directories this agent may write>
VERIFIED CONTEXT: <the specific facts from DISCOVER/PLAN this agent needs, not everything found>
CONSTRAINTS: <conventions, safety limits, things not to touch>
EXPECTED ARTIFACT: <what "done" looks like for this delegation>
STOP CONDITIONS: <when to stop and report back rather than proceed>
```

Link or name exact files for the agent to read itself rather than pasting their contents. Never paste the entire conversation history or a large fraction of the repository into a delegation packet — that defeats the isolated-context model and is exactly the token cost this budget exists to control.

Use these exact headings verbatim in the delegation prompt rather than covering the same ground in unlabeled prose — they're cheap, deterministic, and let a packet be audited straight from the transcript (a real, scoped packet looks different at a glance from a full-context dump). Keep each field short; a one-line `OWNED AREA: none (read-only review)` is enough when there's nothing to write.

## One writer per area, ownership ledger

Before any parallel work, partition by file/directory ownership so two agents never write the same files concurrently. Keep this as a lightweight, conceptual ledger in the plan/report — not a new persisted state file:

```
AREA                    OWNER               MODE
src/api/*               backend-engineer    WRITE
supabase/migrations/*   database-engineer   WRITE
tests/e2e/*             qa-engineer         WRITE
(affected area)         security-reviewer   READ
(affected area)         code-reviewer       READ
```

Read-only reviewers may overlap freely with each other and with the area a writer owns — the constraint is on concurrent *writers*, not readers. If genuine write overlap is unavoidable (two roles both need to touch the same file), serialize those specific files rather than parallelizing them.

Never run in parallel:
- an architecture decision and the implementation that depends on its outcome;
- a migration's schema design and backend implementation that needs the final schema;
- two agents with write access to the same file or module boundary.

Prefer parallel *read-only* reviews (code review + security review running independently) over any concurrent writers.

## Stage policies

- **Review**: `reviewing-code` for anything non-trivial, multi-file, touching a public/API contract, auth/security/data handling, a migration, or release-scoped. The security leg — `auditing-security` run inline, or `ai-dev-team:security-reviewer` delegated (never both, see One executor per stage) — is *mandatory*, not optional, when the change touches auth, authorization, tenant isolation, RLS, payments, secrets, dependency/supply-chain surface, CI security, or other sensitive data — never skip it because the request only said "implement." Don't run a security review mechanically on a pure copy/text change with no such surface.
- **Test**: unit/integration work is `writing-automated-tests`; E2E/browser work is `testing-with-playwright`; running the project's *existing* test suite happens regardless of either, as part of verification — writing new tests and running existing ones are not the same step and a full delivery usually needs both.
- **Database**: any schema/migration/RLS work goes through `managing-database-migrations`, never generic `implementing-features` — ADR 0005's five safety levels stay authoritative regardless of how the orchestrator phrases the request, and "full team" framing never overrides them.
- **Architecture**: `reviewing-architecture` only for a genuine structural/design decision with a real fork in approach — not ceremony for every feature. A specific, already-decided change is `planning-implementation`'s job.
- **Release/Deploy**: a release-scoped request runs `preparing-releases` for the readiness verdict; only once readiness allows it does `planning-deployment` produce the deployment plan. The report may say "ready for human deployment" — it must never say "deployed" without actual external evidence, and `planning-deployment` itself never executes the deploy regardless of how the readiness verdict came out.
