---
name: designing-user-experiences
description: Produces advisory UI/UX design handoffs for user-facing flows, responsive layouts, accessible interaction and existing design-system reuse. Use before implementation when material UX decisions remain open; not for implementing a settled design.
when_to_use: USE for new screens, interaction redesign, UX flows, responsive layouts, or unresolved accessibility and design-system decisions. NOT USE for a trivial styling fix with a settled design, backend-only work or implementing an already accepted handoff.
---

# Designing user experiences

Follow [the safety baseline](../enforcing-safety-baseline/SKILL.md). Advisory only; never write files, install packages or mutate the project.

## Workflow

1. Discover the target user, goal, route/surface, existing components, tokens and conventions. Read actual evidence; distinguish requested design from observed UI. Do not assume framework, visual state or design library.
2. Map the shortest usable journey, content hierarchy and component boundaries. Prefer reuse; explain necessary deviations.
3. Specify loading, empty, error, success and permission states where applicable. Define responsive behavior, keyboard/focus order, accessible names, contrast targets and reduced-motion behavior where relevant. Use testable criteria, not generic promises of compliance.
4. Identify API/data dependencies and material unresolved decisions. Do not invent endpoints or change contracts. A dependency that can alter implementation blocks freeze.
5. Return the [design handoff](../../references/orchestration-contracts.md) with evidence, scope and acceptance criteria. Handoff to frontend implementation; do not claim implementation or verified visual results.

## Decisions

- UI-only scope with no evidence of API/database changes: do not request backend/database work.
- Existing design system: reuse evidenced primitives and tokens; propose additions only when needed.
- No established design system: propose a minimal framework-neutral baseline; do not assert one exists.
- Missing browser/screenshot access: label visual review NOT RUN; provide testable design criteria instead.
- Unresolved material API/data or UX decision: explicitly mark blocker; no dependent mutation until resolved.
- Trivial style change with settled interaction: route to implementing-features without dedicated design stage.

## Exit criteria

A concrete handoff records user goal, surface, hierarchy, components, applicable states, responsive behavior, accessibility, reuse, acceptance criteria and unresolved decisions. Each material assertion is grounded in evidence or labeled proposal. No writes or unsupported implementation/visual claims.
