#!/usr/bin/env python
"""Round 2, injection type "ambiguous evidence".

The round-1 corruption candidates were all stated explicitly, often with the
option word itself ("I'd call it moderate", "mild ache"), so an LLM found no
defensible alternative for 25 of 27 of them (runs/plausible_proposals.md).
Here ONE user utterance per trajectory (turn 1 or 2) is rewritten by hand so
that the field's value is genuinely under-determined by the wording, and the
injected value is the other defensible reading. Gold is left at the original
value; the headline measurement is persistence of the injected reading, not
accuracy against gold. Everything else in the trajectory is unchanged, and the
field is (by construction of the round-1 candidates) never mentioned again.

Writes runs/trajectories_ambiguous.jsonl and prints the rewrite table.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cfb_common as C  # noqa: E402

# tid: (turn, old substring, new substring, field path, injected alternative, note)
REWRITES = {
    "pa_gen_01": (1, "and I'd call it moderate.",
                  "It's not agony, but it's definitely more than a niggle.",
                  "pain_details[0].pain_severity", "Mild", "gold Moderate; vague intensity"),
    "pa_gen_02": (2, "it gives me a rash, and I'd say it's moderate.",
                  "it gives me a nasty rash all over.",
                  "allergies[0].allergy_severity", "Severe", "gold Moderate; 'nasty', 'all over'"),
    "pa_gen_03": (2, "I do wear an upper denture, but no lower one.",
                  "I've got a partial plate up top, nothing on the bottom.",
                  "upper_denture", "No", "gold Yes; does a partial plate count as a denture"),
    "pa_gen_04": (2, "and I use a walker now.",
                  "and they gave me a walker after that, I keep it by the bed.",
                  "ambulatory_aid_use", "Has but does not use", "gold Yes (uses); 'keep it by the bed'"),
    "pa_gen_05": (1, "It's a mild ache.",
                  "It's a dull ache, bothers me when I walk a lot.",
                  "pain_details[0].pain_severity", "Moderate", "gold Mild; 'dull ache' + functional impact"),
    "cr_gen_01": (2, "It was around 6:45 in the evening,",
                  "It was sometime between half six and seven in the evening,",
                  "time_of_accident", "18:30", "gold 18:45; interval wording"),
    "cr_gen_02": (2, "and it was pitch dark with no streetlights anywhere.",
                  "and it was dark out; there's one streetlight down by the silo but it doesn't really reach that stretch.",
                  "lighting", "Dark–Lit", "gold Dark-Unlit; a streetlight exists nearby"),
    "cr_gen_03": (2, "It was a straight stretch, dry road, sunny and clear,",
                  "It was a straight stretch, the road was fine, bit of dew but nothing to speak of, sunny and clear,",
                  "road_surface_condition", "Wet", "gold Dry; 'bit of dew'"),
    "cr_gen_04": (2, "Around 7:15 in the evening, at dusk.",
                  "Around 7:15 in the evening; the sun had just about gone and the streetlights were starting to come on.",
                  "lighting", "Dark–Lit", "gold Dusk / Dawn; sun gone, streetlights on"),
    "pa_handmade_01": (2, "I bring up a small amount of green phlegm,",
                       "I bring up some green phlegm,",
                       "sputum_amount", "Moderate", "gold Small; 'some'"),
}


def main():
    trajs = C.read_jsonl(C.RUNS_DIR / "trajectories.jsonl")
    out = []
    print(f"{'trajectory':16s} {'field':34s} {'gold':16s} {'injected':22s} options-ok")
    for traj in trajs:
        tid = traj["trajectory_id"]
        if tid not in REWRITES:
            print(f"{tid}: no rewrite defined -> skipped")
            continue
        turn_no, old, new, path, alt, note = REWRITES[tid]
        schema = C.load_schema(traj["questionnaire_id"])
        idx = C.schema_index(schema)
        info = idx["fields"][C.leaf_field_id(path)]
        if info["type"] == "single_choice":
            assert alt in info["options"], f"{tid} {path}: {alt!r} not in {info['options']}"
        elif info["type"] == "bool":
            assert isinstance(alt, bool), f"{tid} {path}: bool expected"
        t = traj["turns"][turn_no - 1]
        assert t["turn"] == turn_no
        assert old in t["utterance"], f"{tid} turn {turn_no}: substring not found: {old!r}"
        gold_val = C.get_path(traj["turns"][-1]["gold_state"], path)
        # the field must be set by turn K and constant afterwards (round-1 candidate rule)
        cand_paths = {c["path"] for c in traj["corruption"]["candidates"]}
        assert path in cand_paths, f"{tid}: {path} is not a round-1 candidate (not a closed fact)"
        assert alt != gold_val
        t2 = json.loads(json.dumps(traj))
        t2["turns"][turn_no - 1]["utterance"] = t["utterance"].replace(old, new)
        t2["corruption"] = {
            "after_turn": traj["corruption"]["after_turn"],
            "kind": "ambiguous",
            "rewrite": {"turn": turn_no, "old": old, "new": new, "note": note},
            "candidates": [{"path": path, "gold_value": gold_val, "wrong_value": alt,
                            "field_type": info["type"], "kind": "ambiguous"}],
        }
        out.append(t2)
        print(f"{tid:16s} {path:34s} {str(gold_val):16s} {str(alt):22s} yes")
    dst = C.RUNS_DIR / "trajectories_ambiguous.jsonl"
    dst.write_text("\n".join(json.dumps(t, ensure_ascii=False) for t in out) + "\n", encoding="utf-8")
    print("wrote", dst, len(out))


if __name__ == "__main__":
    main()
