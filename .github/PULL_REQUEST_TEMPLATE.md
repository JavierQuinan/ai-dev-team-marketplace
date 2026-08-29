## Summary

<!-- What does this PR change and why? 1-3 bullet points. -->

## Type of change

- [ ] New skill
- [ ] New agent
- [ ] Change to an existing skill/agent
- [ ] Documentation
- [ ] CI / tooling
- [ ] Other (describe above)

## Validation

- [ ] `python scripts/validate.py` passes locally
- [ ] Tested locally with `claude --plugin-dir ./plugins/ai-dev-team`
- [ ] New/changed skill has at least 3 evals in `tests/evals/`

## Security

- [ ] No secrets, tokens, or real credentials included
- [ ] No hardcoded reference to a specific private project or client
- [ ] Any irreversible-action guidance still routes through the shared confirmation policy (`references/evidence-and-safety.md`)

## Reviewer checklist

- [ ] `SKILL.md`/agent frontmatter is complete and discovery-friendly (see [docs/contributing/skill-authoring-checklist.md](../docs/contributing/skill-authoring-checklist.md))
- [ ] No unnecessary duplication of existing skill/agent responsibility
- [ ] Progressive disclosure respected (SKILL.md stays lean, detail lives in references/)
- [ ] CI is green
