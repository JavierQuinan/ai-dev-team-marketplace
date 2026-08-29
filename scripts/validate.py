#!/usr/bin/env python3
"""Validates the ai-dev-team-marketplace repository structure.

Standard-library only (no external dependencies). Checks marketplace.json,
plugin.json, every SKILL.md and agent file's frontmatter, local file
references, and the tests/evals/*.json schema.

Usage:
    python scripts/validate.py

Exit code is non-zero if any error is found. Warnings do not affect the
exit code but are always printed.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MD_LINK_RE = re.compile(r"\]\(([^)#\s]+)")

errors: list[str] = []
warnings: list[str] = []


def error(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def load_json(path: Path) -> dict | None:
    if not path.exists():
        error(f"missing required file: {path.relative_to(ROOT)}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        error(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
        return None


def parse_frontmatter(path: Path) -> dict[str, str] | None:
    """Minimal flat key: value YAML frontmatter parser.

    Sufficient for this repo's frontmatter, which never nests lists/maps.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        error(f"{path.relative_to(ROOT)}: file must start with '---' frontmatter delimiter")
        return None
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        error(f"{path.relative_to(ROOT)}: unterminated frontmatter (no closing '---')")
        return None
    fm: dict[str, str] = {}
    for raw in lines[1:end]:
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        if ":" not in raw:
            warn(f"{path.relative_to(ROOT)}: unparsed frontmatter line: {raw!r}")
            continue
        key, _, value = raw.partition(":")
        fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm


def check_local_links(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for match in MD_LINK_RE.finditer(text):
        target = match.group(1)
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (path.parent / target).resolve()
        if not resolved.exists():
            error(f"{path.relative_to(ROOT)}: broken local link -> {target}")


def validate_marketplace() -> dict | None:
    mp_path = ROOT / ".claude-plugin" / "marketplace.json"
    mp = load_json(mp_path)
    if mp is None:
        return None

    for field in ("name", "owner", "plugins"):
        if field not in mp:
            error(f"marketplace.json: missing required field '{field}'")
    if "owner" in mp and "name" not in mp.get("owner", {}):
        error("marketplace.json: owner.name is required")
    if "name" in mp and not NAME_RE.match(mp["name"]):
        error(f"marketplace.json: name '{mp['name']}' is not kebab-case")

    plugins = mp.get("plugins", [])
    if not isinstance(plugins, list) or not plugins:
        error("marketplace.json: plugins must be a non-empty array")

    seen_names = set()
    for entry in plugins:
        pname = entry.get("name")
        if not pname:
            error("marketplace.json: a plugin entry is missing 'name'")
            continue
        if pname in seen_names:
            error(f"marketplace.json: duplicate plugin name '{pname}'")
        seen_names.add(pname)
        if "source" not in entry:
            error(f"marketplace.json: plugin '{pname}' is missing 'source'")
        elif isinstance(entry["source"], str):
            src = (ROOT / entry["source"]).resolve()
            if not src.exists():
                error(f"marketplace.json: plugin '{pname}' source path does not exist: {entry['source']}")

    return mp


def validate_plugin(marketplace: dict) -> tuple[Path | None, dict | None]:
    plugin_root = ROOT / "plugins" / "ai-dev-team"
    plugin_json_path = plugin_root / ".claude-plugin" / "plugin.json"
    plugin = load_json(plugin_json_path)
    if plugin is None:
        return None, None

    if "name" not in plugin:
        error("plugin.json: missing required field 'name'")
    elif not NAME_RE.match(plugin["name"]):
        error(f"plugin.json: name '{plugin['name']}' is not kebab-case")

    mp_entry = next((p for p in marketplace.get("plugins", []) if p.get("name") == plugin.get("name")), None)
    if mp_entry is None:
        error(f"plugin.json name '{plugin.get('name')}' has no matching entry in marketplace.json")
    else:
        mp_version = mp_entry.get("version")
        plugin_version = plugin.get("version")
        if mp_version and plugin_version and mp_version != plugin_version:
            error(
                f"version mismatch: marketplace.json plugin entry version '{mp_version}' "
                f"!= plugin.json version '{plugin_version}'"
            )

    return plugin_root, plugin


def validate_skills(plugin_root: Path) -> set[str]:
    skills_dir = plugin_root / "skills"
    if not skills_dir.exists():
        error(f"missing skills directory: {skills_dir.relative_to(ROOT)}")
        return set()

    names: set[str] = set()
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        dir_name = skill_dir.name
        if not NAME_RE.match(dir_name):
            error(f"skill directory '{dir_name}' is not kebab-case")
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            error(f"skill '{dir_name}' is missing SKILL.md")
            continue

        if dir_name in names:
            error(f"duplicate skill name '{dir_name}'")
        names.add(dir_name)

        fm = parse_frontmatter(skill_md)
        if fm is not None:
            description = fm.get("description", "")
            if not description:
                error(f"skill '{dir_name}': frontmatter 'description' is empty or missing")
            elif len(description) > 1536:
                warn(f"skill '{dir_name}': description exceeds the 1536-character listing cap")

        line_count = len(skill_md.read_text(encoding="utf-8").splitlines())
        if line_count > 500:
            error(f"skill '{dir_name}': SKILL.md is {line_count} lines, exceeds the 500-line official guidance")
        elif line_count > 250:
            warn(f"skill '{dir_name}': SKILL.md is {line_count} lines, exceeds this repo's 250-line target")

        check_local_links(skill_md)

    return names


def validate_agents(plugin_root: Path) -> set[str]:
    agents_dir = plugin_root / "agents"
    if not agents_dir.exists():
        warn(f"no agents directory found at {agents_dir.relative_to(ROOT)}")
        return set()

    names: set[str] = set()
    for agent_file in sorted(agents_dir.glob("*.md")):
        fm = parse_frontmatter(agent_file)
        if fm is None:
            continue
        name = fm.get("name")
        if not name:
            error(f"agent '{agent_file.name}': frontmatter 'name' is required")
            continue
        if not NAME_RE.match(name):
            error(f"agent '{agent_file.name}': name '{name}' is not kebab-case")
        if name in names:
            error(f"duplicate agent name '{name}'")
        names.add(name)
        if not fm.get("description"):
            error(f"agent '{name}': frontmatter 'description' is required")
        check_local_links(agent_file)

    return names


REQUIRED_EVAL_FIELDS = ("id", "skill", "scenario", "query", "expected_behavior", "forbidden_behavior", "evidence_required")


def validate_evals(skill_names: set[str]) -> None:
    evals_dir = ROOT / "tests" / "evals"
    if not evals_dir.exists():
        error(f"missing evals directory: {evals_dir.relative_to(ROOT)}")
        return

    eval_files = sorted(evals_dir.glob("*.json"))
    if not eval_files:
        error("tests/evals/ contains no eval files")
        return

    seen_ids: set[str] = set()
    per_skill_count: dict[str, int] = {name: 0 for name in skill_names}

    for path in eval_files:
        data = load_json(path)
        if data is None:
            continue
        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            if not isinstance(entry, dict):
                error(f"{path.relative_to(ROOT)}: eval entry is not an object")
                continue
            missing = [f for f in REQUIRED_EVAL_FIELDS if f not in entry or not entry[f]]
            if missing:
                error(f"{path.relative_to(ROOT)}: eval '{entry.get('id', '?')}' missing fields: {missing}")
                continue
            eid = entry["id"]
            if eid in seen_ids:
                error(f"{path.relative_to(ROOT)}: duplicate eval id '{eid}'")
            seen_ids.add(eid)
            skill = entry["skill"]
            if skill not in skill_names:
                error(f"{path.relative_to(ROOT)}: eval '{eid}' references unknown skill '{skill}'")
            else:
                per_skill_count[skill] = per_skill_count.get(skill, 0) + 1

    for skill, count in per_skill_count.items():
        if count < 3:
            error(f"skill '{skill}' has only {count} eval(s); at least 3 are required")


def main() -> int:
    marketplace = validate_marketplace()
    skill_names: set[str] = set()
    if marketplace is not None:
        plugin_root, plugin = validate_plugin(marketplace)
        if plugin_root is not None and plugin is not None:
            skill_names = validate_skills(plugin_root)
            validate_agents(plugin_root)

    if skill_names:
        validate_evals(skill_names)
    else:
        error("cannot validate evals: no skills were discovered")

    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")

    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
