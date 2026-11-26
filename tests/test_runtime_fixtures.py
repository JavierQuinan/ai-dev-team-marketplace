import subprocess
import tempfile
import unittest
from pathlib import Path
from scripts.create_runtime_fixtures import create, SCENARIOS

class FixtureTests(unittest.TestCase):
    def test_reproducible_baselines(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b=Path(tmp)/"a",Path(tmp)/"b"
            first,second=create(a),create(b)
            self.assertEqual(first,second)
            self.assertEqual(set(first),set(SCENARIOS))
            for scenario in first:
                self.assertEqual(subprocess.check_output(["git","status","--porcelain"],cwd=a/scenario,text=True),"")
                self.assertTrue((a/scenario/"TASK.md").is_file())
            with self.assertRaises(FileExistsError):
                create(a)

    def test_baseline_regressions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"fixtures"
            create(root)
            for scenario,expected in [("small",1),("full-stack",1),("security",1),("api-only",0),("migration",0)]:
                import sys
                run=subprocess.run([sys.executable,"-m","unittest","discover","-v"],cwd=root/scenario,capture_output=True,text=True)
                self.assertEqual(run.returncode,expected,run.stderr)
                self.assertIn("Ran 1 test",run.stderr)

if __name__=="__main__":
    unittest.main()
