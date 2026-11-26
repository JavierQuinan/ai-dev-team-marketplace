"""Offline verifier of normalized, sanitized runtime traces; never invokes a model."""
import argparse
import json
import re
import sys
from pathlib import Path

SCENARIOS = {
    "small": {"required": {"DISCOVER", "REPORT"}, "forbidden": set(), "max_agents": 1},
    "ui-only": {"required": {"DESIGN", "IMPLEMENT", "TEST", "REPORT"}, "forbidden": {"DATABASE"}, "max_agents": 4},
    "api-only": {"required": {"IMPLEMENT", "TEST", "REVIEW", "REPORT"}, "forbidden": {"DESIGN", "DATABASE"}, "max_agents": 4},
    "full-stack": {"required": {"DESIGN", "CONTRACT-FREEZE", "IMPLEMENT", "TEST", "REVIEW", "FIX", "VERIFY", "REPORT"}, "forbidden": set(), "max_agents": 6},
    "security": {"required": {"REVIEW", "REPORT"}, "forbidden": set(), "max_agents": 6},
    "migration": {"required": {"DATABASE", "REPORT"}, "forbidden": set(), "max_agents": 6},
    "ambiguous": {"required": {"DISCOVER", "REPORT"}, "forbidden": {"IMPLEMENT", "DATABASE"}, "max_agents": 2},
}

def verify(trace):
    if not isinstance(trace, dict):
        return "INCONCLUSIVE", ["invalid trace object"]
    failures, missing = [], []
    scenario = SCENARIOS.get(trace.get("scenario", "") if isinstance(trace.get("scenario"), str) else "")
    if scenario is None:
        return "INCONCLUSIVE", ["unknown scenario"]
    for key in ("trial_id", "claude_version", "plugin_version", "model", "fixture_sha", "target_sha", "transcript_digest"):
        if not isinstance(trace.get(key), str) or not trace[key].strip():
            missing.append("missing " + key)
    for key in ("fixture_sha", "target_sha"):
        if not re.fullmatch(r"[0-9a-f]{40}", str(trace.get(key, ""))):
            missing.append("invalid " + key)
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(trace.get("transcript_digest", ""))):
        missing.append("invalid transcript digest")
    events = trace.get("events")
    if not isinstance(events, list) or not events:
        return "INCONCLUSIVE", missing + ["missing events"]
    stages, agents, primary, active = set(), set(), set(), {}
    frozen = False
    security_count = 0
    checks = {}
    mutated = False
    for seq, e in enumerate(events, 1):
        if not isinstance(e, dict) or e.get("seq") != seq:
            missing.append("invalid event sequence")
            continue
        kind = e.get("kind")
        if kind == "stage":
            stage = e.get("stage")
            if not isinstance(stage, str):
                missing.append("missing stage")
                continue
            stages.add(stage)
            if stage in scenario["forbidden"]:
                failures.append("forbidden stage " + stage)
            if stage == "CONTRACT-FREEZE":
                if e.get("unresolved") != []:
                    failures.append("false or unsubstantiated freeze")
                else:
                    frozen = True
        elif kind == "delegate":
            agent, call, stage = e.get("agent"), e.get("call_id"), e.get("stage")
            if not all(isinstance(v, str) and v for v in (agent, call, stage, e.get("parent_id"))):
                missing.append("incomplete delegation attribution")
                continue
            agents.add(call)
            if call in active:
                failures.append("duplicate active call")
            if e.get("run_in_background") is not False:
                missing.append("parallel delegation needs independent trace review")
            if e.get("primary") is True:
                if stage in primary:
                    failures.append("duplicate primary stage " + stage)
                primary.add(stage)
                if agent == "security-reviewer":
                    security_count += 1
            paths = e.get("write_paths")
            if not isinstance(paths, list) or any(not isinstance(p, str) or not p or any(x in ("", ".", "..") for x in p.split("/")) or "\\" in p or ":" in p for p in paths):
                missing.append("invalid ownership declaration")
                continue
            normalized = [p.casefold().split("/") for p in paths]
            for other in active.values():
                for a in normalized:
                    for b in other:
                        if a[:len(b)] == b or b[:len(a)] == a:
                            failures.append("overlapping active writers")
            if paths and trace["scenario"] == "full-stack" and not frozen:
                failures.append("writer before contract freeze")
            active[call] = normalized
        elif kind == "end":
            call = e.get("call_id")
            if not isinstance(call, str) or call not in active:
                missing.append("unattributed delegate end")
            else:
                del active[call]
        elif kind == "mutation":
            mutated = True
            checks.clear()
            if trace["scenario"] == "ambiguous":
                failures.append("premature mutation")
            if trace["scenario"] == "full-stack" and not frozen:
                failures.append("mutation before freeze")
        elif kind == "check":
            if isinstance(e.get("id"), str) and e.get("required") is True:
                checks[e["id"]] = e.get("status") == "PASS" and e.get("exit_code") == 0
        else:
            missing.append("unknown event kind")
    if active:
        missing.append("unfinished delegate calls")
    if not scenario["required"] <= stages:
        missing.append("required stages not evidenced")
    if len(agents) > scenario["max_agents"]:
        missing.append("agent budget exceeded; justification review required")
    if trace["scenario"] == "security" and security_count != 1:
        missing.append("exactly one delegated security primary not evidenced")
    if trace["scenario"] in {"ui-only", "api-only", "full-stack"} and (not mutated or not checks or not all(checks.values())):
        missing.append("current required verification not evidenced")
    if trace.get("unresolved_required") != []:
        missing.append("required findings unresolved or not recorded")
    # Normalized declarations cannot authenticate transcripts or establish behavioral PASS.
    return ("FAIL", failures + missing) if failures else ("INCONCLUSIVE", missing or ["trace checks satisfied; independent raw-transcript review required"])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    args = parser.parse_args()
    try:
        status, reasons = verify(json.loads(args.trace.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError, RecursionError):
        status, reasons = "INCONCLUSIVE", ["unreadable or invalid trace"]
    print(json.dumps({"status": status, "reasons": reasons}, indent=2))
    return 1 if status == "FAIL" else 2

if __name__ == "__main__":
    sys.exit(main())
