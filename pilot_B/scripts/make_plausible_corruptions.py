#!/usr/bin/env python
"""Round 2: propose PLAUSIBLE alternative values for the corruption candidates.

Round 1 injected values that the dialogue history flatly contradicts (e.g. the
user said "sunny and clear", we injected "Dusk / Dawn"). A system that audits
the prior against the history repairs those almost by construction. This script
asks the LLM, for every existing corruption candidate (structured scalar set in
turns 1..K and never mentioned again), for the single most DEFENSIBLE
alternative reading of the same user words, with a 1-5 plausibility score.
The output is reviewed by hand before use (see `apply`).

Usage:
  python make_plausible_corruptions.py propose
      -> runs/plausible_proposals.jsonl + runs/plausible_proposals.md
  python make_plausible_corruptions.py apply --min-plausibility 3 [--pick tid=path ...]
      [--override tid=path=json_value ...]
      -> runs/trajectories_plausible.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cfb_common as C  # noqa: E402

from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402
from llm import get_chat_model_with_config, response_text  # noqa: E402

SYSTEM = (
    "You are an expert annotator auditing a conversational form-filling dataset. "
    "You judge whether a schema field value is UNIQUELY determined by what the user said, "
    "or whether a careful human annotator could defensibly commit to a different value from "
    "the same words. You never invent facts that were not said. Answer with strict JSON only."
)

PROMPT = """Schema field: {path}
Field definition (type, options, wording): {field_info}
Current annotated (gold) value: {gold}

Dialogue turns in which this field was set (assistant question, then user answer):
{context}

Question: from these exact words, is there a different value for this field that a careful
annotator could defensibly commit to (not a guess, not new information)? Consider: vague
intensity words ("fairly bad", "a bit"), rounding of numbers/dates/times, overlapping options,
and whether the user's statement actually licenses the gold value at all (then null may be
the defensible alternative).

Return JSON: {{"alternative": <value in the field format, or null if the gold value is the
only defensible reading>, "plausibility": <1-5; 5 = equally defensible as gold, 3 = clearly
weaker but a reasonable annotator might choose it, 1 = essentially wrong>, "reason": "<one sentence>"}}"""


def field_info(idx: dict[str, Any], path: str) -> str:
    info = dict(idx["fields"].get(C.leaf_field_id(path), {}))
    keep = {k: v for k, v in info.items()
            if k in ("type", "options", "label", "title", "question", "prompt", "description", "help", "min", "max", "unit")}
    return json.dumps(keep, ensure_ascii=False)


def turns_for(traj: dict[str, Any], path: str) -> str:
    out = []
    for t in traj["turns"]:
        if any(u["path"] == path for u in t.get("updates", [])):
            out.append(f"[turn {t['turn']}] assistant: {t.get('assistant', '')}\n[turn {t['turn']}] user: {t['utterance']}")
    if not out:  # fall back to turns 1..K
        k = traj["corruption"]["after_turn"]
        for t in traj["turns"][:k]:
            out.append(f"[turn {t['turn']}] assistant: {t.get('assistant', '')}\n[turn {t['turn']}] user: {t['utterance']}")
    return "\n".join(out)


def parse_json(text: str) -> dict[str, Any]:
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)


def propose(args):
    trajs = C.read_jsonl(Path(args.trajectories))
    model, cfg = get_chat_model_with_config(max_tokens=400)
    out_rows = []
    for traj in trajs:
        schema = C.load_schema(traj["questionnaire_id"])
        idx = C.schema_index(schema)
        for cand in traj["corruption"]["candidates"]:
            msg = PROMPT.format(path=cand["path"], field_info=field_info(idx, cand["path"]),
                                gold=json.dumps(cand["gold_value"]), context=turns_for(traj, cand["path"]))
            r = model.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=msg)])
            txt = response_text(r)
            try:
                js = parse_json(txt)
            except Exception:
                js = {"alternative": None, "plausibility": 0, "reason": "unparseable: " + txt[:120]}
            row = {"trajectory_id": traj["trajectory_id"], "questionnaire_id": traj["questionnaire_id"],
                   "path": cand["path"], "field_type": cand["field_type"], "gold_value": cand["gold_value"],
                   "round1_wrong_value": cand["wrong_value"], "alternative": js.get("alternative"),
                   "plausibility": js.get("plausibility"), "reason": js.get("reason"),
                   "context": turns_for(traj, cand["path"]), "model": cfg.get("model")}
            out_rows.append(row)
            print(f"{row['trajectory_id']:16s} {row['path']:40s} gold={str(row['gold_value']):14s} "
                  f"alt={str(row['alternative']):14s} p={row['plausibility']}", flush=True)
    out = Path(args.out)
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in out_rows) + "\n", encoding="utf-8")
    md = ["# Plausible-alternative proposals (LLM-proposed, to be hand-reviewed)", "",
          "| trajectory | field | gold | round-1 wrong | proposed alt | p | reason |", "|---|---|---|---|---|---|---|"]
    for r in out_rows:
        md.append(f"| {r['trajectory_id']} | `{r['path']}` | {r['gold_value']} | {r['round1_wrong_value']} | "
                  f"{r['alternative']} | {r['plausibility']} | {str(r['reason']).replace('|', '/')} |")
    md += ["", "## Evidence per field", ""]
    for r in out_rows:
        md += [f"### {r['trajectory_id']} `{r['path']}`", "", "```", r["context"], "```", ""]
    out.with_suffix(".md").write_text("\n".join(md), encoding="utf-8")
    print("wrote", out, "and", out.with_suffix(".md"))


def apply(args):
    trajs = C.read_jsonl(Path(args.trajectories))
    props = C.read_jsonl(Path(args.proposals))
    picks = {}
    for p in args.pick or []:
        tid, path = p.split("=", 1)
        picks[tid] = path
    overrides = {}
    for o in args.override or []:  # tid=path=json_value
        tid, path, val = o.split("=", 2)
        overrides[(tid, path)] = json.loads(val)
    by_tid: dict[str, list[dict[str, Any]]] = {}
    for r in props:
        by_tid.setdefault(r["trajectory_id"], []).append(r)
    out_trajs = []
    report = []
    for traj in trajs:
        tid = traj["trajectory_id"]
        chosen = []
        for r in by_tid.get(tid, []):
            alt = overrides.get((tid, r["path"]), r["alternative"])
            pl = r["plausibility"] or 0
            if (tid, r["path"]) in overrides:
                pl = 5
            if alt is None or alt == r["gold_value"]:
                continue
            if tid in picks and picks[tid] != r["path"]:
                continue
            if pl < args.min_plausibility and tid not in picks:
                continue
            chosen.append({"path": r["path"], "gold_value": r["gold_value"], "wrong_value": alt,
                           "field_type": r["field_type"], "kind": "plausible", "plausibility": pl,
                           "reason": r["reason"]})
        chosen.sort(key=lambda c: -c["plausibility"])
        if not chosen:
            report.append(f"{tid}: NO plausible candidate -> trajectory dropped")
            continue
        t2 = json.loads(json.dumps(traj))
        t2["corruption"] = {"after_turn": traj["corruption"]["after_turn"], "candidates": chosen,
                            "kind": "plausible", "source": "make_plausible_corruptions.py apply"}
        out_trajs.append(t2)
        report.append(f"{tid}: " + "; ".join(
            f"{c['path']} {c['gold_value']!r}->{c['wrong_value']!r} (p={c['plausibility']})" for c in chosen))
    Path(args.out).write_text("\n".join(json.dumps(t, ensure_ascii=False) for t in out_trajs) + "\n", encoding="utf-8")
    print("\n".join(report))
    print(f"wrote {args.out}: {len(out_trajs)} trajectories")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("propose")
    a.add_argument("--trajectories", default=str(C.RUNS_DIR / "trajectories.jsonl"))
    a.add_argument("--out", default=str(C.RUNS_DIR / "plausible_proposals.jsonl"))
    b = sub.add_parser("apply")
    b.add_argument("--trajectories", default=str(C.RUNS_DIR / "trajectories.jsonl"))
    b.add_argument("--proposals", default=str(C.RUNS_DIR / "plausible_proposals.jsonl"))
    b.add_argument("--out", default=str(C.RUNS_DIR / "trajectories_plausible.jsonl"))
    b.add_argument("--min-plausibility", type=int, default=3)
    b.add_argument("--pick", nargs="*", help="tid=path : force this field for a trajectory")
    b.add_argument("--override", nargs="*", help="tid=path=json_value : hand-set the alternative")
    args = ap.parse_args()
    propose(args) if args.cmd == "propose" else apply(args)


if __name__ == "__main__":
    main()
