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
- [ ] `claude plugin validate .` and `claude plugin validate ./plugins/<plugin>` pass locally (`npm install -g @anthropic-ai/claude-code`, no credentials required)
- [ ] Tested locally with `claude --plugin-dir ./plugins/<plugin>`
- [ ] New/changed skill has at least 3 evals in `tests/evals/`
- [ ] New/changed agent still preloads `enforcing-safety-baseline` (or the equivalent for a new plugin) if it's meant to be directly invocable

## Security

- [ ] No secrets, tokens, or real credentials included
- [ ] No hardcoded reference to a specific private project or client
- [ ] Any irreversible-action guidance still routes through the shared confirmation policy (`plugins/ai-dev-team/skills/enforcing-safety-baseline/SKILL.md`), reachable by direct invocation, not only via `orchestrating-development-team`

## Reviewer checklist

- [ ] `SKILL.md`/agent frontmatter is complete and discovery-friendly (see [docs/contributing/skill-authoring-checklist.md](../docs/contributing/skill-authoring-checklist.md))
- [ ] No unnecessary duplication of existing skill/agent responsibility
- [ ] Progressive disclosure respected (SKILL.md stays lean, detail lives in references/)
- [ ] CI is green
