# ADR 0003: Plugin packaging boundary — self-contained plugin directories

## Status

Accepted — 2026-08-29 (second hardening pass on v0.1.0, pre-merge)

## Context

Second pre-merge review of PR #1 found a P1 blocker: several files inside `plugins/ai-dev-team/` linked to files elsewhere in the marketplace repository using relative paths that climb out of the plugin directory (`../../../../docs/...`, `../../README.md`, `../../CONTRIBUTING.md`, `../../docs/adr/...`).

That works in this monorepo checkout, where the whole repository is present. It does not work for anyone who actually installs the plugin from the marketplace: per the official documentation (`code.claude.com/docs/en/plugins-reference#plugin-cache`), "Claude Code copies *marketplace* plugins to the user's local **plugin cache** (`~/.claude/plugins/cache`) rather than using them in place," and explicitly, "Claude Code also doesn't copy files outside the plugin directory into the cache when it installs the plugin, so when a script inside a copied plugin reads a path above the plugin root, it doesn't find those files either." A skill or agent shipped with a dangling `../../` link is broken for every real installer, even though it validated cleanly for a contributor working in the full checkout — and neither `scripts/validate.py` (before this pass) nor `claude plugin validate` catches it, confirmed empirically (see `docs/architecture/token-efficiency.md#frontmatter-validation`).

The same official documentation also describes a sanctioned way to share files *within* a marketplace: a symlink inside a plugin directory pointing elsewhere in the same marketplace gets dereferenced and its target's content copied into the cache at install time ("This lets a meta-plugin's `skills/` directory link to skills defined by other plugins in the marketplace"). That mechanism was considered and rejected for this fix — it depends on `core.symlinks=true` and, on Windows, either Developer Mode or elevated privileges to check out correctly, which this project's own contributors (including this session's environment) cannot assume, and it adds a second, harder-to-audit way for plugin content to depend on the rest of the repo.

## Decision

Every runtime file inside `plugins/ai-dev-team/` (every `SKILL.md`, every agent file, and the two `references/*.md` files) must resolve entirely within `plugins/ai-dev-team/`. Three cases were resolved differently, matching the nature of each link:

- **Pure contributor rationale in a skill body** (`enforcing-safety-baseline` and `orchestrating-development-team` linking to `docs/architecture/token-efficiency.md` for "why"/"full reasoning"): the link added no runtime value — the actionable instruction was already stated inline — so it was **removed outright**, with the substance of the explanation folded into the surrounding sentence instead of left as a dangling "see X" pointer.
- **Purely navigational links from `plugins/ai-dev-team/README.md` and `CHANGELOG.md`** toward the marketplace root (`README.md`, `CONTRIBUTING.md`, an ADR): converted to **absolute GitHub URLs** (`https://github.com/JavierQuinan/ai-dev-team-marketplace/blob/main/...`). These files are read by a human browsing the installed plugin or the repo, not executed, so an absolute URL that survives being copied out of context is the right shape — and the README now says explicitly why these particular links are absolute instead of relative.
- No case required moving reference content *into* `plugins/ai-dev-team/references/` (Option B in the review) — nothing removed under the first bullet was runtime-required, so there was nothing left needing a home inside the plugin.

## Validator and test coverage

- `scripts/validate.py`'s `check_local_links` now takes an optional `plugin_root` and, when a link resolves to a real file *outside* that root, reports it as an error distinct from "broken link" (`runtime link escapes the plugin root`) — a link that exists in the checkout but wasn't going to ship with the plugin is exactly the bug this ADR fixes, and it must never again pass silently just because the target happens to exist in the monorepo.
- `tests/test_validate.py::TestPluginRootBoundary` covers both the escaping case (error) and a same-plugin sibling link (passes).
- `tests/test_validate.py::TestPackagingBoundary::test_plugin_is_self_contained_when_copied` goes further: it copies `plugins/ai-dev-team/` alone into a temp directory — literally simulating what a marketplace install does — and re-checks every link from that copy. This is the regression test for the exact failure mode that passed two previous rounds of CI unnoticed, because a full-checkout validator run had no way to observe what an actual install would and wouldn't have available.

## Consequences

- **Positive:** the plugin is now genuinely installable standalone; the packaging-boundary check and the copy-simulation test make this a structural guarantee going forward, not a one-time manual fix.
- **Trade-off:** contributor-facing "why" links from a `SKILL.md` body have to either stay inside the plugin or be dropped, which is a small loss of connective narrative for someone reading the skill file directly in the monorepo. Judged acceptable — the reasoning still exists in the ADRs and architecture docs; it's just not linked from inside a file that ships without them.
- **Follow-up:** if a future skill genuinely needs runtime content that's naturally shared across plugins in this marketplace, revisit the symlink mechanism from the official docs rather than reaching for another cross-plugin relative link — but only once the project's contribution tooling can guarantee `core.symlinks=true` and working symlink checkouts on all supported platforms.
