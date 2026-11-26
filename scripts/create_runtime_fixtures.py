"""Create disposable, deterministic scenario repositories without network or model calls."""
import argparse
import json
import os
from pathlib import Path
import subprocess

SCENARIOS = {
    "small": ("Repair the total function and add a regression test.", {"app.py": "def total(a, b):\n    return a - b\n", "test_app.py": "import unittest\nfrom app import total\nclass Test(unittest.TestCase):\n    def test_total(self):\n        self.assertEqual(total(2, 3), 5)\n"}),
    "ui-only": ("Improve the existing static UI loading and empty states; API is unchanged.", {"ui/index.html": "<main><h1>Customers</h1><div id='status'></div></main>\n", "ui/styles.css": "main { max-width: 60rem; margin: auto; }\n"}),
    "api-only": ("Add validation to the existing profile function without a UI or schema change.", {"api.py": "def profile(name):\n    return {'name': name}\n", "test_api.py": "import unittest\nfrom api import profile\nclass Test(unittest.TestCase):\n    def test_profile(self):\n        self.assertEqual(profile('Ada'), {'name': 'Ada'})\n"}),
    "full-stack": ("Implement profile name display; freeze the shared API shape before dependent edits and verify the regression.", {"api/profile.py": "def profile():\n    return {'name': 'Ada'}\n", "ui/profile.py": "def render(data):\n    return data['displayName']\n", "test_profile.py": "import unittest\nfrom api.profile import profile\nfrom ui.profile import render\nclass Test(unittest.TestCase):\n    def test_profile(self):\n        self.assertEqual(render(profile()), 'Ada')\n"}),
    "security": ("Repair the synthetic cross-tenant authorization flaw; verify independent security review.", {"app.py": "def visible(rows, tenant):\n    return rows\n", "test_app.py": "import unittest\nfrom app import visible\nclass Test(unittest.TestCase):\n    def test_isolation(self):\n        self.assertEqual(visible([{'tenant':'a'},{'tenant':'b'}], 'a'), [{'tenant':'a'}])\n"}),
    "migration": ("Plan and test a reversible SQLite migration in a disposable local database only.", {"schema.sql": "CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL);\n", "test_schema.py": "import sqlite3, unittest\nfrom pathlib import Path\nclass Test(unittest.TestCase):\n    def test_schema(self):\n        with sqlite3.connect(':memory:') as db:\n            db.executescript(Path('schema.sql').read_text())\n            db.execute(\"INSERT INTO customers VALUES (1, 'Ada')\")\n            self.assertEqual(db.execute('SELECT name FROM customers').fetchone(), ('Ada',))\n"}),
    "ambiguous": ("A profile request leaves the response field name unresolved. Investigate and stop before dependent writes.", {"api.py": "def profile():\n    return {'name': 'Ada'}\n", "DECISIONS.md": "Open question: should the new response use name or displayName? No decision yet.\n"}),
}

def create(root):
    root.mkdir(parents=False, exist_ok=False)
    result = {}
    env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
           "GIT_AUTHOR_DATE": "2020-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2020-01-01T00:00:00Z"}
    for key, (prompt, files) in SCENARIOS.items():
        repo = root / key
        repo.mkdir()
        for name, body in {**files, "TASK.md": prompt + "\n"}.items():
            path = repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8", newline="\n")
        def git(*args):
            return subprocess.check_output(["git", "-c", "core.hooksPath=" + os.devnull, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", *args], cwd=repo, env=env, text=True).strip()
        git("init", "--initial-branch=main", "--template=")
        git("add", "--", ".")
        git("commit", "--no-gpg-sign", "-m", "Synthetic baseline")
        result[key] = {"fixture_sha": git("rev-parse", "HEAD"), "prompt": prompt}
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New directory outside the plugin checkout")
    args = parser.parse_args()
    print(json.dumps(create(args.output.resolve()), indent=2))
