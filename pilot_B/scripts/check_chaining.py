"""Check whether ConFormBench items can be chained into coherent multi-turn trajectories.

A pair (A -> B) of items from the same questionnaire is 'state-chainable' if A's
gold_resulting_state equals B's prior_state (ignoring empty-vs-null differences),
and 'history-chainable' if B's visible_history ends with A's history + A's utterance.
Read-only; writes a JSON report to runs/chaining_report.json.
"""
from __future__ import annotations

import collections
import glob
import json
import os
import sys
from pathlib import Path

DATA = Path(os.environ.get("CONFORMBENCH_DATA_DIR", ""))
OUT = Path(__file__).resolve().parent.parent / "runs" / "chaining_report.json"


def is_empty(v):
    if v is None or v == "":
        return True
    if isinstance(v, list):
        return all(is_empty(x) for x in v)
    if isinstance(v, dict):
        return all(is_empty(x) for x in v.values())
    return False


def flat(state, prefix=""):
    out = {}
    if isinstance(state, dict):
        for k in sorted(state):
            out.update(flat(state[k], f"{prefix}.{k}" if prefix else k))
    elif isinstance(state, list) and state and all(isinstance(x, dict) for x in state):
        for i, r in enumerate(state):
            out.update(flat(r, f"{prefix}[{i}]"))
    else:
        out[prefix] = state
    return out


def states_equal(a, b):
    fa, fb = flat(a), flat(b)
    for k in set(fa) | set(fb):
        va, vb = fa.get(k), fb.get(k)
        if is_empty(va) and is_empty(vb):
            continue
        if va != vb:
            return False
    return True


def overlap(a, b):
    """fraction of non-empty leaves of b that equal a."""
    fa, fb = flat(a), flat(b)
    keys = [k for k in fb if not is_empty(fb[k])]
    if not keys:
        return None
    return sum(1 for k in keys if fa.get(k) == fb[k]) / len(keys)


def load(pattern):
    items = []
    for p in sorted(glob.glob(str(DATA / pattern))):
        d = json.loads(Path(p).read_text(encoding="utf-8"))
        d["_path"] = str(Path(p).relative_to(DATA))
        d["_id"] = d.get("item_id") or d.get("scenario_id")
        d["_q"] = (d.get("questionnaire_id") or d.get("questionnaire") or "").removeprefix("pilot_")
        items.append(d)
    return items


def main():
    report = {}
    for label, pattern in [("public", "items/public/*/*/ground_truth.json"),
                           ("benchmark", "items/benchmark/*/*/ground_truth.json")]:
        items = load(pattern)
        by_q = collections.defaultdict(list)
        for d in items:
            by_q[d["_q"]].append(d)
        state_pairs, hist_pairs, best_overlaps = [], [], []
        identical_priors = collections.Counter()
        for q, group in by_q.items():
            for a in group:
                best = (0.0, None)
                for b in group:
                    if a is b:
                        continue
                    if states_equal(a["gold_resulting_state"], b["prior_state"]):
                        state_pairs.append((a["_id"], b["_id"]))
                    ha = (a.get("visible_history") or []) + [{"role": "user", "content": a["current_utterance"]}]
                    hb = b.get("visible_history") or []
                    a_utt_in_b = any(t.get("content") == a["current_utterance"] for t in hb)
                    if a_utt_in_b:
                        hist_pairs.append((a["_id"], b["_id"]))
                    ov = overlap(a["gold_resulting_state"], b["prior_state"])
                    if ov is not None and ov > best[0]:
                        best = (ov, b["_id"])
                best_overlaps.append((a["_id"], round(best[0], 3), best[1]))
            # shared prior states
            seen = []
            for d in group:
                key = json.dumps(d["prior_state"], sort_keys=True)
                identical_priors[(q, key[:0] + str(hash(key)))] += 1
        dup_prior_groups = sum(1 for v in identical_priors.values() if v > 1)
        report[label] = {
            "n_items": len(items),
            "per_questionnaire": {q: len(g) for q, g in sorted(by_q.items())},
            "state_chainable_pairs(gold_A==prior_B)": state_pairs,
            "history_chainable_pairs(utt_A in hist_B)": hist_pairs,
            "n_prior_states_shared_by_>1_item": dup_prior_groups,
            "best_gold_to_prior_overlap_per_item": sorted(best_overlaps, key=lambda x: -x[1])[:15],
        }
        print(f"[{label}] items={len(items)} per_q={report[label]['per_questionnaire']}")
        print(f"  state-chainable pairs: {len(state_pairs)} {state_pairs[:10]}")
        print(f"  history-chainable pairs: {len(hist_pairs)} {hist_pairs[:10]}")
        print(f"  prior states shared by >1 item: {dup_prior_groups}")
        print(f"  top overlaps: {report[label]['best_gold_to_prior_overlap_per_item'][:8]}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    sys.exit(main())
