#!/usr/bin/env python
"""Build closed-loop trajectories for Pilot B.

Step 0 (done separately, scripts/check_chaining.py): public and benchmark items
are independent snapshots (0 pairs where gold(A) == prior(B) or where A's
utterance appears in B's history), so chaining existing items is not coherent.

This script therefore generates trajectories with the LLM (repo llm.py backend):
the model writes a 5-turn dialogue (assistant question + user answer per turn)
plus a SPARSE list of record updates per turn. Gold records are then built
deterministically by applying the updates cumulatively to the empty record, and
validated with the repo's shape validator plus type / option / gate / count /
coherence checks. Invalid trajectories are retried with the error list as
feedback and rejected after --max-attempts.

Also writes corruption candidates (structured scalar leaves set in turns 1..K,
never touched again, with a deterministic wrong value) for closed_loop.py.

Usage:
  python make_trajectories.py --plan patient_admin:5,crash_report:4 --out ../runs/trajectories.jsonl
  python make_trajectories.py --handmade --out ../runs/trajectories_handmade.jsonl   # no API
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cfb_common as C  # noqa: E402

N_TURNS = 5
CORRUPT_AFTER = 2

SEEDS = {
    "patient_admin": [
        "a 67-year-old retired teacher with a week-long chesty cough and knee pain, on two regular medications",
        "a 34-year-old warehouse worker with lower back pain after lifting, a penicillin allergy, and a vegetarian diet",
        "a 52-year-old with recent shoulder pain and headaches, who wears an upper denture and has a shellfish allergy",
        "a 78-year-old who had a fall last month, uses a walker, takes blood thinners, and avoids pork for religious reasons",
        "a 45-year-old with a dry cough, mild hip pain, two drug allergies, and lactose intolerance",
        "a 29-year-old asthmatic with a productive cough with yellow sputum and a peanut allergy",
    ],
    "crash_report": [
        "a two-car rear-end collision at a signal-controlled intersection on a wet evening",
        "a single-vehicle crash into a fence on a curve during snow at night on an unlit road",
        "a side-swipe between two cars on a straight road in clear daylight, with one witness",
        "a three-vehicle chain collision at a stop sign at dusk, with a minor injury",
        "a parking-lot style low-speed collision while one car was turning left in fog",
    ],
}

GEN_SYSTEM = (
    "You write synthetic, internally consistent test dialogues for a conversational "
    "form-filling benchmark. You output strictly valid JSON and nothing else."
)


# --------------------------------------------------------------------------
# Schema rendering for the generator prompt
# --------------------------------------------------------------------------

def render_schema(schema: dict[str, Any]) -> str:
    lines: list[str] = []

    def fmt_field(n, prefix, ind):
        t = n.get("type")
        desc = (n.get("question_text") or "").strip()
        if t in ("single_choice", "multiple_choice"):
            t = f"{t}: " + " | ".join(n.get("options") or [])
        if t == "table":
            lines.append(f"{'  ' * ind}- {prefix}{n['id']} (table) -- DO NOT USE")
            return
        if n.get("type") == "multiline_text":
            lines.append(f"{'  ' * ind}- {prefix}{n['id']} (multiline_text) -- DO NOT USE (leave null)")
            return
        lines.append(f"{'  ' * ind}- {prefix}{n['id']} ({t}) -- {desc}")

    def walk(nodes, ind=0, group=None):
        for n in nodes or []:
            st = n.get("structure_type", "regular")
            if st == "regular":
                fmt_field(n, f"{group}[i]." if group else "", ind)
            elif st == "repeat_group":
                rep = n.get("repeat") or {}
                cnt = rep.get("from_slot")
                lines.append(f"{'  ' * ind}- {n['id']}[i] = repeat group rows (row count must equal `{cnt}`):")
                walk(n.get("fields"), ind + 1, n["id"])
            elif st == "gate":
                g = n.get("gate") or {}
                lines.append(f"{'  ' * ind}- [only when {g.get('gate_on')} in {json.dumps(g.get('when_values'))}]:")
                walk(n.get("fields"), ind + 1, group)
            elif st == "group":
                walk(n.get("fields"), ind, group)

    walk(schema.get("questions"))
    return "\n".join(lines)


def build_prompt(qid: str, schema: dict[str, Any], seed: str, feedback: str | None) -> str:
    ctx = schema.get("record_context") or {}
    rules = f"""
Write a {N_TURNS}-turn conversation between a form-filling ASSISTANT and a USER filling in the
"{schema.get('title', qid)}" form (speaker role: {ctx.get('speaker_role', 'user')}). Scenario: {seed}.

FORM FIELDS (use only these paths; repeat rows use group[index].field with index from 0):
{render_schema(schema)}

Return JSON exactly of this shape:
{{"scenario": "<one line>",
  "turns": [
    {{"assistant": "<assistant question>", "user": "<user answer>",
      "updates": [{{"path": "<field path>", "value": <json value>}}],
      "note": "<what this turn does>"}}
  ]}}

RULES
1. Exactly {N_TURNS} turns. Turn 1 assistant = short greeting + first question. Each user answer is natural
   conversational English (1-3 sentences), never mentions field ids, and gives new information.
2. "updates" = exactly the record changes this user answer licenses (given everything said before). Do not
   re-list unchanged values. Each turn has at least one update.
3. Values: bool -> true/false; number -> JSON number; single_choice -> exactly one listed option string;
   multiple_choice -> JSON list of listed option strings; date -> "YYYY-MM-DD"; time -> "HH:MM" (24h);
   text -> a SHORT phrase copied VERBATIM from the user's words in that turn (no paraphrase, no added words).
4. Never use fields marked DO NOT USE. Never use the value "Unknown" or "Other".
5. Gates: set the gate field (e.g. a yes/no field) in the same or an earlier turn before any gated child,
   and only set gated children when the gate is open. Repeat rows: the row-count field must be set no later than the turn
   in which the user states how many there are; rows can be described in later turns. Never describe more
   rows than the count. Add rows in order (0, 1, 2...).
6. Turns 1-2 together establish at least 7 facts, including at least 4 bool/single_choice/number/date facts
   and at least one repeat-group row.
7. In exactly one of turns 3-5 the user explicitly CORRECTS a value they gave in turn 1 or 2 (e.g. "Actually,
   it was X, not Y"); that turn's updates set the corrected value.
8. Another of turns 3-5 adds a new repeat-group row or a new topic.
9. At least 4 bool/single_choice/number/date facts set in turns 1-2 are NEVER mentioned, repeated, or
   re-confirmed in turns 3-5 (neither by the user nor by the assistant).
10. Output JSON only, no comments.
""".strip()
    if feedback:
        rules += "\n\nYOUR PREVIOUS ATTEMPT WAS REJECTED FOR THESE REASONS; FIX THEM:\n" + feedback
    return rules


# --------------------------------------------------------------------------
# Deterministic gold construction + validation
# --------------------------------------------------------------------------

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^\d{2}:\d{2}$")


def coerce_and_check(path: str, value: Any, idx: dict[str, Any]) -> tuple[Any, str | None]:
    info = idx["fields"].get(C.leaf_field_id(path))
    if info is None:
        return value, f"unknown field path {path!r}"
    t = info["type"]
    opts = info.get("options") or []
    if value is None:
        return value, None
    if t == "bool":
        return value, None if isinstance(value, bool) else f"{path}: bool expected, got {value!r}"
    if t in ("number", "integer"):
        ok = isinstance(value, (int, float)) and not isinstance(value, bool)
        return value, None if ok else f"{path}: number expected, got {value!r}"
    if t == "single_choice":
        if isinstance(value, (int, float)) and str(value) in opts:
            value = str(value)
        if value not in opts:
            return value, f"{path}: {value!r} not in options {opts}"
        if value in ("Unknown", "Other"):
            return value, f"{path}: Unknown/Other not allowed"
        return value, None
    if t == "multiple_choice":
        if not isinstance(value, list) or not all(v in opts for v in value):
            return value, f"{path}: list of options expected, got {value!r}"
        return value, None
    if t == "date":
        return value, None if isinstance(value, str) and _DATE_RE.match(value) else f"{path}: bad date {value!r}"
    if t == "time":
        return value, None if isinstance(value, str) and _TIME_RE.match(value) else f"{path}: bad time {value!r}"
    if t == "table":
        return value, f"{path}: table fields not allowed"
    if t == "multiline_text":
        return value, f"{path}: multiline_text fields not allowed"
    if not isinstance(value, str):
        return value, f"{path}: text expected, got {value!r}"
    return value, None


def check_state(state: dict[str, Any], schema: dict[str, Any], idx: dict[str, Any], label: str) -> list[str]:
    errs = [f"{label}: {e}" for e in C.validate_resulting_state(state, schema)]
    for gid, g in idx["gates"].items():
        ctrl = state.get(g["gate_on"])
        if ctrl in g["when_values"]:
            continue
        for child in g["children"]:
            if child in idx["repeat_groups"]:
                if state.get(child):
                    errs.append(f"{label}: gate {g['gate_on']}={ctrl!r} closed but repeat group {child} has rows")
            elif child in state and state.get(child) not in (None, [], ""):
                errs.append(f"{label}: gate {g['gate_on']}={ctrl!r} closed but {child} is set")
    for gid, rg in idx["repeat_groups"].items():
        cf = rg.get("count_field")
        rows = state.get(gid) or []
        if cf:
            cnt = state.get(cf)
            try:
                cnt_i = int(cnt) if cnt is not None else None
            except (TypeError, ValueError):
                cnt_i = None
            if rows and cnt_i is not None and len(rows) > cnt_i:
                errs.append(f"{label}: {cf}={cnt!r} but {gid} has {len(rows)} rows")
            if cnt_i and not rows:
                errs.append(f"{label}: {cf}={cnt!r} but {gid} has no rows")
    return errs


def materialize_counts(state: dict[str, Any], idx: dict[str, Any]) -> None:
    """Repo convention (flatagent._materialize_repeat_counts, used by Direct's prompt):
    when a from_slot count is known, the record holds that many rows; rows whose
    attributes are not yet stated are empty shells (all children null)."""
    for gid, rg in idx["repeat_groups"].items():
        cf = rg.get("count_field")
        if not cf:
            continue
        try:
            cnt = int(state.get(cf)) if state.get(cf) is not None else None
        except (TypeError, ValueError):
            continue
        rows = state.get(gid)
        if not isinstance(rows, list):
            rows = []
            state[gid] = rows
        while cnt is not None and len(rows) < cnt:
            rows.append({f: None for f in sorted(rg["fields"])})


def wrong_value_for(path: str, value: Any, idx: dict[str, Any]) -> Any:
    info = idx["fields"][C.leaf_field_id(path)]
    t = info["type"]
    if t == "bool":
        return not value
    if t == "single_choice":
        opts = [o for o in info["options"] if o not in ("Unknown", "Other")]
        if value in opts and len(opts) > 1:
            return opts[(opts.index(value) + 1) % len(opts)]
        return None
    if t in ("number", "integer"):
        return value + 2 if isinstance(value, int) else round(value * 1.5 + 1, 1)
    if t == "date":
        d = dt.date.fromisoformat(value) + dt.timedelta(days=3)
        return d.isoformat()
    if t == "time":
        h, m = map(int, value.split(":"))
        return f"{(h + 2) % 24:02d}:{m:02d}"
    if t == "multiple_choice":
        opts = [o for o in info["options"] if o not in ("Unknown", "Other") and o not in value]
        return [opts[0]] if opts else None
    return None


def build_trajectory(raw: dict[str, Any], qid: str, schema: dict[str, Any], tid: str) -> tuple[dict[str, Any] | None, list[str], dict[str, Any]]:
    idx = C.schema_index(schema)
    errs: list[str] = []
    turns_in = raw.get("turns") or []
    if len(turns_in) != N_TURNS:
        errs.append(f"expected {N_TURNS} turns, got {len(turns_in)}")
    state = C.empty_record(schema)
    turns_out = []
    touched_by_turn: list[set[str]] = []
    corrections = 0
    text_not_verbatim: list[str] = []
    n_updates = 0
    for t, turn in enumerate(turns_in, start=1):
        utt = str(turn.get("user") or "").strip()
        ast = str(turn.get("assistant") or "").strip()
        ups = turn.get("updates") or []
        if not utt or not ast:
            errs.append(f"turn {t}: missing assistant or user text")
        if not ups:
            errs.append(f"turn {t}: no updates")
        touched = set()
        for up in ups:
            path, value = up.get("path"), up.get("value")
            if not isinstance(path, str):
                errs.append(f"turn {t}: bad update {up!r}")
                continue
            value, e = coerce_and_check(path, value, idx)
            if e:
                errs.append(f"turn {t}: {e}")
                continue
            before = C.get_path(state, path)
            if t > CORRUPT_AFTER and before not in (None, [], "") and before != value:
                corrections += 1
            try:
                C.set_path(state, path, value, idx)
            except (KeyError, IndexError) as exc:
                errs.append(f"turn {t}: {exc}")
                continue
            n_updates += 1
            touched.add(path)
            info = idx["fields"].get(C.leaf_field_id(path)) or {}
            if info.get("type") in ("text", "string") and isinstance(value, str):
                if value.lower() not in utt.lower():
                    text_not_verbatim.append(f"t{t}:{path}={value!r}")
        materialize_counts(state, idx)
        errs.extend(check_state(state, schema, idx, f"after turn {t}"))
        touched_by_turn.append(touched)
        turns_out.append({
            "turn": t, "assistant": ast, "utterance": utt,
            "updates": ups, "note": turn.get("note", ""), "gold_state": deepcopy(state),
        })
    if corrections == 0:
        errs.append("no explicit correction of an earlier value in turns 3-5 (rule 7)")

    # corruption candidates: structured leaves set by turn K, never touched later, gold constant after K
    cands = []
    if len(turns_out) == N_TURNS:
        gold_k = C.flatten_state(turns_out[CORRUPT_AFTER - 1]["gold_state"])
        later_touched = set().union(*touched_by_turn[CORRUPT_AFTER:])
        later_text = " ".join(t["utterance"] + " " + t["assistant"] for t in turns_out[CORRUPT_AFTER:]).lower()
        for leaf, v in gold_k.items():
            info = idx["fields"].get(C.leaf_field_id(leaf)) or {}
            ftype = info.get("type")
            if ftype not in ("single_choice", "bool", "number", "integer", "date", "time"):
                continue
            if v in (None, [], "") or leaf in later_touched:
                continue
            fid = C.leaf_field_id(leaf)
            if fid in idx["gate_controllers"] or fid in idx["count_fields"]:
                continue
            if any(C.flatten_state(turns_out[j]["gold_state"]).get(leaf) != v for j in range(CORRUPT_AFTER, N_TURNS)):
                continue
            if isinstance(v, str) and len(v) >= 4 and v.lower() in later_text:
                continue  # value re-mentioned later -> not a silent slot
            wv = wrong_value_for(leaf, v, idx)
            if wv is None:
                continue
            prio = {"single_choice": 0, "number": 1, "integer": 1, "date": 2, "time": 2, "bool": 3}[ftype]
            cands.append({"path": leaf, "gold_value": v, "wrong_value": wv, "field_type": ftype, "_prio": prio})
        cands.sort(key=lambda c: (c["_prio"], c["path"]))
        for c in cands:
            c.pop("_prio")
        if not cands:
            errs.append("no silent corruption candidate (rule 9): every closed fact from turns 1-2 is touched later")

    stats = {
        "n_updates": n_updates,
        "n_corrections_t3plus": corrections,
        "text_values_not_verbatim": text_not_verbatim,
        "n_corruption_candidates": len(cands),
        "final_nonempty_leaves": sum(1 for v in C.flatten_state(state).values() if v not in (None, "", [])),
    }
    if errs:
        return None, errs, stats
    traj = {
        "trajectory_id": tid,
        "questionnaire_id": qid,
        "scenario": raw.get("scenario", ""),
        "initial_state": C.empty_record(schema),
        "turns": turns_out,
        "corruption": {"after_turn": CORRUPT_AFTER, "candidates": cands},
        "validation": stats,
    }
    return traj, [], stats


# --------------------------------------------------------------------------
# A hand-written trajectory (no API) used to validate the harness offline
# --------------------------------------------------------------------------

HANDMADE = {
    "scenario": "Handmade: 67-year-old with cough, knee pain, aspirin; corrects pain severity",
    "turns": [
        {"assistant": "Hello, I'll help you complete your admission screening. Are you having any pain at the moment?",
         "user": "Yes, my left knee has been hurting for 2 weeks, it's moderate most days. I also have a cough.",
         "updates": [
             {"path": "pain_experience", "value": True},
             {"path": "number_of_pains", "value": 1},
             {"path": "pain_details[0].pain_part", "value": "left knee"},
             {"path": "pain_details[0].pain_severity", "value": "Moderate"},
             {"path": "pain_details[0].pain_duration", "value": "2 weeks"},
             {"path": "cough_present", "value": True}]},
        {"assistant": "Thanks. Tell me about the cough, and do you bring anything up?",
         "user": "The cough started 5 days ago and I bring up a small amount of green phlegm, no blood. I take aspirin 81 mg by mouth daily.",
         "updates": [
             {"path": "cough_duration", "value": "5 days"},
             {"path": "sputum_present", "value": True},
             {"path": "sputum_color", "value": ["Green"]},
             {"path": "sputum_amount", "value": "Small"},
             {"path": "hemoptysis_any", "value": "No"},
             {"path": "number_of_medications", "value": 1},
             {"path": "current_medications[0].medication_name", "value": "aspirin"},
             {"path": "current_medications[0].dose", "value": "81 mg"},
             {"path": "current_medications[0].route", "value": "Oral"},
             {"path": "current_medications[0].frequency", "value": "daily"}]},
        {"assistant": "Any allergies to medicines or foods?",
         "user": "I'm allergic to penicillin, it gives me hives, fairly severe.",
         "updates": [
             {"path": "number_of_allergies", "value": 1},
             {"path": "allergies[0].allergen", "value": "penicillin"},
             {"path": "allergies[0].reaction", "value": "hives"},
             {"path": "allergies[0].allergy_severity", "value": "Severe"}]},
        {"assistant": "Have you had any falls in the last year?",
         "user": "No falls. Actually, about the knee, it's really more mild than moderate.",
         "updates": [
             {"path": "fall_in_last_12_months", "value": False},
             {"path": "pain_details[0].pain_severity", "value": "Mild"}]},
        {"assistant": "Do you wear dentures?",
         "user": "Yes, just an upper denture, nothing on the bottom.",
         "updates": [
             {"path": "denture_present", "value": True},
             {"path": "upper_denture", "value": "Yes"},
             {"path": "lower_denture", "value": "No"}]},
    ],
}


def _extract_json(text: str) -> dict[str, Any]:
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    s, e = text.find("{"), text.rfind("}")
    if s == -1 or e == -1:
        raise ValueError("no JSON object in response")
    return json.loads(text[s : e + 1])


def generate(qid: str, seed: str, tid: str, max_attempts: int, max_tokens: int, log: list) -> dict[str, Any] | None:
    from langchain_core.messages import HumanMessage, SystemMessage
    from llm import get_chat_model_with_config, response_text

    schema = C.load_schema(qid)
    model, cfg = get_chat_model_with_config(max_tokens=max_tokens)
    feedback = None
    for attempt in range(1, max_attempts + 1):
        msgs = [SystemMessage(content=GEN_SYSTEM), HumanMessage(content=build_prompt(qid, schema, seed, feedback))]
        t0 = time.time()
        try:
            resp = model.invoke(msgs)
        except Exception as exc:
            log.append({"tid": tid, "attempt": attempt, "error": f"{type(exc).__name__}: {str(exc)[:300]}"})
            continue
        usage = (getattr(resp, "usage_metadata", None) or {})
        rec = {"tid": tid, "qid": qid, "attempt": attempt, "model": cfg.get("model"),
               "input_tokens": usage.get("input_tokens", 0), "output_tokens": usage.get("output_tokens", 0),
               "reasoning_tokens": (usage.get("output_token_details") or {}).get("reasoning", 0),
               "thinking": C.llm_patch.thinking_mode(),
               "latency_s": round(time.time() - t0, 1)}
        try:
            raw = _extract_json(response_text(resp))
        except Exception as exc:
            rec["rejected"] = [f"unparseable JSON: {exc}"]
            log.append(rec)
            feedback = "- Output was not valid JSON."
            continue
        traj, errs, stats = build_trajectory(raw, qid, schema, tid)
        rec["stats"] = stats
        if traj is None:
            rec["rejected"] = errs[:15]
            log.append(rec)
            feedback = "\n".join(f"- {e}" for e in errs[:15])
            continue
        rec["accepted"] = True
        log.append(rec)
        traj["generator"] = {"model": cfg.get("model"), "attempts": attempt, "seed": seed}
        return traj
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", default="patient_admin:5,crash_report:4")
    ap.add_argument("--out", default=str(C.RUNS_DIR / "trajectories.jsonl"))
    ap.add_argument("--max-attempts", type=int, default=3)
    ap.add_argument("--max-tokens", type=int, default=6000)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--handmade", action="store_true", help="write the hand-written trajectory only (no API)")
    args = ap.parse_args(argv)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.handmade:
        schema = C.load_schema("patient_admin")
        traj, errs, stats = build_trajectory(HANDMADE, "patient_admin", schema, "pa_handmade_01")
        if traj is None:
            raise SystemExit("handmade trajectory invalid: " + "; ".join(errs))
        traj["generator"] = {"model": "human", "attempts": 1}
        out.write_text(json.dumps(traj, ensure_ascii=False) + "\n", encoding="utf-8")
        print("wrote", out, stats, "candidates:", [c["path"] for c in traj["corruption"]["candidates"]])
        return

    if not C.env_key_present():
        raise SystemExit("OPENAI_API_KEY missing in conformbench/.env; cannot generate with the LLM")

    jobs = []
    for part in args.plan.split(","):
        qid, n = part.split(":")
        for i in range(int(n)):
            seed = SEEDS[qid][i % len(SEEDS[qid])]
            jobs.append((qid, seed, f"{qid[:2]}_gen_{i + 1:02d}"))
    log: list = []
    from concurrent.futures import ThreadPoolExecutor

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda j: generate(j[0], j[1], j[2], args.max_attempts, args.max_tokens, log), jobs))
    accepted = [r for r in results if r]
    with out.open("w", encoding="utf-8") as fh:
        for r in accepted:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    log_path = out.with_name(out.stem + "_generation_log.json")
    summary = {
        "requested": len(jobs), "accepted": len(accepted),
        "attempts_total": len(log),
        "input_tokens": sum(int(r.get("input_tokens") or 0) for r in log),
        "output_tokens": sum(int(r.get("output_tokens") or 0) for r in log),
        "reasoning_tokens": sum(int(r.get("reasoning_tokens") or 0) for r in log),
        "elapsed_s": round(time.time() - t0, 1),
    }
    log_path.write_text(json.dumps({"summary": summary, "attempts": log}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=1))
    print("wrote", out, "and", log_path)


if __name__ == "__main__":
    main()
