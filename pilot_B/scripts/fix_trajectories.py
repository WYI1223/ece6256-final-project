#!/usr/bin/env python
"""Apply the human-review fixes found while reading the 9 LLM-generated trajectories.

Each fix edits the raw dialogue/updates and the gold records are REBUILT through
make_trajectories.build_trajectory (so every validator re-runs). A `human_review`
block is written into each trajectory recording what was changed or flagged.

Usage: python fix_trajectories.py ../runs/trajectories.jsonl   (in place; keeps a .orig copy)
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cfb_common as C  # noqa: E402
from make_trajectories import build_trajectory  # noqa: E402


def upd(raw, turn, path, value=None, remove=False):
    ups = raw["turns"][turn - 1]["updates"]
    ups[:] = [u for u in ups if u["path"] != path]
    if not remove:
        ups.append({"path": path, "value": value})


def utt(raw, turn, old, new):
    t = raw["turns"][turn - 1]
    assert old in t["user"], (turn, old)
    t["user"] = t["user"].replace(old, new)


FIXES = {
    "pa_gen_01": (
        ["T2 gold hemoptysis_any='No' was invented (the user never mentioned blood) -> null"],
        lambda r: upd(r, 2, "hemoptysis_any", remove=True),
    ),
    "cr_gen_02": (
        ["T1 gold time_of_accident '00:20' was invented ('just after midnight' licenses no exact time) -> null"],
        lambda r: upd(r, 1, "time_of_accident", remove=True),
    ),
    "pa_gen_03": (
        ["T1 gold pain_details[0].pain_severity 'Moderate' was never stated, so the T4 correction "
         "'High, not Moderate' was incoherent -> T1 utterance now states 'moderate shoulder pain'"],
        lambda r: utt(r, 1, "having shoulder pain", "having moderate shoulder pain"),
    ),
    "pa_gen_05": (
        ["T3 'correction' was a no-op (T2 already said 'about three weeks'; gold only changed the string "
         "to 'three weeks') -> T2 now says 'about three days', T3 corrects to 'about three weeks'"],
        lambda r: (utt(r, 2, "started about three weeks ago", "started about three days ago"),
                   upd(r, 2, "pain_details[0].pain_duration", "about three days"),
                   upd(r, 3, "pain_details[0].pain_duration", "about three weeks")),
    ),
    "cr_gen_03": (
        ["T2 gold number_of_vehicles_involved='2' was premature (the other car is first mentioned in T3) -> moved to T3",
         "T1 'the 14th of March this year' does not license a year -> utterance now says 'the 14th of March 2025'"],
        lambda r: (upd(r, 2, "number_of_vehicles_involved", remove=True),
                   upd(r, 3, "number_of_vehicles_involved", "2"),
                   utt(r, 1, "the 14th of March this year", "the 14th of March 2025")),
    ),
}

FLAGS = {  # judged acceptable but ambiguous; left unchanged
    "pa_gen_04": ["T1 'fairly bad' -> pain_severity 'High' is a judgment call (Moderate also defensible)"],
    "pa_gen_02": ["T5 'vegetarian' -> preference_type 'Prefers' (vs 'Avoids') is ambiguous"],
    "cr_gen_02": ["T3 pre_crash_manoeuvre 'Straight' on a curve where the car 'slid straight off' is ambiguous"],
    "cr_gen_01": ["vehicles[0].role 'stopped at the red light' is an odd role label (free text; strict scoring will mismatch)",
                  "the correction (speed limit 35 -> 30) targets a T4 value, not a T1-2 value"],
    "cr_gen_04": ["vehicle role labels ('second vehicle in the chain') are paraphrase-prone free text",
                  "T5 reports an injury but injury_table (table) is excluded from gold -> a solver filling it is penalized"],
}


def main():
    path = Path(sys.argv[1])
    orig = path.with_suffix(".orig.jsonl")
    if not orig.exists():
        shutil.copy(path, orig)
    trajs = C.read_jsonl(orig)
    out = []
    for t in trajs:
        tid = t["trajectory_id"]
        review = {"reviewed_by": "pilot agent (manual read)", "fixes": [], "flags": FLAGS.get(tid, [])}
        if tid in FIXES:
            notes, fn = FIXES[tid]
            raw = {"scenario": t.get("scenario", ""),
                   "turns": [{"assistant": x["assistant"], "user": x["utterance"],
                              "updates": json.loads(json.dumps(x["updates"])), "note": x.get("note", "")}
                             for x in t["turns"]]}
            fn(raw)
            new, errs, stats = build_trajectory(raw, t["questionnaire_id"], C.load_schema(t["questionnaire_id"]), tid)
            if new is None:
                raise SystemExit(f"{tid}: fix produced an invalid trajectory: {errs}")
            new["generator"] = t.get("generator")
            review["fixes"] = notes
            t = new
        t["human_review"] = review
        out.append(t)
        print(tid, "fixes:", len(review["fixes"]), "flags:", len(review["flags"]),
              "candidates:", [c["path"] for c in t["corruption"]["candidates"]])
    path.write_text("".join(json.dumps(t, ensure_ascii=False) + "\n" for t in out), encoding="utf-8")
    print("wrote", path)


if __name__ == "__main__":
    main()
