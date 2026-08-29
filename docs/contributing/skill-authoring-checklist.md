# Skill authoring checklist

Quick-reference checklist for `python scripts/validate.py` reviewers and PR authors. The full standard is in [../../CONTRIBUTING.md](../../CONTRIBUTING.md); this is the condensed version to paste into a review.

- [ ] `SKILL.md` lives at `plugins/ai-dev-team/skills/<kebab-case-name>/SKILL.md`
- [ ] Frontmatter `description` is third person, states what + when, includes concrete trigger phrasing
- [ ] `SKILL.md` is under ~250 lines
- [ ] Shared policy (evidence/safety, stack detection, context recovery) is linked from `references/`, not restated
- [ ] Has a Workflow section
- [ ] Has a Decisions section covering realistic edge cases
- [ ] Has an Exit criteria section that requires evidence, not just a claim of completion
- [ ] No hardcoded reference to a specific private project, client, or vertical
- [ ] No secrets, tokens, or real credentials anywhere in the skill or its supporting files
- [ ] At least 3 evals added/updated in `tests/evals/` matching the skill
- [ ] `python scripts/validate.py` passes with no errors
