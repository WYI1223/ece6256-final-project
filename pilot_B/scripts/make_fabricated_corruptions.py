#!/usr/bin/env python
"""Round 2, injection type "fabricated value".

A realistic way a carried state goes wrong is an invented value: 3 of the 9
LLM-generated trajectories in round 1 contained values the user never said.
Here, after turn K, a plausible value is written into a structured top-level
field that the user NEVER mentions anywhere in the trajectory (gold null at
every turn, no gate involved). Nothing in the visible history contradicts the
value; nothing licenses it either. A system that audits the prior against the
evidence should clear it; a system that only applies the current turn's
updates will carry it forever.

Candidate choice per trajectory: ungated top-level single_choice fields first
(value = first option that is not Unknown/Other/None), then bools (value True),
up to 3 candidates, deterministic order. The runner injects the first one.

Writes runs/trajectories_fabricated.jsonl.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cfb_common as C  # noqa: E402

SKIP_OPTIONS = {"Unknown", "Other", "None", "Not applicable", "N/A", "Unsure"}


def main():
    trajs = C.read_jsonl(C.RUNS_DIR / "trajectories.jsonl")
    out = []
    for traj in trajs:
        qid = traj["questionnaire_id"]
        schema = C.load_schema(qid)
        idx = C.schema_index(schema)
        never_set = []
        for fid in idx["top_level"]:
            info = idx["fields"].get(fid)
            if not info or info["group"] or info["gates"]:
                continue
            if fid in idx["gate_controllers"] or fid in idx["count_fields"]:
                continue
            if info["type"] not in ("single_choice", "bool"):
                continue
            if any(C.get_path(t["gold_state"], fid) not in (None, "", []) for t in traj["turns"]):
                continue
            # also require that no user utterance mentions the field id words (cheap guard)
            words = [w for w in fid.split("_") if len(w) > 3]
            text = " ".join(t["utterance"].lower() for t in traj["turns"])
            if words and all(w in text for w in words):
                continue
            never_set.append((0 if info["type"] == "single_choice" else 1, fid, info))
        never_set.sort(key=lambda x: (x[0], x[1]))
        cands = []
        for _, fid, info in never_set[:3]:
            if info["type"] == "single_choice":
                opts = [o for o in info["options"] if o not in SKIP_OPTIONS]
                if not opts:
                    continue
                val = opts[0]
            else:
                val = True
            cands.append({"path": fid, "gold_value": None, "wrong_value": val,
                          "field_type": info["type"], "kind": "fabricated",
                          "question": info.get("question", "")[:120]})
        if not cands:
            print(f"{traj['trajectory_id']}: no never-mentioned ungated choice/bool field -> skipped")
            continue
        t2 = json.loads(json.dumps(traj))
        t2["corruption"] = {"after_turn": traj["corruption"]["after_turn"], "kind": "fabricated", "candidates": cands}
        out.append(t2)
        print(f"{traj['trajectory_id']:16s} " + " | ".join(f"{c['path']}={c['wrong_value']!r}" for c in cands))
    dst = C.RUNS_DIR / "trajectories_fabricated.jsonl"
    dst.write_text("\n".join(json.dumps(t, ensure_ascii=False) for t in out) + "\n", encoding="utf-8")
    print("wrote", dst, len(out))


if __name__ == "__main__":
    main()
