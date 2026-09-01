# Token efficiency strategy

This marketplace is designed so that having many skills installed costs almost nothing until one of them is actually used. This document explains the strategy so future skills (v0.2+) follow the same discipline.

## Progressive disclosure

Claude Code loads skill *metadata* (`name` + `description`, and `when_to_use` if present) for every installed skill so it can decide when to invoke one — this is the only cost paid just by having the plugin installed. The full `SKILL.md` body loads only when a skill is actually invoked. Anything inside `SKILL.md` that isn't needed for every invocation belongs in a separate file instead.

This plugin applies three tiers:

1. **Metadata (always loaded).** `name` + `description` (+ `when_to_use` where the trigger phrasing needs to be explicit). Kept to one or two sentences, written in third person, stating what the skill does and when to use it — concrete enough that Claude can discriminate between skills without opening any of them.
2. **SKILL.md body (loaded on invocation).** Workflow, decisions, and exit criteria for that skill only. Target: under 250 lines (stricter than the official 500-line guidance) so a single invocation's context cost stays small even when a skill is invoked mid-conversation.
3. **references/ (loaded only when the skill body links to it and the task needs it).** Detailed, reusable material — stack-detection patterns, the context-recovery strategy — factored out once and linked from every skill that needs it, instead of restated per skill.

The evidence/safety policy is the one exception to "reference, not skill": it lives at `skills/enforcing-safety-baseline/SKILL.md` instead of in `references/`, for the reason explained in [Agent context and the safety baseline](#agent-context-and-the-safety-baseline) below — a plain reference file can't be preloaded into a subagent's context, and this policy needs to reach agents that never go through a parent skill at all.

## Why references/ instead of inlining

Two pieces of policy are shared across most or all of the ten workflow skills: stack detection (how to identify frontend/backend/DB/testing tooling from evidence) and, for the skills that use it, the project-context-recovery priority order. Inlining these into every `SKILL.md` file would mean:

- ~10x the token cost paid every time any one of them loads a full copy inline versus a link.
- Ten places to keep in sync if the policy changes, with drift as the near-certain outcome.

Instead, `plugins/ai-dev-team/references/stack-detection.md` and `references/context-recovery.md` hold that content once. Each `SKILL.md` links to the specific reference(s) it needs with a relative markdown link, so Claude opens the reference only when working the skill that needs it — not preloaded, not duplicated. The evidence/safety policy follows the same "write once, link everywhere" principle, but through the skill-preload mechanism rather than a markdown link — see below.

## Agent context and the safety baseline

Earlier revisions of this document claimed a subagent could rely on safety/evidence discipline "already being active" because a parent skill had loaded it. That claim was wrong, and the corrected model is recorded here so it isn't reintroduced.

Per the official subagent documentation: **"Each subagent starts with a fresh, isolated context window. It doesn't see your conversation history, the skills you've already invoked, or the files Claude has already read."** ([code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents#manage-subagent-context)) A subagent's initial context is composed only of the delegation message Claude writes, its own system prompt, and — critically — the full content of any skill listed in its frontmatter `skills` field. Nothing a parent skill loaded carries over automatically.

This means an `ai-dev-team` agent invoked directly (by name, by `@agent-ai-dev-team:<name>`, or delegated to from outside `orchestrating-development-team` entirely) would start with none of the safety/evidence policy in context unless that policy is preloaded into the agent itself. Depending on the parent to have "already loaded a skill" doesn't help a subagent that never saw the parent's context in the first place.

**Fix:** every agent in `agents/` preloads `enforcing-safety-baseline` via its own `skills:` frontmatter field:

```yaml
tools: Read, Edit, Write, Glob, Grep, Bash, Skill
skills: [enforcing-safety-baseline]
```

`enforcing-safety-baseline` is deliberately small (a few dozen lines) precisely because it is injected in full into every one of the ten agents' contexts at startup — the "preload only what's small and universal" trade-off discussed below. It is a real skill (not a reference file) specifically because only skills can be named in a `skills:` preload list; `references/*.md` files cannot. It sets `user-invocable: false` (hidden from the `/` menu — it's infrastructure, not a user command) but must stay model-invocable, since Claude Code can't preload a skill that sets `disable-model-invocation: true`.

The ten workflow skills (`implementing-features`, `debugging-systematically`, etc.) are **not** preloaded into agents, on purpose: full-preloading a 30–50 line workflow skill into every invocation of its mapped agent, whether the task is trivial or not, would reintroduce the "mega-context on every call" problem this document exists to avoid. Instead, each agent's `tools` list includes `Skill`, and its system prompt names the one workflow skill most relevant to its role (e.g. `backend-engineer` names `implementing-features`), so the agent can pull in the full workflow via the Skill tool exactly when the task is non-trivial enough to need it — not on every trivial one-line change. This is the "safety + token efficiency + direct-invocation correctness" balance: the small, universal, safety-critical policy is unconditionally guaranteed; the larger, role-specific workflow guidance is available on demand rather than forced.

## When to open a reference vs. run a script

- **Open a reference** when the content is knowledge Claude needs to reason with (detection heuristics, policy rules, decision criteria).
- **Run a script** (in `scripts/`) when the logic is deterministic and repetitive — parsing, validation, structural checks — where executing code is cheaper and more reliable than having the model re-derive the logic from a written procedure every time. This marketplace currently uses this pattern for the repo-wide `scripts/validate.py` validator (see [../contributing/](../contributing/)) rather than for skill-internal logic, since none of the ten workflow skills has deterministic logic complex enough to justify a bundled script yet — a v0.2 candidate (e.g. dependency-vulnerability scanning in `auditing-security`) may add one.

## Avoiding context pollution

- No skill restates another skill's full workflow — `orchestrating-development-team` references the others by name and stage, it does not copy their instructions.
- Shared reference policy (stack detection, context recovery) lives once in `references/`, not per skill; the safety/evidence policy lives once in `enforcing-safety-baseline`, not per skill or per agent.
- Descriptions are written to be discriminating on their own (specific trigger phrases, specific "when to use") so Claude doesn't need to open a skill body just to figure out whether it's the right one.
- Agents in `agents/` carry only role-specific instructions in their own prose; the safety/evidence policy reaches them through the `skills:` preload mechanism (one small, shared source) rather than being copy-pasted into all ten agent files — see [Agent context and the safety baseline](#agent-context-and-the-safety-baseline).

## Keeping metadata discovery-friendly

- `description` states the concrete action and the concrete trigger — "reviews a diff or PR ... use when asked to review code, check a PR" — not "helps with code."
- `when_to_use` (where present) captures literal phrasing users say ("continúa", "resume", "prueba con Playwright") so intent matching doesn't depend on the model inferring paraphrases.
- Skill and agent names are literal, task-shaped (`debugging-systematically`, not `helper` or `assistant-2`), so the namespaced command (`/ai-dev-team:debugging-systematically`) is self-explanatory even without reading the description.

## Frontmatter validation: what this repo's validator does and does not check

`scripts/validate.py` is stdlib-only Python: it has no YAML library and does not attempt to be one. Its frontmatter reader (`Validator.parse_frontmatter`) understands exactly three shapes: a single-line `key: value`; a single-line inline list `key: [a, b, c]`; and a simple block-style list (`key:` on its own line followed by `  - item` lines). It does **not** parse nested maps, multi-line strings, YAML anchors/aliases, or a block list mixed with other content under the same key. None of this plugin's current `SKILL.md` or agent files use anything beyond those three shapes, by convention — `CONTRIBUTING.md` asks new contributions to keep the same convention specifically so this stays true.

This is a deliberate scope decision (Option A, evaluated during the v0.1.0 hardening pass), not an oversight: **the official `claude plugin validate` command is the schema authority**, and this script only adds checks the official CLI is not designed to make:

| Check | Official `claude plugin validate` | This repo's `scripts/validate.py` |
|---|---|---|
| marketplace.json / plugin.json JSON validity and required top-level fields | Yes | Yes (redundant, kept for a single fast local check) |
| Agent frontmatter (`name`, `description` presence, format) | Yes (confirmed empirically — see below) | Yes (redundant) |
| Skill frontmatter deep validation (`name` format, non-empty `description`) | **Not observed** — an empty `description` and an invalid `name` in a `SKILL.md` both passed `claude plugin validate --strict` with zero warnings in local testing (Claude Code v2.1.251) | Yes — this is the check the pre-merge review specifically asked for |
| Skill frontmatter `name` matching its directory (this repo's own convention, not a Claude Code requirement) | No — not a spec requirement, so not checked | Yes |
| A skill/agent's declared `skills:` preload list pointing at a skill that doesn't exist | **Not observed** — a nonexistent skill name in an agent's `skills:` field passed validation in local testing | Yes |
| Multi-plugin marketplace: every declared local plugin resolves and validates independently | The CLI itself only validates the single path you point it at — CI compensates by looping it over every local plugin `scripts/list_local_plugins.py` finds | Yes — `scripts/validate.py` itself iterates every `plugins[]` entry in `marketplace.json` |
| A runtime link (in a skill/agent file) that resolves to a real file in the monorepo checkout but *outside the plugin's own directory* | **Not observed** — empirically verified: a fixture plugin whose `SKILL.md` linked one directory above the plugin root passed `claude plugin validate --strict` with zero warnings (Claude Code v2.1.251); only an unrelated `author`-field warning showed up, from other missing metadata in that fixture | Yes — this is the P1 packaging-boundary check; Claude Code copies only the plugin's own directory into the cache on install (see [ADR 0003](../adr/0003-plugin-packaging-boundary.md)), so this can only be caught by a checker that knows where the plugin root is |
| `tests/evals/*.json` schema and per-`(plugin, skill)` eval coverage (≥3 evals per pair) | N/A — this repo's own convention, not a Claude Code concept | Yes |
| Local markdown link integrity between skill/agent/doc files | N/A | Yes |
| Full JSON-Schema-level correctness (field types, enum values, unrecognized-key warnings) | Yes | No — not attempted |

Run both, for different reasons:

```bash
# Schema authority — install once, no Anthropic credentials required:
npm install -g @anthropic-ai/claude-code
claude plugin validate . --strict                       # marketplace.json
python scripts/list_local_plugins.py | while read -r p;  do
  claude plugin validate "$p" --strict                   # every local plugin's manifest + component paths
done

# This repo's own invariants (multi-plugin aware, name/eval/link/packaging-boundary checks above):
python scripts/validate.py
```

Never describe this script's output as "valid frontmatter" or "schema-validated" in documentation — say specifically what it checked, per the table above. If a future version of `claude plugin validate` starts deep-checking skill frontmatter, the corresponding row in this table (and the redundant checks in this script) should be revisited rather than left stale.
