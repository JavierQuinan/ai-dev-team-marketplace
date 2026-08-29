# Token efficiency strategy

This marketplace is designed so that having many skills installed costs almost nothing until one of them is actually used. This document explains the strategy so future skills (v0.2+) follow the same discipline.

## Progressive disclosure

Claude Code loads skill *metadata* (`name` + `description`, and `when_to_use` if present) for every installed skill so it can decide when to invoke one — this is the only cost paid just by having the plugin installed. The full `SKILL.md` body loads only when a skill is actually invoked. Anything inside `SKILL.md` that isn't needed for every invocation belongs in a separate file instead.

This plugin applies three tiers:

1. **Metadata (always loaded).** `name` + `description` (+ `when_to_use` where the trigger phrasing needs to be explicit). Kept to one or two sentences, written in third person, stating what the skill does and when to use it — concrete enough that Claude can discriminate between skills without opening any of them.
2. **SKILL.md body (loaded on invocation).** Workflow, decisions, and exit criteria for that skill only. Target: under 250 lines (stricter than the official 500-line guidance) so a single invocation's context cost stays small even when a skill is invoked mid-conversation.
3. **references/ (loaded only when the skill body links to it and the task needs it).** Detailed, reusable material — stack-detection patterns, the evidence/safety policy, the context-recovery strategy — factored out once and linked from every skill that needs it, instead of restated per skill.

## Why references/ instead of inlining

Three pieces of policy are shared across most or all of the ten skills: the evidence rule (never claim "tests pass" without running them), the safety rule (irreversible actions need confirmation), and stack detection (how to identify frontend/backend/DB/testing tooling from evidence). Inlining these into all ten `SKILL.md` files would mean:

- ~10x the token cost paid every time any one of them loads a full copy inline versus a link.
- Ten places to keep in sync if the policy changes, with drift as the near-certain outcome.

Instead, `plugins/ai-dev-team/references/evidence-and-safety.md`, `references/stack-detection.md`, and `references/context-recovery.md` hold that content once. Each `SKILL.md` links to the specific reference(s) it needs with a relative markdown link, so Claude opens the reference only when working the skill that needs it — not preloaded, not duplicated.

## When to open a reference vs. run a script

- **Open a reference** when the content is knowledge Claude needs to reason with (detection heuristics, policy rules, decision criteria).
- **Run a script** (in `scripts/`) when the logic is deterministic and repetitive — parsing, validation, structural checks — where executing code is cheaper and more reliable than having the model re-derive the logic from a written procedure every time. This marketplace currently uses this pattern for the repo-wide `scripts/validate.py` validator (see [../contributing/](../contributing/)) rather than for skill-internal logic, since none of the ten foundational skills has deterministic logic complex enough to justify a bundled script yet — a v0.2 candidate (e.g. dependency-vulnerability scanning in `auditing-security`) may add one.

## Avoiding context pollution

- No skill restates another skill's full workflow — `orchestrating-development-team` references the other nine by name and stage, it does not copy their instructions.
- Shared policy lives once in `references/`, not per skill.
- Descriptions are written to be discriminating on their own (specific trigger phrases, specific "when to use") so Claude doesn't need to open a skill body just to figure out whether it's the right one.
- Agents in `agents/` carry only role-specific instructions; they do not re-embed the shared safety/evidence policy — that discipline is expected to already be active for the parent skill that delegated to them.

## Keeping metadata discovery-friendly

- `description` states the concrete action and the concrete trigger — "reviews a diff or PR ... use when asked to review code, check a PR" — not "helps with code."
- `when_to_use` (where present) captures literal phrasing users say ("continúa", "resume", "prueba con Playwright") so intent matching doesn't depend on the model inferring paraphrases.
- Skill and agent names are literal, task-shaped (`debugging-systematically`, not `helper` or `assistant-2`), so the namespaced command (`/ai-dev-team:debugging-systematically`) is self-explanatory even without reading the description.
