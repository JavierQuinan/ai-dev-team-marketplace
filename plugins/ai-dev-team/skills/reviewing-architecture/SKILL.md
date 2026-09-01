---
name: reviewing-architecture
description: Reviews system/module architecture, module boundaries, dependency direction, and technical debt/scalability risk, and drafts ADRs — for existing systems or a proposed design. Advisory only; never implements or refactors. Use when asked to review architecture, draft an ADR, analyze technical debt, or decide how to modularize something.
when_to_use: USE for architecture review, module-boundary analysis, dependency-direction findings, technical-debt/scalability decisions, or ADR drafting — "genera un ADR para esta decisión", "revisa la arquitectura de este módulo", "analiza deuda técnica aquí", "esto va a escalar si...", "cómo deberíamos modularizar X". NOT USE for a specific implementation plan with no genuine architectural fork (stays with `planning-implementation`), a diff-level correctness/security review (stays with `reviewing-code`), or a request to just understand what exists with no decision or review being asked (stays with `analyzing-codebase`).
---

# Reviewing architecture

Advisory and analysis only — this skill never edits or writes code, never runs a refactor, and never persists a file itself. See [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md).

## Workflow

1. **Discover the real structure.** Read modules/packages, dependency-graph evidence, public interfaces, data flow, integration points, deployment shape, existing ADRs, and the layering the repo already establishes. Never propose Clean Architecture, DDD, hexagonal, microservices, or any other pattern just because it's popular — only because the evidence in this repo actually calls for it.
2. **Define the actual question.** Separate a genuine architecture decision from an implementation detail or a style preference. If there's no real architectural fork here, say so and don't inflate the task — route back to `planning-implementation` instead.
3. **Identify constraints**: existing contracts, deployment model, data ownership, evidenced team boundaries, compatibility requirements, multi-tenancy, security, performance, operational limits.
4. **Find options.** For a genuine decision, present a small number of viable options — not an exhaustive list.
5. **State trade-offs** per material option: complexity, coupling, operability, migration cost, failure modes, scalability, security, reversibility.
6. **Recommend one option** and explain why it fits *this* repo specifically. Never end on "it depends" when a call is asked for.
7. **Review for evidence-based findings**: circular dependencies, wrong dependency direction, duplicated domain ownership, cross-module data access, shared mutable state, unbounded coupling, single points of failure, a sync call where an async boundary is actually needed, contract/versioning risk, tenant-boundary confusion, a concrete scaling bottleneck. Never fabricate a finding to make the review look thorough — a genuinely healthy area gets no manufactured complaint.
8. **Draft an ADR when asked**, matching the target repo's own existing ADR convention if it has one — don't impose this marketplace's format on a different repo. Minimum structure: Status, Context, Decision, Consequences; add Alternatives considered / Risks / Follow-up only when they add real value. State the content and, if inferable, the target path/number — this skill does not write the file itself (see below).
9. **Hand off, never implement.** Once a decision is accepted, `planning-implementation` → `implementing-features` (or the relevant engineer role) carries it out. This skill's job ends at the recommendation or the drafted ADR content.

## Boundaries

- **vs. `planning-implementation`** — that skill answers *how*: files, ordered steps, for a specific already-decided change. This skill answers *why*: the architectural decision or structural review underneath a class of changes.
- **vs. `reviewing-code`** — that skill finds diff-level correctness/security/regression findings. This skill finds system/module-level, long-lived design consequences — composable with, not a replacement for, a code review.
- **vs. `analyzing-codebase`** — that skill maps what exists. This skill judges whether the architecture is sound and what decision should follow.

## Decisions

- The request is really about a specific, already-decided change with no design fork → redirect to `planning-implementation`, don't run a full architecture review for it.
- The codebase is genuinely healthy → say so; don't manufacture a modularization or refactor recommendation to appear thorough.
- The user asks for an ADR to be saved/written to disk → provide the drafted content and the inferred path/number; hand it to the orchestrator or the appropriate implementation role to actually persist once the decision is accepted — this skill does not call `Write`/`Edit` itself.
- The target repo already has its own ADR format/numbering → follow it exactly rather than imposing this marketplace's structure.
- A small monolith is working fine → don't recommend microservices, a message queue, or another distributed-systems pattern without a concrete, evidenced bottleneck driving it.

## Exit criteria

- Every architecture finding cites the concrete evidence (file/module/dependency) that produced it — no unverified speculation presented as fact.
- A recommendation, when one is asked for, picks an option and states why — never left at "it depends."
- No refactor, edit, or file write was performed by this skill.
- An ADR draft, when produced, matches the target repo's existing convention or explicitly notes none was found.
