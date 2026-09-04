# Contributing to ai-dev-team-marketplace

Thanks for considering a contribution. This marketplace favors a small number of excellent, composable skills over broad, shallow coverage — read this before proposing a new skill.

## Before proposing a new skill

Ask first whether the need is better served by:

1. **Extending an existing skill's `references/`** — e.g. adding a new framework's detection pattern to `references/stack-detection.md` rather than creating a framework-specific skill.
2. **Adding a reference/template/script inside an existing skill's directory** — if the new content only ever applies within one skill's workflow.
3. **A genuinely new responsibility** — only then propose a new skill, using the "new skill proposal" issue template.

See [docs/adr/0001-marketplace-architecture.md](docs/adr/0001-marketplace-architecture.md) for why this marketplace is structured this way, and [ROADMAP.md](ROADMAP.md) for families already under consideration.

## Development setup

No build step is required — this repository is plugin source, validated with Python's standard library.

```bash
# Validate the whole marketplace (JSON validity, structure, frontmatter, eval schemas, local links)
python scripts/validate.py

# Load the plugin locally in Claude Code for manual testing
claude --plugin-dir ./plugins/ai-dev-team
```

Inside a session started with `--plugin-dir`, exercise the skill directly (`/ai-dev-team:<skill-name>`) or let Claude invoke it automatically based on your prompt. Run `/reload-plugins` after editing files to pick up changes without restarting.

## Skill authoring standard

Every `SKILL.md` in this repository must:

- Live at `plugins/ai-dev-team/skills/<skill-name>/SKILL.md`, where `<skill-name>` is lowercase, kebab-case, and verb-first where possible (matching the naming pattern used by the existing skills, such as `analyzing-codebase` and `implementing-features`).
- Have YAML frontmatter with `name` **equal to the directory name** and `description`: third person, states what the skill does and when to use it, includes concrete trigger phrasing. Avoid vague descriptions ("helps with X"). `name` is optional per the Claude Code spec (it falls back to the directory name), but this repo requires it explicitly and requires it to match, because a plugin skill's frontmatter `name` silently overrides the invocation command's last segment — an unnoticed mismatch would ship a skill under a different command than its directory suggests. `scripts/validate.py` enforces this; see [Frontmatter validation](docs/architecture/token-efficiency.md#frontmatter-validation-what-this-repos-validator-does-and-does-not-check) for exactly what is and isn't checked.
- Stay under ~250 lines. Move detail to `references/`, `templates/`, or `scripts/` inside the skill's own directory, or to the plugin-level `references/` if the content is shared across skills.
- Not duplicate policy already covered by `plugins/ai-dev-team/references/stack-detection.md` or `references/context-recovery.md` — link to them instead. Not duplicate the evidence/safety policy either — link to [`enforcing-safety-baseline`](plugins/ai-dev-team/skills/enforcing-safety-baseline/SKILL.md) instead, as the workflow skills already do.
- Include a "Workflow" section, a "Decisions" section (how to handle the realistic edge cases), and an "Exit criteria" section (how to know the skill's job is actually done, backed by evidence — not by a claim).
- Never encode a specific private project's domain, naming, or infrastructure — this repository is consumed by unrelated projects and must stay generic.

See [docs/architecture/token-efficiency.md](docs/architecture/token-efficiency.md) for the full rationale behind these constraints, and run `claude plugin validate ./plugins/ai-dev-team` (installed via `npm install -g @anthropic-ai/claude-code`, no credentials required) before relying solely on `scripts/validate.py` — the official CLI is the schema authority; this repo's validator only checks invariants the official CLI doesn't (see below).

## Evals are required

Any new or materially changed skill needs at least 3 scenario evals in `tests/evals/`, following the existing JSON schema (`id`, `skill`, `scenario`, `query`, `expected_behavior`, `forbidden_behavior`, `evidence_required`). `scripts/validate.py` checks the schema; it does not execute the evals against a live model — that remains a manual review step until an automated eval runner is added (tracked in [ROADMAP.md](ROADMAP.md)).

## Pull requests

1. Branch from `main`, one focused change per PR.
2. Run `python scripts/validate.py` and fix everything it reports before opening the PR.
3. Fill out the PR template completely, including the reviewer checklist.
4. Never commit real secrets, `.env` files with real values, or data from a private project.
5. PRs are reviewed by a maintainer before merge; nothing is auto-merged.

## Contribution licensing

This project uses the Apache License 2.0 for both outbound and inbound contributions.

By intentionally submitting a contribution for inclusion in this project, you agree that the contribution is provided under the Apache License 2.0 in accordance with Section 5 of that license, unless you explicitly state otherwise in writing before submission or a separate written agreement applies.

You must have the legal right to submit the contribution. Do not submit code, documentation, prompts, datasets, generated artifacts, or other material that you are not authorized to contribute. If a contribution incorporates third-party material, identify its source and license and preserve any notices required by that license. Material whose terms are incompatible with Apache-2.0 must not be incorporated into this repository.

The project does not currently require a separate Contributor License Agreement (CLA) or Developer Certificate of Origin (DCO) sign-off. This keeps contribution friction low while preserving Apache-2.0's default contribution terms. If project governance changes in the future, any new contribution requirement will be documented prospectively.

See [LICENSE](LICENSE) for the license terms and [NOTICE](NOTICE) for project attribution notices.

## Code of conduct

Participation in this project is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security issues

Do not open a public issue for a security vulnerability — see [SECURITY.md](SECURITY.md) for responsible disclosure.

## Multilingual support

The canonical documentation is English, since this is an internationally-consumed open-source project. Issues and discussions in other languages (e.g. Spanish) are welcome; a maintainer may respond in that language, but canonical docs and skill content stay in English for consistency.
