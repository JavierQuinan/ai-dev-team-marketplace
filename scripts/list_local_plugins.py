#!/usr/bin/env python3
"""Lists every locally-resolvable plugin declared in marketplace.json.

Reuses Validator.resolve_local_plugin_root (from validate.py) rather than
re-implementing source resolution, so this and the main validator can never
drift on what counts as a valid local plugin path.

Prints one plugin root per line, as a path relative to `root` (POSIX-style
forward slashes, for portability in a bash CI loop). A plugin whose source
is remote (github/url/npm/archive/command) or that fails to resolve is
silently skipped here — scripts/validate.py is what reports resolution
errors; this script exists purely for CI/shell enumeration.

Usage:
    python scripts/list_local_plugins.py [root]

Example (bash):
    while IFS= read -r plugin_root; do
      claude plugin validate "$plugin_root" --strict
    done < <(python scripts/list_local_plugins.py)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Import the sibling module by path rather than package-relative import,
# since scripts/ is not a package (mirrors tests/test_validate.py).
import importlib.util

_spec = importlib.util.spec_from_file_location("validate", Path(__file__).resolve().parent / "validate.py")
_validate = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_validate)
Validator = _validate.Validator


def list_local_plugin_roots(root: Path) -> list[Path]:
    v = Validator(root)
    marketplace = v.validate_marketplace()
    if marketplace is None:
        return []
    roots: list[Path] = []
    for entry in marketplace.get("plugins", []):
        if not isinstance(entry, dict) or not entry.get("name"):
            continue
        plugin_root = v.resolve_local_plugin_root(entry)
        if plugin_root is not None:
            roots.append(plugin_root)
    return roots


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path(__file__).resolve().parent.parent
    for plugin_root in list_local_plugin_roots(root):
        try:
            rel = plugin_root.relative_to(root)
        except ValueError:
            rel = plugin_root
        print(rel.as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
