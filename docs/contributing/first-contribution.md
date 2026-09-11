# First contribution

This guide is the shortest path from a fresh checkout to a reviewable pull request.

## Pick a scoped issue

Start with an issue labeled `good first issue` or `help wanted`. Prefer a task that changes one responsibility at a time: one reference, one validation rule, one eval family, or one documentation path.

Before coding, leave a short comment describing the scope you intend to take. This helps avoid duplicate work.

## Set up the repository

Fork `JavierQuinan/ai-dev-team-marketplace` to your GitHub account first. Then clone your fork and add the canonical repository as `upstream`:

```bash
git clone https://github.com/<your-user>/ai-dev-team-marketplace.git
cd ai-dev-team-marketplace
git remote add upstream https://github.com/JavierQuinan/ai-dev-team-marketplace.git
git fetch upstream
git checkout -b <type>/<short-description> upstream/main
```

Push contribution branches to your fork:

```bash
git push -u origin <type>/<short-description>
```

Open the pull request from your fork branch into `JavierQuinan/ai-dev-team-marketplace:main`.

The repository has no application build step. Its source is validated as plugin content.

Run the local validator before changing anything so you know the baseline is clean:

```bash
python scripts/validate.py
```

For schema validation with the official Claude Code CLI:

```bash
npm install -g @anthropic-ai/claude-code
claude plugin validate . --strict
claude plugin validate ./plugins/ai-dev-team --strict
```

## Make the smallest useful change

Keep the change evidence-driven and repository-generic.

For references and skill extensions:

- extend an existing skill before proposing a new one;
- keep stack-specific details opt-in;
- do not encode private-project names, infrastructure, customer data, or secrets;
- add or update eval scenarios for materially changed behavior;
- include negative or insufficient-evidence cases where false positives are possible.

For documentation:

- describe behavior that exists now;
- distinguish implemented behavior from roadmap intent;
- keep links relative when the target lives in this repository.

## Validate

Run the checks relevant to your change:

```bash
python scripts/validate.py
python tests/test_validate.py -v
node --test tests/devsecops_inventory.test.mjs
git diff --check
```

If your change touches a plugin manifest, skill, agent, or frontmatter, also run:

```bash
claude plugin validate . --strict
claude plugin validate ./plugins/ai-dev-team --strict
```

A pull request should not claim a check passed unless you actually ran it on the submitted revision.

## Open the pull request

Push your branch and open a focused PR against `main`.

A good PR explains:

1. the problem being solved;
2. the exact scope;
3. what intentionally remains out of scope;
4. validation performed;
5. any limitations or evidence gaps.

Do not include generated activity whose only purpose is to increase contribution counts. Contributions should remain independently useful to the project.

## Good first places to contribute

Current contribution-friendly work is tracked with the `good first issue` and `help wanted` labels.

Typical examples include:

- focused reference packs;
- CI/debugging guidance;
- eval coverage;
- validation edge cases;
- documentation clarity and installation troubleshooting.

For architecture constraints and skill-authoring rules, continue with [CONTRIBUTING.md](../../CONTRIBUTING.md) and [ROADMAP.md](../../ROADMAP.md).
