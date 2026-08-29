# ADR 0001: Marketplace architecture for v0.1.0

## Status

Accepted — 2026-08-29

## Context

`ai-dev-team-marketplace` is a new, public Claude Code plugin marketplace intended to package a reusable "AI software development team" (architecture, implementation, debugging, testing, security, review, release) as portable skills and agents that work across arbitrary stacks and project domains (SaaS, ERP, LegalTech, e-commerce, automotive, fitness, and stacks not yet known).

Two structural risks needed to be decided up front:

1. **Breadth vs. depth.** It would be easy to ship 40–100 shallow, near-duplicate skills covering every framework combination. That maximizes apparent coverage but produces skills that are hard to discover correctly (overlapping descriptions), expensive in aggregate context cost, and hard to maintain (any policy change has to be replicated everywhere).
2. **Stack coupling.** A marketplace meant to serve unknown future stacks cannot hardcode assumptions about any one framework, and must never encode details from any single private/vertical project (e.g. a specific client's domain model) into shared, public skill content.

## Decision

- **Multi-plugin marketplace, single plugin for v0.1.0.** `.claude-plugin/marketplace.json` is structured to hold multiple plugins from the start (`plugins: []`), but only registers one plugin, `ai-dev-team`, for this release. Future plugin families (see [roadmap](../../ROADMAP.md)) become additional marketplace entries, not additions bolted onto `ai-dev-team`.
- **Ten foundational skills, not fifty.** Each skill maps to one clearly-scoped responsibility in the software delivery lifecycle (continuity, orchestration, discovery, planning, implementation, debugging, E2E testing, review, security, release). Overlap between skills is resolved by delegation (`orchestrating-development-team` references the other nine by name) rather than by duplicating their content.
- **Skills are stack-detecting, not stack-specific.** No skill assumes Angular vs. React, NestJS vs. Laravel, Postgres vs. MySQL. Detection patterns live once in `references/stack-detection.md` and skills apply them, so the same skill set works unmodified across all target stacks listed in the project brief.
- **Progressive disclosure is mandatory, not optional.** `SKILL.md` files stay under ~250 lines and link to `references/` for shared reference material (stack detection, context-recovery strategy) instead of restating it. Rationale and mechanics are recorded in [../architecture/token-efficiency.md](../architecture/token-efficiency.md).
- **Specialized agents, not one mega-agent.** Ten subagents (`agents/*.md`) map to delivery roles (architect, frontend/backend/database engineer, QA, security reviewer, code reviewer, debugger, release manager, repository explorer) so orchestration can delegate role-scoped work with role-scoped tool access, instead of a single unrestricted agent doing everything. How these agents get the shared safety policy despite starting with an isolated context is its own decision — see [ADR 0002](0002-agent-safety-baseline.md).
- **Eval-driven from the start.** Each of the ten workflow skills ships with scenario-based evals under `tests/evals/`, validated by schema in CI, rather than relying only on manual testing before merge.
- **Security-by-default, autonomy-with-limits.** A shared safety/evidence policy — no unverified claims of success, explicit confirmation required before irreversible actions (force-push, hard reset, destructive migrations, production deploys, merges, secret rotation) — is linked by every skill and preloaded into every agent instead of being trusted to be remembered ad hoc. Originally shipped as a plain reference file linked from most skills; corrected in [ADR 0002](0002-agent-safety-baseline.md) once review found it didn't reach directly-invoked skills or agents.
- **No vendor lock-in beyond the Claude Code plugin format itself.** Skills follow the open Agent Skills `SKILL.md` standard where the frontmatter allows it; Claude-Code-specific extensions (`when_to_use`, `context: fork`, etc.) are used only where they add real value (e.g. none of the ten v0.1.0 skills currently require subagent forking).

## Consequences

- **Positive:** smaller surface to audit and keep correct; consistent behavior across all ten skills for safety/evidence; low aggregate token cost even as the plugin grows, because shared policy isn't duplicated; a clear, documented place (`docs/roadmap.md`, this ADR) for reviewers to evaluate what's deliberately deferred versus missing by oversight.
- **Negative / accepted trade-off:** ten skills necessarily leave gaps (no dedicated skill yet for, e.g., dependency-vulnerability scanning, accessibility testing, or infra-as-code) — deferred to v0.2+ rather than rushed into v0.1.0 at lower quality.
- **Follow-up:** any new skill proposed after v0.1.0 must justify why it isn't better served by extending an existing skill's `references/`, per [CONTRIBUTING.md](../../CONTRIBUTING.md), to keep the "few excellent skills" principle from eroding over time.
