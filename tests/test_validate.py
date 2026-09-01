#!/usr/bin/env python3
"""Deterministic tests for scripts/validate.py (and scripts/list_local_plugins.py).

Standard-library only (unittest + tempfile). Each test builds a minimal,
throwaway fixture repository under a temp directory and runs a fresh
Validator against it, so these tests never depend on the state of the real
ai-dev-team-marketplace repo and never leak errors/warnings between cases.
A handful of tests deliberately target the real repo (packaging boundary,
agent namespacing) — those are regression tests for bugs that specifically
slipped through the first two rounds of pre-merge review.

Usage:
    python tests/test_validate.py
    python -m unittest tests.test_validate -v
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load(module_name: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(module_name, REPO_ROOT / rel_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validate = _load("validate", "scripts/validate.py")
Validator = validate.Validator
MD_LINK_RE = validate.MD_LINK_RE

list_local_plugins = _load("list_local_plugins", "scripts/list_local_plugins.py")


MINIMAL_SKILL_MD = """---
name: {name}
description: A minimal test skill for validator fixtures.
---

# {name}

## Workflow

Do the thing.

## Decisions

- N/A.

## Exit criteria

- Done.
"""

MINIMAL_AGENT_MD = """---
name: {name}
description: A minimal test agent for validator fixtures.
tools: Read
---

You are a test agent.
"""


def make_eval(plugin: str, skill: str, idx: int) -> dict:
    return {
        "id": f"{plugin}-{skill}-{idx:02d}",
        "plugin": plugin,
        "skill": skill,
        "scenario": "A test scenario.",
        "query": "do the thing",
        "expected_behavior": "does the thing correctly",
        "forbidden_behavior": "does the wrong thing",
        "evidence_required": "evidence of the thing",
    }


class Fixture:
    """Builds a minimal marketplace + plugin(s) fixture under a temp dir."""

    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def cleanup(self):
        self._tmp.cleanup()

    def write_file(self, rel_path: str, content: str) -> Path:
        path = self.root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_marketplace(self, plugins: list[dict], **extra) -> None:
        mp_dir = self.root / ".claude-plugin"
        mp_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "name": "test-marketplace",
            "owner": {"name": "Test Owner"},
            "plugins": plugins,
            **extra,
        }
        (mp_dir / "marketplace.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def write_plugin(
        self,
        rel_path: str,
        name: str,
        *,
        version: str = "0.1.0",
        skills: dict[str, dict] | None = None,
        agents: dict[str, dict] | None = None,
        write_manifest: bool = True,
    ) -> Path:
        plugin_root = self.root / rel_path
        (plugin_root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
        if write_manifest:
            manifest = {"name": name, "description": "test plugin", "version": version}
            (plugin_root / ".claude-plugin" / "plugin.json").write_text(
                json.dumps(manifest, indent=2), encoding="utf-8"
            )

        skills = skills if skills is not None else {"sample-skill": {}}
        for skill_name, opts in skills.items():
            skill_dir = plugin_root / "skills" / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)
            body = opts.get("body")
            if body is None:
                fm_name = opts.get("fm_name", skill_name)
                if opts.get("omit_name"):
                    body = MINIMAL_SKILL_MD.replace("name: {name}\n", "").format(name=skill_name)
                else:
                    body = MINIMAL_SKILL_MD.format(name=fm_name)
            (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")

        agents = agents if agents is not None else {}
        if agents:
            (plugin_root / "agents").mkdir(parents=True, exist_ok=True)
        for agent_name, opts in agents.items():
            body = opts.get("body", MINIMAL_AGENT_MD.format(name=opts.get("fm_name", agent_name)))
            (plugin_root / "agents" / f"{agent_name}.md").write_text(body, encoding="utf-8")

        return plugin_root

    def write_evals(self, evals: list[dict], filename: str = "sample.json") -> None:
        evals_dir = self.root / "tests" / "evals"
        evals_dir.mkdir(parents=True, exist_ok=True)
        (evals_dir / filename).write_text(json.dumps(evals, indent=2), encoding="utf-8")

    def write_full_evals_for(self, plugin: str, skill_names: list[str]) -> None:
        evals = [make_eval(plugin, s, i) for s in skill_names for i in range(1, 4)]
        self.write_evals(evals, filename=f"{plugin}.json")


class ValidatorTestCase(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def run_validator(self) -> Validator:
        v = Validator(self.fx.root)
        v.run()
        return v


class TestValidMarketplace(ValidatorTestCase):
    def test_minimal_valid_single_plugin_marketplace_passes(self):
        self.fx.write_marketplace([{"name": "demo-plugin", "source": "./plugins/demo-plugin", "version": "0.1.0"}])
        self.fx.write_plugin("plugins/demo-plugin", "demo-plugin")
        self.fx.write_full_evals_for("demo-plugin", ["sample-skill"])

        v = self.run_validator()
        self.assertEqual(v.errors, [], msg=f"unexpected errors: {v.errors}")

    def test_valid_two_plugin_marketplace_passes(self):
        self.fx.write_marketplace(
            [
                {"name": "plugin-one", "source": "./plugins/plugin-one", "version": "0.1.0"},
                {"name": "plugin-two", "source": "./plugins/plugin-two", "version": "0.1.0"},
            ]
        )
        self.fx.write_plugin("plugins/plugin-one", "plugin-one", skills={"skill-a": {}})
        self.fx.write_plugin("plugins/plugin-two", "plugin-two", skills={"skill-b": {}})
        self.fx.write_full_evals_for("plugin-one", ["skill-a"])
        self.fx.write_full_evals_for("plugin-two", ["skill-b"])

        v = self.run_validator()
        self.assertEqual(v.errors, [], msg=f"unexpected errors: {v.errors}")


class TestPluginResolution(ValidatorTestCase):
    def test_nonexistent_plugin_source_is_an_error(self):
        self.fx.write_marketplace([{"name": "ghost-plugin", "source": "./plugins/does-not-exist", "version": "0.1.0"}])

        v = self.run_validator()
        self.assertTrue(
            any("does not exist" in e for e in v.errors),
            msg=f"expected a missing-source error, got: {v.errors}",
        )

    def test_second_plugin_invalid_missing_manifest_is_an_error(self):
        self.fx.write_marketplace(
            [
                {"name": "plugin-one", "source": "./plugins/plugin-one", "version": "0.1.0"},
                {"name": "plugin-two", "source": "./plugins/plugin-two", "version": "0.1.0"},
            ]
        )
        self.fx.write_plugin("plugins/plugin-one", "plugin-one")
        self.fx.write_plugin("plugins/plugin-two", "plugin-two", write_manifest=False)

        v = self.run_validator()
        self.assertTrue(
            any("plugin.json" in e and "missing required file" in e for e in v.errors),
            msg=f"expected a missing plugin.json error, got: {v.errors}",
        )

    def test_duplicate_plugin_name_is_an_error(self):
        self.fx.write_marketplace(
            [
                {"name": "dup-plugin", "source": "./plugins/dup-a", "version": "0.1.0"},
                {"name": "dup-plugin", "source": "./plugins/dup-b", "version": "0.1.0"},
            ]
        )
        self.fx.write_plugin("plugins/dup-a", "dup-plugin")
        self.fx.write_plugin("plugins/dup-b", "dup-plugin")

        v = self.run_validator()
        self.assertTrue(
            any("duplicate plugin name" in e for e in v.errors),
            msg=f"expected a duplicate plugin name error, got: {v.errors}",
        )

    def test_source_escaping_repo_root_is_an_error(self):
        self.fx.write_marketplace([{"name": "escaper", "source": "../outside", "version": "0.1.0"}])

        v = self.run_validator()
        self.assertTrue(
            any("escapes the repository root" in e for e in v.errors),
            msg=f"expected a path-escape error, got: {v.errors}",
        )

    def test_not_hardcoded_to_ai_dev_team(self):
        """The validator must work for a plugin with any name/path — no hardcoded assumption."""
        self.fx.write_marketplace([{"name": "totally-different-name", "source": "./somewhere/else", "version": "0.1.0"}])
        self.fx.write_plugin("somewhere/else", "totally-different-name")
        self.fx.write_full_evals_for("totally-different-name", ["sample-skill"])

        v = self.run_validator()
        self.assertEqual(v.errors, [], msg=f"unexpected errors: {v.errors}")


class TestSkillFrontmatter(ValidatorTestCase):
    def _single_plugin(self, skills: dict[str, dict]):
        self.fx.write_marketplace([{"name": "demo-plugin", "source": "./plugins/demo-plugin", "version": "0.1.0"}])
        self.fx.write_plugin("plugins/demo-plugin", "demo-plugin", skills=skills)

    def test_skill_missing_name_is_an_error(self):
        self._single_plugin({"my-skill": {"omit_name": True}})
        v = self.run_validator()
        self.assertTrue(
            any("frontmatter 'name' is required" in e for e in v.errors),
            msg=f"expected a missing-name error, got: {v.errors}",
        )

    def test_skill_name_mismatch_with_directory_is_an_error(self):
        self._single_plugin({"my-skill": {"fm_name": "totally-different-name"}})
        v = self.run_validator()
        self.assertTrue(
            any("does not match its" in e and "directory name" in e for e in v.errors),
            msg=f"expected a name-mismatch error, got: {v.errors}",
        )

    def test_duplicate_frontmatter_skill_name_is_an_error(self):
        self._single_plugin(
            {
                "skill-a": {"fm_name": "shared-name", "body": MINIMAL_SKILL_MD.format(name="shared-name")},
                "skill-b": {"fm_name": "shared-name", "body": MINIMAL_SKILL_MD.format(name="shared-name")},
            }
        )
        v = self.run_validator()
        self.assertTrue(
            any("duplicate skill frontmatter name" in e for e in v.errors),
            msg=f"expected a duplicate-name error, got: {v.errors}",
        )

    def test_missing_description_is_an_error(self):
        body = "---\nname: my-skill\n---\n\nNo description.\n"
        self._single_plugin({"my-skill": {"body": body}})
        v = self.run_validator()
        self.assertTrue(
            any("'description' is empty or missing" in e for e in v.errors),
            msg=f"expected a missing-description error, got: {v.errors}",
        )


class TestFrontmatterBlockList(unittest.TestCase):
    """Aligns with the documented parser subset: flat scalar, inline list,
    and simple block-style list are all supported; nothing else is."""

    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def test_inline_list_is_parsed(self):
        path = self.fx.write_file(
            "agent.md",
            "---\nname: my-agent\ndescription: test\nskills: [a, b, c]\n---\n\nBody.\n",
        )
        v = Validator(self.fx.root)
        fm = v.parse_frontmatter(path)
        self.assertEqual(fm["skills"], ["a", "b", "c"])
        self.assertEqual(v.errors, [])

    def test_simple_block_list_is_parsed(self):
        path = self.fx.write_file(
            "agent.md",
            "---\nname: my-agent\ndescription: test\nskills:\n  - a\n  - b\n  - c\n---\n\nBody.\n",
        )
        v = Validator(self.fx.root)
        fm = v.parse_frontmatter(path)
        self.assertEqual(fm["skills"], ["a", "b", "c"])
        self.assertEqual(v.errors, [])


class TestLocalLinks(ValidatorTestCase):
    def test_broken_local_link_is_an_error(self):
        body = MINIMAL_SKILL_MD.format(name="my-skill") + "\nSee [missing](../missing-file.md) for more.\n"
        self.fx.write_marketplace([{"name": "demo-plugin", "source": "./plugins/demo-plugin", "version": "0.1.0"}])
        self.fx.write_plugin("plugins/demo-plugin", "demo-plugin", skills={"my-skill": {"body": body}})

        v = self.run_validator()
        self.assertTrue(
            any("broken local link" in e for e in v.errors),
            msg=f"expected a broken-link error, got: {v.errors}",
        )


class TestPluginRootBoundary(ValidatorTestCase):
    def test_plugin_runtime_link_escaping_plugin_root_is_an_error(self):
        # docs/shared.md lives at the fixture repo root, i.e. outside the
        # plugin. It DOES exist in this checkout, which is exactly the
        # trap: the link must still fail, because a marketplace install
        # copies only plugins/demo-plugin/, not the file this points to.
        self.fx.write_file("docs/shared.md", "# Shared doc\n\nNot part of any plugin.\n")
        body = (
            MINIMAL_SKILL_MD.format(name="demo")
            + "\nSee [shared](../../../../docs/shared.md) for background.\n"
        )
        self.fx.write_marketplace([{"name": "demo-plugin", "source": "./plugins/demo-plugin", "version": "0.1.0"}])
        self.fx.write_plugin("plugins/demo-plugin", "demo-plugin", skills={"demo": {"body": body}})

        v = self.run_validator()
        self.assertTrue(
            any("runtime link escapes the plugin root" in e for e in v.errors),
            msg=f"expected a plugin-root-escape error, got: {v.errors}",
        )

    def test_link_within_plugin_root_passes(self):
        body = MINIMAL_SKILL_MD.format(name="demo") + "\nSee [sibling](../other-skill/SKILL.md) for more.\n"
        self.fx.write_marketplace([{"name": "demo-plugin", "source": "./plugins/demo-plugin", "version": "0.1.0"}])
        self.fx.write_plugin(
            "plugins/demo-plugin",
            "demo-plugin",
            skills={"demo": {"body": body}, "other-skill": {}},
        )
        self.fx.write_full_evals_for("demo-plugin", ["demo", "other-skill"])

        v = self.run_validator()
        self.assertEqual(v.errors, [], msg=f"unexpected errors: {v.errors}")


class TestEvals(ValidatorTestCase):
    def test_eval_referencing_unknown_plugin_skill_pair_is_an_error(self):
        self.fx.write_marketplace([{"name": "demo-plugin", "source": "./plugins/demo-plugin", "version": "0.1.0"}])
        self.fx.write_plugin("plugins/demo-plugin", "demo-plugin", skills={"sample-skill": {}})
        self.fx.write_evals(
            [make_eval("demo-plugin", "sample-skill", i) for i in range(1, 4)]
            + [make_eval("demo-plugin", "no-such-skill", 1)]
        )

        v = self.run_validator()
        self.assertTrue(
            any("unknown plugin/skill pair" in e and "no-such-skill" in e for e in v.errors),
            msg=f"expected an unknown-pair eval error, got: {v.errors}",
        )

    def test_eval_unknown_plugin_is_an_error(self):
        self.fx.write_marketplace([{"name": "demo-plugin", "source": "./plugins/demo-plugin", "version": "0.1.0"}])
        self.fx.write_plugin("plugins/demo-plugin", "demo-plugin", skills={"sample-skill": {}})
        self.fx.write_evals(
            [make_eval("demo-plugin", "sample-skill", i) for i in range(1, 4)]
            + [make_eval("some-other-plugin", "sample-skill", 1)]
        )

        v = self.run_validator()
        self.assertTrue(
            any("unknown plugin/skill pair" in e and "some-other-plugin" in e for e in v.errors),
            msg=f"expected an unknown-plugin eval error, got: {v.errors}",
        )

    def test_eval_missing_plugin_field_is_an_error(self):
        self.fx.write_marketplace([{"name": "demo-plugin", "source": "./plugins/demo-plugin", "version": "0.1.0"}])
        self.fx.write_plugin("plugins/demo-plugin", "demo-plugin", skills={"sample-skill": {}})
        eval_no_plugin = make_eval("demo-plugin", "sample-skill", 1)
        del eval_no_plugin["plugin"]
        self.fx.write_evals([eval_no_plugin])

        v = self.run_validator()
        self.assertTrue(
            any("missing fields" in e and "'plugin'" in e for e in v.errors),
            msg=f"expected a missing-plugin-field error, got: {v.errors}",
        )

    def test_fewer_than_three_evals_is_an_error(self):
        self.fx.write_marketplace([{"name": "demo-plugin", "source": "./plugins/demo-plugin", "version": "0.1.0"}])
        self.fx.write_plugin("plugins/demo-plugin", "demo-plugin", skills={"sample-skill": {}})
        self.fx.write_evals([make_eval("demo-plugin", "sample-skill", 1)])

        v = self.run_validator()
        self.assertTrue(
            any("plugin 'demo-plugin' skill 'sample-skill' has only 1 eval(s)" in e for e in v.errors),
            msg=f"expected an insufficient-evals error, got: {v.errors}",
        )

    def test_same_skill_name_in_two_plugins_has_independent_eval_coverage(self):
        self.fx.write_marketplace(
            [
                {"name": "plugin-one", "source": "./plugins/plugin-one", "version": "0.1.0"},
                {"name": "plugin-two", "source": "./plugins/plugin-two", "version": "0.1.0"},
            ]
        )
        self.fx.write_plugin("plugins/plugin-one", "plugin-one", skills={"reviewing-code": {}})
        self.fx.write_plugin("plugins/plugin-two", "plugin-two", skills={"reviewing-code": {}})
        # Only plugin-one gets 3 evals; plugin-two's same-named skill gets none.
        self.fx.write_full_evals_for("plugin-one", ["reviewing-code"])

        v = self.run_validator()
        self.assertTrue(
            any("plugin 'plugin-two' skill 'reviewing-code' has only 0 eval(s)" in e for e in v.errors),
            msg=f"expected plugin-two's reviewing-code to be reported uncovered, got: {v.errors}",
        )
        # And plugin-one's identically-named skill must NOT be flagged —
        # its 3 evals must not leak coverage to plugin-two.
        self.assertFalse(
            any("plugin 'plugin-one' skill 'reviewing-code'" in e for e in v.errors),
            msg=f"plugin-one's reviewing-code should be fully covered, got: {v.errors}",
        )
        # The old "not plugin-scoped" limitation warning must be gone entirely.
        self.assertFalse(
            any("not plugin-scoped" in w for w in v.warnings),
            msg=f"eval coverage must now be plugin-scoped with no caveat warning, got: {v.warnings}",
        )


class TestAgentSkillPreload(ValidatorTestCase):
    def test_agent_preloading_unknown_skill_is_an_error(self):
        agent_body = (
            "---\nname: my-agent\ndescription: test agent\ntools: Read, Skill\n"
            "skills: [does-not-exist]\n---\n\nBody.\n"
        )
        self.fx.write_marketplace([{"name": "demo-plugin", "source": "./plugins/demo-plugin", "version": "0.1.0"}])
        self.fx.write_plugin(
            "plugins/demo-plugin",
            "demo-plugin",
            skills={"sample-skill": {}},
            agents={"my-agent": {"body": agent_body}},
        )
        self.fx.write_full_evals_for("demo-plugin", ["sample-skill"])

        v = self.run_validator()
        self.assertTrue(
            any("preloads unknown skill" in e for e in v.errors),
            msg=f"expected an unknown-preload error, got: {v.errors}",
        )

    def test_agent_preloading_known_skill_passes(self):
        agent_body = (
            "---\nname: my-agent\ndescription: test agent\ntools: Read, Skill\n"
            "skills: [sample-skill]\n---\n\nBody.\n"
        )
        self.fx.write_marketplace([{"name": "demo-plugin", "source": "./plugins/demo-plugin", "version": "0.1.0"}])
        self.fx.write_plugin(
            "plugins/demo-plugin",
            "demo-plugin",
            skills={"sample-skill": {}},
            agents={"my-agent": {"body": agent_body}},
        )
        self.fx.write_full_evals_for("demo-plugin", ["sample-skill"])

        v = self.run_validator()
        self.assertEqual(v.errors, [], msg=f"unexpected errors: {v.errors}")

        # Preloaded skill *names* stay bare (local to the plugin), per the
        # official spec for the `skills:` frontmatter field — only the
        # Skill-tool *invocation text* in the agent's prose gets namespaced.
        # This test documents that distinction so it isn't "corrected" by
        # mistake in a future pass.


class TestLocalPluginEnumeration(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def test_lists_every_local_plugin_root(self):
        self.fx.write_marketplace(
            [
                {"name": "plugin-one", "source": "./plugins/plugin-one", "version": "0.1.0"},
                {"name": "plugin-two", "source": "./plugins/plugin-two", "version": "0.1.0"},
                {"name": "remote-plugin", "source": {"source": "github", "repo": "someone/somewhere"}, "version": "0.1.0"},
            ]
        )
        self.fx.write_plugin("plugins/plugin-one", "plugin-one")
        self.fx.write_plugin("plugins/plugin-two", "plugin-two")

        roots = list_local_plugins.list_local_plugin_roots(self.fx.root)
        # Resolve fx.root too: on Windows, tempfile can hand back a short
        # (8.3) path component while Path.resolve() elsewhere expands it,
        # which makes relative_to() raise even for the same directory.
        base = self.fx.root.resolve()
        rel = sorted(str(r.relative_to(base)).replace("\\", "/") for r in roots)
        self.assertEqual(rel, ["plugins/plugin-one", "plugins/plugin-two"])

    def test_real_repo_lists_ai_dev_team_only(self):
        roots = list_local_plugins.list_local_plugin_roots(REPO_ROOT)
        rel = sorted(str(r.relative_to(REPO_ROOT)).replace("\\", "/") for r in roots)
        self.assertEqual(rel, ["plugins/ai-dev-team"])


class TestAgentWorkflowSkillNamespacing(unittest.TestCase):
    """Regression test for the P2 finding: an agent's Skill-tool invocation
    prose must reference its mapped workflow skill as `ai-dev-team:<skill>`,
    not the bare basename, so delegation is unambiguous even when another
    installed plugin defines a same-named skill.
    """

    INVOKE_RE = re.compile(r"invoke (?:the )?`([^`]+)`")

    def test_no_agent_invokes_a_bare_unnamespaced_workflow_skill(self):
        agents_dir = REPO_ROOT / "plugins" / "ai-dev-team" / "agents"
        skills_dir = REPO_ROOT / "plugins" / "ai-dev-team" / "skills"
        known_skills = {p.name for p in skills_dir.iterdir() if p.is_dir()}
        self.assertTrue(known_skills, "expected to find at least one skill directory")

        violations = []
        for agent_file in sorted(agents_dir.glob("*.md")):
            text = agent_file.read_text(encoding="utf-8")
            for match in self.INVOKE_RE.finditer(text):
                token = match.group(1)
                if token in known_skills:
                    violations.append(f"{agent_file.name}: invokes bare `{token}` instead of `ai-dev-team:{token}`")

        self.assertEqual(violations, [], msg="\n".join(violations))

    def test_workflow_agents_do_namespace_their_mapped_skill(self):
        """Sanity check the regex itself isn't vacuously passing (e.g. because
        nothing matched at all)."""
        backend_engineer = (REPO_ROOT / "plugins" / "ai-dev-team" / "agents" / "backend-engineer.md").read_text(
            encoding="utf-8"
        )
        matches = self.INVOKE_RE.findall(backend_engineer)
        self.assertTrue(
            any(m == "ai-dev-team:implementing-features" for m in matches),
            msg=f"expected backend-engineer to invoke ai-dev-team:implementing-features, matches were: {matches}",
        )


class TestPackagingBoundary(unittest.TestCase):
    """Simulates what Claude Code actually does when installing a plugin
    from a marketplace: copy the plugin directory alone, nothing else from
    the repo. This is the exact scenario the P1 packaging finding described
    and that passed the first two rounds of CI unnoticed, because the full
    monorepo checkout made every relative link resolve locally.
    """

    def test_plugin_is_self_contained_when_copied(self):
        plugin_src = REPO_ROOT / "plugins" / "ai-dev-team"
        with tempfile.TemporaryDirectory() as tmp:
            copied_root = Path(tmp) / "ai-dev-team"
            shutil.copytree(plugin_src, copied_root)

            broken = []
            for md in sorted(copied_root.rglob("*.md")):
                text = md.read_text(encoding="utf-8")
                for match in MD_LINK_RE.finditer(text):
                    target = match.group(1)
                    if target.startswith(("http://", "https://", "mailto:")):
                        continue
                    resolved = (md.parent / target).resolve()
                    if not resolved.exists():
                        broken.append(f"{md.relative_to(copied_root)} -> {target}")
                    else:
                        try:
                            resolved.relative_to(copied_root.resolve())
                        except ValueError:
                            broken.append(
                                f"{md.relative_to(copied_root)} -> {target} "
                                f"(resolves outside the copied plugin, so it wasn't copied)"
                            )

            self.assertEqual(
                broken,
                [],
                msg=(
                    "plugin is not self-contained when copied in isolation "
                    "(as a real marketplace install would copy it):\n" + "\n".join(broken)
                ),
            )


class TestRealRepo(unittest.TestCase):
    """Sanity check: the real repo this script ships in must also pass."""

    def test_real_repo_passes(self):
        v = Validator(REPO_ROOT)
        v.run()
        self.assertEqual(v.errors, [], msg=f"real repo has validator errors: {v.errors}")
        self.assertEqual(v.warnings, [], msg=f"real repo has validator warnings: {v.warnings}")


if __name__ == "__main__":
    unittest.main()
