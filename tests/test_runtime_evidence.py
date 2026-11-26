import unittest
from scripts.runtime_evidence import verify

def trace(scenario="full-stack"):
    stages = ["DESIGN","CONTRACT-FREEZE","IMPLEMENT","TEST","REVIEW","FIX","VERIFY","REPORT"]
    events = [{"kind":"stage","stage":s,"unresolved":[]} for s in stages]
    events.insert(3,{"kind":"mutation"})
    events.insert(-1,{"kind":"check","id":"regression","required":True,"status":"PASS","exit_code":0})
    return {"scenario":scenario,"trial_id":"synthetic-1","claude_version":"synthetic",
            "plugin_version":"candidate","model":"synthetic","fixture_sha":"a"*40,
            "target_sha":"b"*40,"transcript_digest":"sha256:"+"c"*64,
            "unresolved_required":[],"events":number(events)}

def number(events):
    return [{**e,"seq":i} for i,e in enumerate(events,1)]

class RuntimeEvidenceTests(unittest.TestCase):
    def test_clean_declarations_are_not_runtime_pass(self):
        self.assertEqual(verify(trace())[0],"INCONCLUSIVE")

    def test_false_freeze(self):
        t=trace()
        t["events"][1]["unresolved"]=["API shape"]
        self.assertEqual(verify(t)[0],"FAIL")

    def test_premature_mutation(self):
        t=trace("ambiguous")
        self.assertEqual(verify(t)[0],"FAIL")

    def test_overlap(self):
        t=trace()
        event={"kind":"delegate","agent":"frontend-engineer","call_id":"a","parent_id":"root",
               "stage":"IMPLEMENT","primary":True,"run_in_background":False,"write_paths":["src"]}
        other={**event,"call_id":"b","agent":"backend-engineer","primary":False,"write_paths":["src/api"]}
        t["events"]=number(t["events"][:2]+[event,other]+t["events"][2:])
        self.assertEqual(verify(t)[0],"FAIL")

    def test_duplicate_primary(self):
        t=trace()
        event={"kind":"delegate","agent":"security-reviewer","call_id":"a","parent_id":"root",
               "stage":"REVIEW","primary":True,"run_in_background":False,"write_paths":[]}
        t["events"]=number(t["events"][:2]+[event,{"kind":"end","call_id":"a"},{**event,"call_id":"b"}]+t["events"][2:])
        self.assertEqual(verify(t)[0],"FAIL")

    def test_stale_checks(self):
        t=trace()
        t["events"]=number(t["events"]+[{"kind":"mutation"}])
        status,reasons=verify(t)
        self.assertEqual(status,"INCONCLUSIVE")
        self.assertIn("current required verification not evidenced",reasons)

    def test_bad_trace(self):
        self.assertEqual(verify(None)[0],"INCONCLUSIVE")
        self.assertEqual(verify({"scenario":[]})[0],"INCONCLUSIVE")

if __name__=="__main__":
    unittest.main()
