---
name: continuing-project-work
description: Reconstructs real project state from git and repo evidence and resumes work when the user says things like "continue where we left off", "continue the agenda module", "resume the superadmin work", "keep going on the frontend", or "continue from the last PR". Use whenever a request refers to prior or ongoing work without restating what it is.
when_to_use: Trigger phrases include "continúa", "sigue con", "retoma", "continue", "resume", "pick up where we left off", or any request that names a module/feature without describing it from scratch.
---

# Continuing project work

Reconstruct project state from verifiable evidence, then resume the implied work. Never rely on conversational memory alone — code and git are authoritative. See [references/context-recovery.md](../../references/context-recovery.md) for the full priority order and rules this skill follows, and [references/evidence-and-safety.md](../../references/evidence-and-safety.md) for the evidence and confirmation policy shared by every skill in this plugin.

## When to activate

- The user references prior work without fully describing it ("continúa el superadmin", "sigue con el frontend", "continúa desde el último PR").
- The user says only "continue" / "continúa" with no further detail.
- A session is resuming after a compaction or a new session opens in a repo with uncommitted or recent work.

## Workflow

1. **Scope the request.** Identify what the user pointed at (a module name, "the frontend", "the last PR", or nothing specific). If nothing specific, the scope is "the most recently active work."
2. **Gather evidence**, following the priority order in `context-recovery.md`:
   - `git status --porcelain`, `git branch --show-current`, `git log -20 --oneline`, `git diff` / `git diff --stat HEAD~5`, `git stash list`.
   - `CLAUDE.md`, `AGENTS.md`, `README.md`, `docs/`, `CHANGELOG.md` if present.
   - Files/directories matching the named scope (search by name, not by guessing).
   - Test files and their last known pass/fail state (run the relevant subset if cheap; don't assume from file presence alone).
   - If GitHub tooling is available (`gh`), check open PRs/issues touching the scoped area.
3. **Reconstruct and report state** before touching anything, as three labeled sections:
   - **Current state** — branch, dirty/clean tree, what the last commits did, what the code currently does (verified, not assumed).
   - **Risks** — uncommitted changes, failing tests, stale/diverged branches, TODOs or `FIXME`s in the scoped area.
   - **Proposed next step** — the most defensible next action, explicitly labeled as an inference if it isn't directly evidenced.
4. **Confirm scope alignment** only if the evidence is ambiguous or contradicts the user's framing (e.g., user says "continue the agenda module" but no such module exists) — otherwise proceed directly into the implied work using `implementing-features`, `debugging-systematically`, or another skill as appropriate.
5. **Resume work on top of what exists.** Do not rewrite functionality that evidence shows is complete. Extend, fix, or finish — don't restart.

## Decisions

- Ambiguous scope + no strong evidence → ask a single clarifying question rather than guessing broadly.
- Dirty working tree → surface it first; it may itself be the unfinished work the user means.
- Conflicting signals (e.g., README says a feature is done, but no code implements it) → trust the code, report the discrepancy.

## Exit criteria

- State is described with cited evidence (commands run, files inspected), not inferred from conversation alone.
- The user has an accurate picture of what's done, what's dirty, and what's next before any new implementation starts.
- No claim of "already working" or "already tested" is made without having just verified it.
