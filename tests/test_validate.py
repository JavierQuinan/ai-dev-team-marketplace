#!/usr/bin/env python3
"""Deterministic tests for scripts/validate.py.

Standard-library only (unittest + tempfile). Each test builds a minimal,
throwaway fixture repository under a temp directory and runs a fresh
Validator against it, so these tests never depend on the state of the real
ai-dev-team-marketplace repo and never leak errors/warnings between cases.

Usage:
    python tests/test_validate.py
    python -m unittest tests.test_validate -v
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "validate.py"
_spec = importlib.util.spec_from_file_location("validate", _SCRIPT_PATH)
validate = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(validate)
Validator = validate.Validator


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


def make_eval(skill: str, idx: int) -> dict:
    return {
        "id": f"{skill}-{idx:02d}",
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

    def write_full_evals_for(self, skill_names: list[str]) -> None:
        evals = [make_eval(s, i) for s in skill_names for i in range(1, 4)]
        self.write_evals(evals)


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
        self.fx.write_full_evals_for(["sample-skill"])

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
        self.fx.write_full_evals_for(["skill-a", "skill-b"])

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
        self.fx.write_full_evals_for(["sample-skill"])

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


class TestEvals(ValidatorTestCase):
    def test_eval_referencing_missing_skill_is_an_error(self):
        self.fx.write_marketplace([{"name": "demo-plugin", "source": "./plugins/demo-plugin", "version": "0.1.0"}])
        self.fx.write_plugin("plugins/demo-plugin", "demo-plugin", skills={"sample-skill": {}})
        self.fx.write_evals([make_eval("sample-skill", i) for i in range(1, 4)] + [make_eval("no-such-skill", 1)])

        v = self.run_validator()
        self.assertTrue(
            any("unknown skill 'no-such-skill'" in e for e in v.errors),
            msg=f"expected an unknown-skill eval error, got: {v.errors}",
        )

    def test_fewer_than_three_evals_is_an_error(self):
        self.fx.write_marketplace([{"name": "demo-plugin", "source": "./plugins/demo-plugin", "version": "0.1.0"}])
        self.fx.write_plugin("plugins/demo-plugin", "demo-plugin", skills={"sample-skill": {}})
        self.fx.write_evals([make_eval("sample-skill", 1)])

        v = self.run_validator()
        self.assertTrue(
            any("has only 1 eval(s)" in e for e in v.errors),
            msg=f"expected an insufficient-evals error, got: {v.errors}",
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
        self.fx.write_full_evals_for(["sample-skill"])

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
        self.fx.write_full_evals_for(["sample-skill"])

        v = self.run_validator()
        self.assertEqual(v.errors, [], msg=f"unexpected errors: {v.errors}")


class TestRealRepo(unittest.TestCase):
    """Sanity check: the real repo this script ships in must also pass."""

    def test_real_repo_passes(self):
        repo_root = Path(__file__).resolve().parent.parent
        v = Validator(repo_root)
        v.run()
        self.assertEqual(v.errors, [], msg=f"real repo has validator errors: {v.errors}")


if __name__ == "__main__":
    unittest.main()
