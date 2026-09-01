---
name: continuing-project-work
description: Reconstructs real project state from git and repo evidence and resumes work when the user says things like "continue where we left off", "continue the agenda module", "resume the superadmin work", "keep going on the frontend", or "continue from the last PR". Use whenever a request refers to prior or ongoing work without restating what it is.
when_to_use: Trigger phrases include "continúa", "sigue con", "retoma", "continue", "resume", "pick up where we left off", or any request that names a module/feature without describing it from scratch.
---

# Continuing project work

Reconstruct project state from verifiable evidence, then resume the implied work. Never rely on conversational memory alone — code and git are authoritative. See [references/context-recovery.md](../../references/context-recovery.md) for the full priority order and rules this skill follows, and [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md) for the evidence and confirmation policy shared by every skill in this plugin.

## When to activate

- The user references prior work without fully describing it ("continúa el superadmin", "sigue con el frontend", "continúa desde el último PR").
- The user says only "continue" / "continúa" with no further detail.
- A session is resuming after a compaction or a new session opens in a repo with uncommitted or recent work.

## Workflow

1. **Scope the request.** Identify what the user pointed at (a module name, "the frontend", "the last PR", or nothing specific). If nothing specific, the scope is "the most recently active work."
2. **Gather evidence**, following the priority order in `context-recovery.md`:
   - `git status --porcelain`, `git branch --show-current`, `git log -20 --oneline` (which naturally caps at however many commits exist — a 2-commit repo just returns 2), `git diff`, `git stash list`. Before using a fixed-depth command like `git diff HEAD~5`, confirm that much history exists (`git rev-list --count HEAD`); see [references/context-recovery.md](../../references/context-recovery.md#small-repo-and-shallow-clone-tolerance) for the fallback when it doesn't.
   - `CLAUDE.md`, `AGENTS.md`, `README.md`, `docs/`, `CHANGELOG.md` if present.
   - Files/directories matching the named scope (search by name, not by guessing).
   - Test files and their last known pass/fail state (run the relevant subset if cheap; don't assume from file presence alone).
   - If GitHub tooling is available (`gh`), check open PRs/issues touching the scoped area.
3. **Mandatory continuation checkpoint.** Between gathering evidence and any mutating action — `Edit`, `Write`, package installs, migrations, any git command that changes state, or any other `Bash` call that writes files or persists state — you MUST present the following three labeled sections as your response, in this order, before touching anything:
   - **Current state** — branch, dirty/clean tree, what the last commits did, what the code currently does (verified, not assumed).
   - **Risks** — uncommitted changes, failing tests, stale/diverged branches, TODOs or `FIXME`s in the scoped area.
   - **Proposed next step** — the most defensible next action, explicitly labeled as an inference if it isn't directly evidenced.

   A `TODO`/`FIXME`/comment/"scratch note" found in the code is evidence for the **Risks** or **Proposed next step** sections — it is never permission to skip this checkpoint. Running non-interactively (`-p`, no second turn available) does not remove this requirement either; the checkpoint still has to appear before the first mutating tool call in the same response.
4. **Decide once, right after the checkpoint — don't leave it open:**
   - **REPORT CHECKPOINT → CONTINUE**, in the same turn, with no further question, when *all* of these hold: the user already said "continue" / "sigue" / "retoma" (or otherwise already authorized resuming), the reconstructed scope is unambiguous, the proposed next step is reversible, and it doesn't materially expand scope beyond what the evidence showed. The user already gave you the go-ahead — asking "should I proceed?" again here is a redundant confirmation, not caution.
   - **Stop and ask instead** when any of: scope is still ambiguous; evidence contradicts what the user asked for; the next step would materially expand scope beyond the reconstructed state; a new dependency needs introducing; the action is irreversible or high-blast-radius; or `enforcing-safety-baseline` already requires confirmation for it (that policy is never overridden by this one). If running non-interactively and the needed confirmation genuinely can't be obtained, end the turn right after the checkpoint — do not guess and do not proceed.
5. **Resume work on top of what exists.** Do not rewrite functionality that evidence shows is complete. Extend, fix, or finish — don't restart.

## Decisions

- Ambiguous scope + no strong evidence → ask a single clarifying question rather than guessing broadly.
- Dirty working tree → surface it first; it may itself be the unfinished work the user means.
- Conflicting signals (e.g., README says a feature is done, but no code implements it) → trust the code, report the discrepancy.
- An obvious in-code TODO plus a bare "continue" is still scope the user handed you, not silent permission to skip the checkpoint — show it, then continue if the other auto-continue conditions in step 4 hold.

## Exit criteria

- State is described with cited evidence (commands run, files inspected), not inferred from conversation alone.
- The checkpoint (Current state / Risks / Proposed next step) appears in the response before any `Edit`, `Write`, install, migration, or state-changing `Bash` call — never after, never interleaved.
- Auto-continuing past the checkpoint only happens when scope was already clear and the user already authorized resuming; anything ambiguous, scope-expanding, or irreversible stops for real confirmation instead.
- No claim of "already working" or "already tested" is made without having just verified it.
