#!/usr/bin/env python
"""Round-2 analysis of closed-loop run dirs, robust to partial runs.

For each run dir given on the command line it prints (markdown):
  1. clean accuracy by turn per condition, EXCLUDING rows whose solver call failed
     (the runner scores a failed call as "no update", which would inflate persistence);
  2. the injected-corruption table per trajectory, marking trajectories whose
     post-injection turns contain a failed call as INVALID;
  3. natural (non-injected) structured errors: how many of incremental's wrong
     leaf-turns are inherited from its own previous output (same wrong value), and
     how many of them rebuild also gets wrong at the same turn (re-derived).
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cfb_common as C  # noqa: E402

TURNS = 5


def load_rows(run: Path):
    p = run / "closed_loop_results.csv"
    if not p.exists():
        return []
    return list(csv.DictReader(open(p, encoding="utf-8")))


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def pct(x):
    return "" if x is None else f"{100 * x:.1f}"


def section_accuracy(rows):
    print("\n### 1. Clean accuracy by turn (macro over trajectories; failed-call rows excluded)\n")
    conds = sorted({r["condition"] for r in rows}, key=lambda c: ("incremental", "rebuild", "oracle").index(c) if c in ("incremental", "rebuild", "oracle") else 9)
    n_turns = max(int(r["turn"]) for r in rows)
    print("| condition | metric | " + " | ".join(f"T{t}" for t in range(1, n_turns + 1)) + " | mean T2+ | excluded rows |")
    print("|---|---|" + "---|" * (n_turns + 2))
    for cond in conds:
        for metric in ("all_field_acc", "structured_acc"):
            vals, excl = [], 0
            for t in range(1, n_turns + 1):
                sel = [r for r in rows if r["condition"] == cond and r["mode"] == "clean" and int(r["turn"]) == t]
                bad = [r for r in sel if r["solver_error"]]
                excl += len(bad)
                vals.append(mean([f(r[metric]) for r in sel if not r["solver_error"]]))
            print(f"| {cond} | {metric} | " + " | ".join(pct(v) for v in vals) + f" | {pct(mean(vals[1:]))} | {excl} |")


def section_injection(rows):
    print("\n### 2. Injected corruption per trajectory (incremental / oracle)\n")
    print("| trajectory | condition | field | injected | gold | persisted by turn | recovered at | valid |")
    print("|---|---|---|---|---|---|---|---|")
    summary = defaultdict(lambda: [0, 0, 0, 0])  # cond -> [valid n, survived first, recovered, never]
    by = defaultdict(list)
    for r in rows:
        if r["mode"] == "corrupt" and r["corrupted_field"]:
            by[(r["trajectory_id"], r["condition"])].append(r)
    for (tid, cond), rs in sorted(by.items()):
        rs.sort(key=lambda r: int(r["turn"]))
        post = [r for r in rs if r["prior_had_wrong_value"] != "" or r["persisted_error"] != ""]
        post = [r for r in post if r["persisted_error"] != ""]
        valid = all(not r["solver_error"] for r in post) and bool(post)
        pers = [int(r["persisted_error"]) for r in post]
        rec_turn = next((r["turn"] for r in post if r["silent_recovery"] == "1"), None)
        never = valid and pers and pers[-1] == 1
        first = rs[0]
        print(f"| {tid} | {cond} | `{first['corrupted_field']}` | {first['injected_value']} | {first['gold_value_of_corrupted']} | "
              f"{'/'.join(map(str, pers))} | {rec_turn or ('never' if never else '-')} | {'yes' if valid else 'NO (failed calls)'} |")
        if valid:
            s = summary[cond]
            s[0] += 1
            s[1] += int(pers[0] == 1) if pers else 0
            s[2] += int(rec_turn is not None)
            s[3] += int(bool(never))
    print("\n| condition | valid trajectories | survived first post-injection turn | silently recovered | never recovered |")
    print("|---|---|---|---|---|")
    for cond, s in summary.items():
        print(f"| {cond} | {s[0]} | {s[1]}/{s[0]} | {s[2]}/{s[0]} | {s[3]}/{s[0]} |")


def wrong_structured(trace_turn, idx):
    """{leaf: candidate_value} for structured leaves marked wrong in this trace turn."""
    out = {}
    wl = trace_turn.get("wrong_leaves") or []
    cand = C.flatten_state(trace_turn.get("candidate_state") or {})
    for leaf in wl:
        if C.is_structured_leaf(leaf, idx):
            out[leaf] = cand.get(leaf)
    return out


def section_natural(run: Path, rows):
    print("\n### 3. Natural structured errors: inherited vs re-derived (clean, turns 2+)\n")
    tdir = run / "traces"
    if not tdir.exists():
        print("(no traces)")
        return
    tot = defaultdict(int)
    for tr_dir in sorted(tdir.iterdir()):
        inc_p, reb_p = tr_dir / "incremental_clean.json", tr_dir / "rebuild_clean.json"
        if not inc_p.exists():
            continue
        inc = json.load(open(inc_p, encoding="utf-8"))
        reb = json.load(open(reb_p, encoding="utf-8")) if reb_p.exists() else None
        qid = next((r["questionnaire_id"] for r in rows if r["trajectory_id"] == tr_dir.name), None)
        if qid is None:
            continue
        idx = C.schema_index(C.load_schema(qid))
        errs = {r["turn"] for r in rows if r["trajectory_id"] == tr_dir.name and r["mode"] == "clean" and r["solver_error"]}
        prev = {}
        for i, tt in enumerate(inc):
            t = i + 1
            cur = wrong_structured(tt, idx)
            if t >= 2 and str(t) not in errs:
                for leaf, val in cur.items():
                    tot["inc_wrong"] += 1
                    inherited = leaf in prev and C.flatten_state({}) is not None and json.dumps(prev[leaf], sort_keys=True) == json.dumps(val, sort_keys=True)
                    tot["inherited"] += int(inherited)
                    if reb is not None and i < len(reb):
                        rw = wrong_structured(reb[i], idx)
                        tot["reb_also_wrong"] += int(leaf in rw)
                        tot["reb_same_value"] += int(leaf in rw and json.dumps(rw[leaf], sort_keys=True) == json.dumps(val, sort_keys=True))
                        tot["inherited_and_reb_wrong"] += int(inherited and leaf in rw)
            prev = cur
    n = tot["inc_wrong"]
    if not n:
        print("(no structured errors)")
        return
    if not any((d / "rebuild_clean.json").exists() for d in tdir.iterdir() if d.is_dir()):
        print(f"- incremental wrong structured leaf-turns (T2+): **{n}**, inherited from its own previous output: {tot['inherited']} ({100 * tot['inherited'] / n:.0f}%)")
        print("- (rebuild condition not run in this out-dir, so the inherited-vs-re-derived split is not available)")
        return
    print(f"- incremental wrong structured leaf-turns (T2+): **{n}**")
    print(f"- inherited from its own previous output (same wrong value): {tot['inherited']} ({100 * tot['inherited'] / n:.0f}%)")
    print(f"- rebuild also wrong on the same leaf-turn: {tot['reb_also_wrong']} ({100 * tot['reb_also_wrong'] / n:.0f}%), with the same wrong value: {tot['reb_same_value']}")
    print(f"- inherited AND rebuild also wrong (error is systematic, state channel not needed): {tot['inherited_and_reb_wrong']}")
    print(f"- inherited but rebuild gets it right (error survives ONLY through the carried state): **{tot['inherited'] - tot['inherited_and_reb_wrong']}** ({100 * (tot['inherited'] - tot['inherited_and_reb_wrong']) / n:.0f}% of incremental's errors)")


def main():
    for arg in sys.argv[1:]:
        run = Path(arg)
        rows = load_rows(run)
        print(f"\n## {run.name}\n")
        if not rows:
            print("(no results yet)")
            continue
        meta = run / "run_meta.json"
        if meta.exists():
            m = json.load(open(meta, encoding="utf-8"))
            print(f"solver `{m.get('solver')}` model `{m.get('model')}` trajectories {m.get('n_trajectories')} "
                  f"solver_errors {m.get('solver_errors')} billed in/out {m.get('billed_input_tokens')}/{m.get('billed_output_tokens')}")
        section_accuracy(rows)
        section_injection(rows)
        section_natural(run, rows)


if __name__ == "__main__":
    main()
