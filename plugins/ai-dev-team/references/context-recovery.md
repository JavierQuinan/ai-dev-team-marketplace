# Project context recovery strategy

Shared reference for reconstructing "where were we" from repository evidence. Used primarily by `continuing-project-work`, and consulted by `orchestrating-development-team` before delegating.

## Priority order

Resolve context in this order; higher-priority sources override lower ones when they conflict:

1. **Explicit user request** — what the user just asked ("continúa el módulo agenda", "sigue con el frontend"). This scopes everything below.
2. **Current git state** — `git status`, `git diff`, `git log -20 --oneline`, current branch name, unpushed commits, stash list. This is ground truth for "what changed" and "what's uncommitted."
3. **Project instructions** — `CLAUDE.md`, `AGENTS.md` (if present), any repo-root or nested instruction files. These define conventions and constraints, not progress.
4. **Recent work** — last N commits' messages and diffs, recently modified files (`git log --stat`, `git diff HEAD~5`), open branches related to the requested scope.
5. **Architecture/docs** — `README`, `docs/`, ADRs, `CHANGELOG.md` — for what the system is supposed to do, useful to distinguish "not built yet" from "built but broken."
6. **Tests** — existing test files and their pass/fail state, to find features with either coverage (likely finished) or failing/missing coverage (likely in progress).
7. **Inferred next step** — only after the above, propose the most likely next action, and label it clearly as an inference, not a fact.

If the tool environment allows access to issue trackers or PRs (e.g. `gh`), pull that context too, but rank it alongside recent work (level 4) — it complements git state, it doesn't override it.

## Rules

- Never assert progress ("X is done") without a corresponding artifact: a commit, a passing test, or code that visibly implements it. "The README says X was planned" is not evidence that X is done.
- When a scope word is given ("agenda", "superadmin", "sanitización"), first find that scope in the actual repo (matching directories, modules, branch names, commit messages) before reasoning about it — don't rely on the term matching something remembered from earlier in the conversation only.
- Prefer the working tree's real diff over any prior conversation summary — code and git are authoritative over memory.
- Uncommitted changes matter: if `git status` shows a dirty tree, describe what's dirty before proposing next steps, since it may itself be the unfinished work.
- Do not silently redo or rewrite functionality that evidence shows is already complete (implemented + passing tests). If it looks complete but the user says otherwise, ask what's actually wrong rather than reimplementing from scratch.
- Present the reconstructed state, the identified risks (uncommitted work, failing tests, stale branches), and the proposed next step as three distinct, labeled sections before starting any implementation.
