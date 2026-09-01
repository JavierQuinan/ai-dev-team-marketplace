#!/usr/bin/env python3
"""Validates the ai-dev-team-marketplace repository structure.

Standard-library only (no external dependencies). Iterates every plugin
declared in .claude-plugin/marketplace.json (multi-plugin aware — does not
hardcode any single plugin name or path) and, for each one resolvable to a
local directory inside this repo, validates its plugin.json, every skill's
SKILL.md frontmatter, every agent's frontmatter, local file references, and
the tests/evals/*.json schema.

This script is a *complement* to the official `claude plugin validate`
command, not a replacement for it. It only checks invariants specific to
this repository's own conventions (skill `name` == directory name, eval
schema, cross-file link integrity, per-skill eval coverage). The official
CLI is the authority on the actual plugin/marketplace/frontmatter schema —
see "What this validator does NOT check" below and
docs/architecture/token-efficiency.md#frontmatter-validation.

Usage:
    python scripts/validate.py [root]

`root` defaults to the repository root (two levels up from this file) and
exists so tests can point this module at a temporary fixture directory
instead of the real repo.

Exit code is non-zero if any error is found. Warnings do not affect the
exit code but are always printed.

What this validator does NOT check (by design — see Option A in the ADR):
    - Full JSON-Schema-level correctness of marketplace.json / plugin.json
      (field types, allowed enum values, unknown-key detection). Run
      `claude plugin validate .` for that.
    - Any YAML beyond three shapes: flat `key: value`, a single-line inline
      list `key: [a, b]`, and a simple block-style list (`key:` on its own
      line followed by `  - item` lines). Nested maps, multi-line strings,
      anchors/aliases, and mixed-style values are not parsed; see
      `Validator.parse_frontmatter` for the exact subset. None of this
      repo's own skills/agents currently need anything beyond that subset,
      by convention.
    - Whether a skill/agent actually behaves as described. That's what
      tests/evals/ and manual testing are for.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MD_LINK_RE = re.compile(r"\]\(([^)#\s]+)")
INLINE_LIST_RE = re.compile(r"^\[(.*)\]$")

REQUIRED_EVAL_FIELDS = (
    "id",
    "plugin",
    "skill",
    "scenario",
    "query",
    "expected_behavior",
    "forbidden_behavior",
    "evidence_required",
)


class Validator:
    """Holds validation state for one run against one repo root.

    Instantiated fresh per run (or per test) so errors/warnings never leak
    between independent validations.
    """

    def __init__(self, root: Path):
        self.root = root
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    def load_json(self, path: Path, *, label: str | None = None) -> dict | list | None:
        label = label or self.rel(path)
        if not path.exists():
            self.error(f"missing required file: {label}")
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self.error(f"invalid JSON in {label}: {exc}")
            return None

    def parse_frontmatter(self, path: Path) -> dict[str, object] | None:
        """Minimal frontmatter parser supporting exactly three shapes:

        1. Flat scalar: `key: value`
        2. Inline list: `key: [a, b, c]` (single line)
        3. Simple block list:
               key:
                 - a
                 - b

        Anything else — nested maps, multi-line strings, YAML anchors,
        a block list mixed with other content under the same key — is not
        supported: a line that doesn't match one of the three shapes above
        is skipped with a warning, not silently misparsed. See the module
        docstring's "What this validator does NOT check" section.
        """
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        label = self.rel(path)
        if not lines or lines[0].strip() != "---":
            self.error(f"{label}: file must start with '---' frontmatter delimiter")
            return None
        try:
            end = lines[1:].index("---") + 1
        except ValueError:
            self.error(f"{label}: unterminated frontmatter (no closing '---')")
            return None

        fm: dict[str, object] = {}
        pending_list_key: str | None = None
        for raw in lines[1:end]:
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if pending_list_key is not None and stripped.startswith("- "):
                if not isinstance(fm.get(pending_list_key), list):
                    fm[pending_list_key] = []
                fm[pending_list_key].append(stripped[2:].strip().strip('"').strip("'"))
                continue
            pending_list_key = None
            if ":" not in raw:
                self.warn(f"{label}: unparsed frontmatter line (not key: value): {raw!r}")
                continue
            key, _, value = raw.partition(":")
            key = key.strip()
            value = value.strip()
            if not value:
                # Could be the start of a block-style list (`key:` then `  - item`
                # lines) or a genuinely empty scalar. Assume block-list start;
                # if no `- ` lines follow, it resolves to an empty string below.
                pending_list_key = key
                fm[key] = ""
                continue
            inline_list = INLINE_LIST_RE.match(value)
            if inline_list:
                items = [i.strip().strip('"').strip("'") for i in inline_list.group(1).split(",") if i.strip()]
                fm[key] = items
            else:
                fm[key] = value.strip('"').strip("'")
        return fm

    def check_local_links(self, path: Path, *, plugin_root: Path | None = None) -> None:
        """Check that every local (non-http) markdown link in `path` resolves.

        When `plugin_root` is given, `path` is understood to be a *runtime*
        file belonging to that plugin (a SKILL.md or an agent file) — a link
        that resolves to a real file in this checkout but outside
        `plugin_root` is still an error, because Claude Code copies only the
        plugin's own directory into the plugin cache when installing from a
        marketplace. A link that exists in this monorepo checkout but points
        outside the plugin will 404 for anyone who installed the plugin
        rather than cloned the whole marketplace repo.
        """
        text = path.read_text(encoding="utf-8")
        resolved_plugin_root = plugin_root.resolve() if plugin_root is not None else None
        for match in MD_LINK_RE.finditer(text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                self.error(f"{self.rel(path)}: broken local link -> {target}")
                continue
            if resolved_plugin_root is not None:
                try:
                    resolved.relative_to(resolved_plugin_root)
                except ValueError:
                    self.error(
                        f"{self.rel(path)}: runtime link escapes the plugin root -> {target} "
                        f"(exists in this checkout but plugin installs copy only the plugin's own "
                        f"directory, so this reference would be broken after install)"
                    )

    # -- marketplace -----------------------------------------------------

    def validate_marketplace(self) -> dict | None:
        mp_path = self.root / ".claude-plugin" / "marketplace.json"
        mp = self.load_json(mp_path)
        if mp is None:
            return None
        if not isinstance(mp, dict):
            self.error("marketplace.json: top-level value must be an object")
            return None

        for field in ("name", "owner", "plugins"):
            if field not in mp:
                self.error(f"marketplace.json: missing required field '{field}'")
        if isinstance(mp.get("owner"), dict) and "name" not in mp["owner"]:
            self.error("marketplace.json: owner.name is required")
        if "name" in mp and isinstance(mp["name"], str) and not NAME_RE.match(mp["name"]):
            self.error(f"marketplace.json: name '{mp['name']}' is not kebab-case")

        plugins = mp.get("plugins", [])
        if not isinstance(plugins, list) or not plugins:
            self.error("marketplace.json: plugins must be a non-empty array")
            return mp

        seen_names: set[str] = set()
        for entry in plugins:
            if not isinstance(entry, dict):
                self.error("marketplace.json: a plugin entry is not an object")
                continue
            pname = entry.get("name")
            if not pname:
                self.error("marketplace.json: a plugin entry is missing 'name'")
                continue
            if pname in seen_names:
                self.error(f"marketplace.json: duplicate plugin name '{pname}'")
            seen_names.add(pname)
            if "source" not in entry:
                self.error(f"marketplace.json: plugin '{pname}' is missing 'source'")

        return mp

    def resolve_local_plugin_root(self, entry: dict) -> Path | None:
        """Resolve a marketplace plugin entry's local source to a directory
        inside this repo. Returns None (no error) for non-local sources
        (github/url/git-subdir/npm/archive/command) — those aren't
        validatable against this checkout.
        """
        name = entry.get("name", "?")
        source = entry.get("source")
        if not isinstance(source, str):
            return None  # remote/dynamic source: out of scope for local validation
        resolved = (self.root / source).resolve()
        try:
            resolved.relative_to(self.root.resolve())
        except ValueError:
            self.error(f"marketplace.json: plugin '{name}' source escapes the repository root: {source}")
            return None
        if not resolved.exists():
            self.error(f"marketplace.json: plugin '{name}' source path does not exist: {source}")
            return None
        return resolved

    # -- plugin ------------------------------------------------------------

    def validate_plugin(self, entry: dict, plugin_root: Path, marketplace: dict) -> dict | None:
        name = entry.get("name", "?")
        plugin_json_path = plugin_root / ".claude-plugin" / "plugin.json"
        plugin = self.load_json(plugin_json_path, label=f"{name}: {self.rel(plugin_json_path)}")
        if plugin is None:
            return None
        if not isinstance(plugin, dict):
            self.error(f"plugin '{name}': plugin.json top-level value must be an object")
            return None

        if "name" not in plugin:
            self.error(f"plugin '{name}': plugin.json is missing required field 'name'")
        elif not NAME_RE.match(str(plugin["name"])):
            self.error(f"plugin '{name}': plugin.json name '{plugin['name']}' is not kebab-case")
        elif plugin["name"] != name:
            self.error(
                f"plugin '{name}': marketplace.json entry name does not match "
                f"plugin.json name '{plugin['name']}'"
            )

        mp_version = entry.get("version")
        plugin_version = plugin.get("version")
        if mp_version and plugin_version and mp_version != plugin_version:
            self.error(
                f"plugin '{name}': version mismatch — marketplace.json entry version "
                f"'{mp_version}' != plugin.json version '{plugin_version}'"
            )

        return plugin

    # -- skills --------------------------------------------------------------

    def validate_skills(self, plugin_name: str, plugin_root: Path) -> set[str]:
        skills_dir = plugin_root / "skills"
        if not skills_dir.exists():
            self.warn(f"plugin '{plugin_name}': no skills/ directory found")
            return set()

        names: set[str] = set()
        fm_names: set[str] = set()
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            dir_name = skill_dir.name
            if not NAME_RE.match(dir_name):
                self.error(f"plugin '{plugin_name}': skill directory '{dir_name}' is not kebab-case")
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                self.error(f"plugin '{plugin_name}': skill '{dir_name}' is missing SKILL.md")
                continue

            if dir_name in names:
                self.error(f"plugin '{plugin_name}': duplicate skill directory name '{dir_name}'")
            names.add(dir_name)

            fm = self.parse_frontmatter(skill_md)
            if fm is not None:
                fm_name = fm.get("name")
                if not fm_name:
                    self.error(f"skill '{dir_name}': frontmatter 'name' is required in this repo (falls back to the directory name per the Claude Code spec, but an explicit, matching name is required here so a mismatch is never silent)")
                elif not isinstance(fm_name, str) or not NAME_RE.match(fm_name):
                    self.error(f"skill '{dir_name}': frontmatter name '{fm_name}' is not kebab-case")
                else:
                    if fm_name != dir_name:
                        self.error(
                            f"skill '{dir_name}': frontmatter name '{fm_name}' does not match its "
                            f"directory name — this changes the effective command name silently"
                        )
                    if fm_name in fm_names:
                        self.error(f"plugin '{plugin_name}': duplicate skill frontmatter name '{fm_name}'")
                    fm_names.add(fm_name)

                description = fm.get("description", "")
                when_to_use = fm.get("when_to_use", "")
                if not description:
                    self.error(f"skill '{dir_name}': frontmatter 'description' is empty or missing")
                elif isinstance(description, str) and isinstance(when_to_use, str):
                    combined = len(description) + len(when_to_use)
                    if combined > 1536:
                        self.warn(
                            f"skill '{dir_name}': description + when_to_use is {combined} chars, "
                            f"exceeds the 1536-character listing cap and will be truncated"
                        )

            line_count = len(skill_md.read_text(encoding="utf-8").splitlines())
            if line_count > 500:
                self.error(f"skill '{dir_name}': SKILL.md is {line_count} lines, exceeds the 500-line official guidance")
            elif line_count > 250:
                self.warn(f"skill '{dir_name}': SKILL.md is {line_count} lines, exceeds this repo's 250-line target")

            self.check_local_links(skill_md, plugin_root=plugin_root)

        return names

    # -- agents ----------------------------------------------------------

    def validate_agents(self, plugin_name: str, plugin_root: Path, skill_names: set[str]) -> set[str]:
        agents_dir = plugin_root / "agents"
        if not agents_dir.exists():
            self.warn(f"plugin '{plugin_name}': no agents/ directory found")
            return set()

        names: set[str] = set()
        for agent_file in sorted(agents_dir.glob("*.md")):
            fm = self.parse_frontmatter(agent_file)
            if fm is None:
                continue
            name = fm.get("name")
            if not name:
                self.error(f"agent '{agent_file.name}': frontmatter 'name' is required")
                continue
            if not isinstance(name, str) or not NAME_RE.match(name):
                self.error(f"agent '{agent_file.name}': name '{name}' is not kebab-case")
            if name in names:
                self.error(f"plugin '{plugin_name}': duplicate agent name '{name}'")
            names.add(str(name))
            if not fm.get("description"):
                self.error(f"agent '{name}': frontmatter 'description' is required")

            preloaded = fm.get("skills")
            if isinstance(preloaded, list):
                for skill_ref in preloaded:
                    if skill_ref not in skill_names:
                        self.error(
                            f"agent '{name}': preloads unknown skill '{skill_ref}' "
                            f"(not found under {plugin_name}'s skills/)"
                        )

            self.check_local_links(agent_file, plugin_root=plugin_root)

        return names

    # -- evals -------------------------------------------------------------

    def validate_evals(self, all_plugin_skill_pairs: set[tuple[str, str]]) -> None:
        """Validate tests/evals/*.json against the known (plugin, skill) pairs.

        Eval identity is scoped by (plugin, skill), not bare skill name,
        because two different plugins may legitimately publish a skill with
        the same basename (their effective identity is namespaced by
        plugin). Without this, evals for plugin-a's `reviewing-code` could
        silently satisfy the coverage requirement for plugin-b's
        `reviewing-code`.
        """
        evals_dir = self.root / "tests" / "evals"
        if not evals_dir.exists():
            self.error(f"missing evals directory: {self.rel(evals_dir)}")
            return

        eval_files = sorted(evals_dir.glob("*.json"))
        if not eval_files:
            self.error("tests/evals/ contains no eval files")
            return

        seen_ids: set[str] = set()
        per_pair_count: dict[tuple[str, str], int] = {pair: 0 for pair in all_plugin_skill_pairs}

        for path in eval_files:
            data = self.load_json(path)
            if data is None:
                continue
            entries = data if isinstance(data, list) else [data]
            for entry in entries:
                if not isinstance(entry, dict):
                    self.error(f"{self.rel(path)}: eval entry is not an object")
                    continue
                missing = [f for f in REQUIRED_EVAL_FIELDS if not entry.get(f)]
                if missing:
                    self.error(f"{self.rel(path)}: eval '{entry.get('id', '?')}' missing fields: {missing}")
                    continue
                eid = entry["id"]
                if eid in seen_ids:
                    self.error(f"{self.rel(path)}: duplicate eval id '{eid}'")
                seen_ids.add(eid)
                pair = (entry["plugin"], entry["skill"])
                if pair not in all_plugin_skill_pairs:
                    self.error(
                        f"{self.rel(path)}: eval '{eid}' references unknown plugin/skill pair "
                        f"('{pair[0]}', '{pair[1]}')"
                    )
                else:
                    per_pair_count[pair] = per_pair_count.get(pair, 0) + 1

        for (plugin_name, skill), count in per_pair_count.items():
            if count < 3:
                self.error(
                    f"plugin '{plugin_name}' skill '{skill}' has only {count} eval(s); at least 3 are required"
                )

    # -- top level ---------------------------------------------------------

    def run(self) -> int:
        marketplace = self.validate_marketplace()
        all_plugin_skill_pairs: set[tuple[str, str]] = set()

        if marketplace is not None:
            for entry in marketplace.get("plugins", []):
                if not isinstance(entry, dict) or not entry.get("name"):
                    continue
                plugin_root = self.resolve_local_plugin_root(entry)
                if plugin_root is None:
                    continue  # remote source, or already reported as an error
                plugin = self.validate_plugin(entry, plugin_root, marketplace)
                if plugin is None:
                    continue
                skill_names = self.validate_skills(entry["name"], plugin_root)
                all_plugin_skill_pairs |= {(entry["name"], s) for s in skill_names}
                self.validate_agents(entry["name"], plugin_root, skill_names)

        if all_plugin_skill_pairs:
            self.validate_evals(all_plugin_skill_pairs)
        else:
            self.error("cannot validate evals: no skills were discovered in any local plugin")

        for w in self.warnings:
            print(f"WARNING: {w}")
        for e in self.errors:
            print(f"ERROR: {e}")

        print(f"\n{len(self.errors)} error(s), {len(self.warnings)} warning(s).")
        return 1 if self.errors else 0


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path(__file__).resolve().parent.parent
    return Validator(root).run()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
