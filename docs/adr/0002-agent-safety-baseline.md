# ADR 0002: Agent safety baseline via skill preload

## Status

Accepted — 2026-08-29 (hardening pass on v0.1.0, pre-merge)

## Context

Pre-merge review of PR #1 (owner architectural review, corroborated by two Codex review threads) found that `docs/architecture/token-efficiency.md` asserted subagents could rely on safety/evidence discipline being "already active" because a parent skill had loaded it. That assumption is incorrect. Per the official subagent documentation, a Claude Code subagent starts with a fresh, isolated context window: it does not see the parent conversation's history, the skills the parent has invoked, or the files the parent has read. Its initial context consists only of the delegation message it's given, its own system prompt, and the full content of any skill named in its own frontmatter `skills` field.

Consequently, none of the ten `ai-dev-team` agents (`agents/*.md`) carried any safety/evidence discipline when invoked directly — by name, by `@agent-ai-dev-team:<name>`, or by any caller other than `orchestrating-development-team` specifically walking through the pipeline. The same review also found three of the ten workflow skills (`analyzing-codebase`, `debugging-systematically`, `reviewing-code`) didn't link the safety policy at all, so direct invocation of those skills had the same gap on the skill side.

A related question: how should the ten role-specific workflow skills (`implementing-features`, `testing-with-playwright`, etc.) reach the agents that map to them (e.g. `backend-engineer` → `implementing-features`), without recreating the "mega-context on every call" problem — full-preloading a 30–50 line workflow skill into every single invocation of its agent, trivial or not.

## Decision

- **The evidence/safety policy became a skill, not a reference file.** `plugins/ai-dev-team/references/evidence-and-safety.md` was deleted and its content moved to `plugins/ai-dev-team/skills/enforcing-safety-baseline/SKILL.md`, because only a skill can be named in an agent's `skills:` preload list — a `references/*.md` file cannot. The new skill sets `user-invocable: false` (it's infrastructure, not a command a person would type) but stays model-invocable (no `disable-model-invocation`), because Claude Code refuses to preload a skill that disables model invocation.
- **Every agent preloads it.** All ten `agents/*.md` files gained `skills: [enforcing-safety-baseline]` in frontmatter, guaranteeing the full policy text is present at agent startup regardless of how the agent was reached.
- **All ten workflow skills link it, not just seven.** `analyzing-codebase`, `debugging-systematically`, and `reviewing-code` gained the link that seven of their siblings already had.
- **The mapped workflow skill is available on demand, not preloaded.** Each agent's `tools` list gained `Skill`, and its system prompt names the one workflow skill most relevant to its role. The agent pulls that skill's full content in via the Skill tool only when the task is non-trivial enough to warrant it, rather than paying that cost on every invocation. This keeps the guaranteed, unconditional preload small (the safety baseline is a few dozen lines) while still making the role-to-skill mapping discoverable and correct.
- **Orchestrator delegation uses scoped agent identifiers.** `orchestrating-development-team` now names agents as `ai-dev-team:<agent-name>` (e.g. `ai-dev-team:backend-engineer`) when describing delegation through the Agent tool, since plugin agents are namespaced and another installed plugin — or a project/user-level agent — can define an agent with the same bare name; the scoped identifier is what disambiguates which one actually runs.

## Consequences

- **Positive:** the safety/evidence policy now holds under direct invocation of any skill or agent, not only when `orchestrating-development-team` ran first. The fix required one new ~50-line skill file and small frontmatter/prose edits to existing files, not a rewrite.
- **Trade-off:** every agent's startup context now includes the full `enforcing-safety-baseline` text (previously zero). This is an intentional, bounded cost — the file is kept small specifically because it is unconditionally preloaded ten times over (once per agent invocation, in each agent's own isolated context, not cumulatively).
- **Follow-up:** if `enforcing-safety-baseline` grows significantly for an unrelated reason in the future, that growth cost is paid by every agent's startup context, which is a reason to keep future additions to it deliberately minimal, or to split out a second, narrower preloadable skill instead of growing this one.
