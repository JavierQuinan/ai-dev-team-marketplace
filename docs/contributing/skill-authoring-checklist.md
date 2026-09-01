# Skill authoring checklist

Quick-reference checklist for `python scripts/validate.py` reviewers and PR authors. The full standard is in [../../CONTRIBUTING.md](../../CONTRIBUTING.md); this is the condensed version to paste into a review.

- [ ] `SKILL.md` lives at `plugins/ai-dev-team/skills/<kebab-case-name>/SKILL.md`
- [ ] Frontmatter `name` is present and equals the directory name exactly
- [ ] Frontmatter `description` is third person, states what + when, includes concrete trigger phrasing
- [ ] `SKILL.md` is under ~250 lines
- [ ] Links [`enforcing-safety-baseline`](../../plugins/ai-dev-team/skills/enforcing-safety-baseline/SKILL.md) for the evidence/safety policy, and `references/stack-detection.md` / `references/context-recovery.md` where relevant — none of it restated inline
- [ ] Has a Workflow section
- [ ] Has a Decisions section covering realistic edge cases
- [ ] Has an Exit criteria section that requires evidence, not just a claim of completion
- [ ] No hardcoded reference to a specific private project, client, or vertical
- [ ] No secrets, tokens, or real credentials anywhere in the skill or its supporting files
- [ ] At least 3 evals added/updated in `tests/evals/` matching the skill
- [ ] `python scripts/validate.py` passes with no errors
- [ ] `claude plugin validate ./plugins/ai-dev-team --strict` passes (schema authority; see [../architecture/token-efficiency.md](../architecture/token-efficiency.md#frontmatter-validation-what-this-repos-validator-does-and-does-not-check) for what each validator actually checks)
- [ ] If this skill is meant to be reached by an agent, that agent's `skills:` preload list or `Skill`-tool pointer was updated to match
