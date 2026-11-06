# Orchestration artifact contracts

These contracts define the minimum material handoff between stages. They are semantic contracts, not rigid serialization schemas: equivalent wording is valid when it carries the same information.

## Design handoff

Required when implementation depends on a user-facing design decision.

- user goal and affected route/surface;
- information hierarchy and component boundaries;
- loading, empty, error and success states where applicable;
- responsive behavior and accessibility requirements;
- existing design-system primitives to reuse, when repository evidence identifies them;
- affected area and acceptance criteria;
- unresolved decisions that block implementation.

A design handoff must not invent a framework, component library or design system that repository evidence does not establish.

## Implementation contract

Required before partitioning dependent implementation across writers.

- objective and bounded scope;
- stable upstream decisions the implementation consumes (design/API/data/architecture as applicable);
- dependencies and ordering constraints;
- ownership ledger: area, owner, READ/WRITE mode;
- expected artifact/output;
- constraints and stop conditions.

A contract is not frozen while a dependency that changes downstream interfaces remains unresolved. Parallel writers may start only after the shared decisions they consume are stable and their WRITE areas are disjoint.

## Agent output

A delegated specialist returns:

- work performed and artifact produced;
- evidence used;
- files/areas read and, for writers, changed;
- tests/checks actually executed and their observed result;
- unresolved items or blockers;
- downstream assumptions;
- explicit non-actions when safety/scope boundaries prevented an action.

Never convert an unexecuted check into a PASS claim.

## Review findings

Each actionable finding identifies:

- severity;
- concrete evidence and affected area;
- reproducibility/trigger when relevant;
- required or optional disposition;
- responsible owner/stage;
- verification needed after a fix.

A vague concern without evidence is not a BLOCKER. An evidenced BLOCKER cannot disappear from REPORT without a fix+verification result or an explicit justified deferral.

## Completion handoff

REPORT records:

- final diff/commit identity when available;
- stages/agents actually used and why they were justified;
- validation actually executed, with observed results;
- findings fixed, deferred or unresolved;
- ownership/concurrency deviations, including duplicate-stage deviations;
- safety gates and human actions still pending (merge, deploy, destructive operation).

A plan is not execution, a deployment plan is not a deployment, and a static eval definition is not runtime proof.

## Dependency-aware concurrency

Default to synchronous execution when stage B consumes a decision or artifact from stage A.

Parallel execution is allowed only when:
1. shared upstream contracts are stable;
2. active WRITE ownership is disjoint;
3. neither task can invalidate the other's assumptions;
4. each parallel task has a complete task packet.

Examples:
- frontend and backend may run in parallel after their shared API/design contract is stable and file ownership is disjoint;
- architecture may not race implementation that depends on the architecture decision;
- migration/schema design may not race backend implementation that requires the final schema;
- independent read-only reviews may overlap.

Delegating a stage's sole specialist remains synchronous (`run_in_background: false`) unless genuine independent parallel work is explicitly justified. Parallelism is an optimization earned by independence, not the default.
