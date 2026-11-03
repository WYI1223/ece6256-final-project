#!/usr/bin/env python
"""Round 2 part 4: 15-turn closed-loop trajectories (no human review of gold).

Same generator design as make_trajectories.py (whose helpers are imported, not
modified): the LLM writes N_TURNS turns (assistant question, user answer,
SPARSE record updates); gold records are built deterministically by applying
the updates; validators = repo shape validator + type/option/gate/count checks
+ coherence rules adapted for 15 turns:
  - 1 to 3 changes of an earlier non-empty value in turns 4..15, at least one of
    them in turns 6..15, and at least one correction turn whose utterance carries
    an explicit correction marker ("actually", "sorry", "I meant", ...);
  - >= 2 corruption candidates: structured scalar leaves (single_choice / number /
    date / time; gate controllers and count fields excluded, as in the 5-turn
    generator) whose final value is set in turns 1..K (K = 3), never touched in
    turns K+1..15, gold constant afterwards, value string not re-mentioned later,
    and (for number/date/time) the digits actually appear in the setting utterance.
Candidates are sorted by the turn that set them (earliest first, so the fact
leaves a 3-exchange window as early as possible), then by type priority.

Usage:
  python long_make_trajectories.py --plan patient_admin:4,crash_report:4 \
      --out ../runs/long/trajectories_long.jsonl --max-attempts 6
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cfb_common as C  # noqa: E402  (data dir, UTF-8 check, thinking patch)
import make_trajectories as M  # noqa: E402  (reuse validators; module is not modified)

N_TURNS = 15
CORRUPT_AFTER = 3
CORRECTION_MARKERS = ("actually", "sorry", "i meant", "correction", "mistake", "wrong", "not ", "let me correct",
                      "i misspoke", "scratch that", "on second thought", "rather than")

SEEDS = {
    "patient_admin": [
        "a 67-year-old retired teacher with a chesty cough with phlegm for a week, right knee pain and lower back "
        "pain, on three regular medications, allergic to penicillin and latex, with an upper denture, who uses a "
        "cane and avoids gluten",
        "a 34-year-old warehouse worker with lower back pain after lifting and a sore left wrist, a penicillin "
        "allergy, one regular medication, a vegetarian diet, a fall at work two months ago, and blurry vision "
        "when reading",
        "a 52-year-old with recent shoulder pain and headaches, upper and lower dentures, a shellfish allergy, two "
        "medications, some unintentional weight loss, and occasional choking on dry food",
        "a 78-year-old who had a fall last month, uses a walker, takes a blood thinner and two other medications, "
        "avoids pork for religious reasons, has cataract-related vision problems and a dry cough",
    ],
    "crash_report": [
        "a two-car rear-end collision at a signal-controlled intersection on a wet evening, with one witness and "
        "a damaged traffic-light pole",
        "a single-vehicle crash into a garden fence on a curve during snow at night on an unlit road, with a minor "
        "injury to the driver",
        "a side-swipe between two cars on a straight road in clear daylight while one car was overtaking, with "
        "two witnesses",
        "a three-vehicle chain collision at a stop sign at dusk, with a minor injury and a damaged mailbox",
    ],
}


def build_prompt(qid: str, schema: dict[str, Any], seed: str, feedback: str | None) -> str:
    ctx = schema.get("record_context") or {}
    rules = f"""
Write a {N_TURNS}-turn conversation between a form-filling ASSISTANT and a USER filling in the
"{schema.get('title', qid)}" form (speaker role: {ctx.get('speaker_role', 'user')}). Scenario: {seed}.

FORM FIELDS (use only these paths; repeat rows use group[index].field with index from 0):
{M.render_schema(schema)}

Return JSON exactly of this shape:
{{"scenario": "<one line>",
  "turns": [
    {{"assistant": "<assistant question>", "user": "<user answer>",
      "updates": [{{"path": "<field path>", "value": <json value>}}],
      "note": "<what this turn does>"}}
  ]}}

RULES
1. Exactly {N_TURNS} turns. Turn 1 assistant = short greeting + first question. Each user answer is natural
   conversational English (1-3 sentences), never mentions field ids, and gives NEW information. Across the 15
   turns the assistant walks through the different sections of the form, so the user keeps adding facts about
   new fields or new repeat-group rows until the end (spread the information; do not front-load everything).
2. "updates" = exactly the record changes this user answer licenses (given everything said before). Do not
   re-list unchanged values. Each turn has at least one update. Never set a value the user did not state
   (no guessing: e.g. "just after midnight" licenses no exact time; "this year" licenses no year).
3. Values: bool -> true/false; number -> JSON number; single_choice -> exactly one listed option string;
   multiple_choice -> JSON list of listed option strings; date -> "YYYY-MM-DD"; time -> "HH:MM" (24h);
   text -> a SHORT phrase copied VERBATIM from the user's words in that turn (no paraphrase, no added words).
   Dates, times and numbers must be stated by the user with their digits (e.g. "March 14, 2024", "6:45 pm",
   "35 mph").
4. Never use fields marked DO NOT USE. Never use the value "Unknown" or "Other".
5. Gates: set the gate field (e.g. a yes/no field) in the same or an earlier turn before any gated child,
   and only set gated children when the gate is open. Repeat rows: the row-count field must be set no later
   than the turn in which the user states how many there are; rows can be described in later turns. Never
   describe more rows than the count. Add rows in order (0, 1, 2...).
6. Turns 1-3 together establish at least 6 facts, including AT LEAST 4 single_choice / number / date / time
   facts that are NOT yes/no gate answers and NOT counts (e.g. a severity, a route, a date, a time, a weather
   or lighting condition, a speed).
7. In one or two of turns 6-15 the user explicitly CORRECTS a value they gave in turns 4-10 (e.g. "Actually,
   it was X, not Y" or "Sorry, I meant X"); that turn's updates set the corrected value. No other turn changes
   an earlier value.
8. PROTECTED FACTS: at least 4 of the single_choice/number/date/time facts set in turns 1-3 are NEVER
   mentioned, repeated, re-confirmed, summarized or corrected in turns 4-15 (neither by the user nor by the
   assistant; the assistant never recaps earlier answers).
9. Output JSON only, no comments.
""".strip()
    if feedback:
        rules += "\n\nYOUR PREVIOUS ATTEMPT WAS REJECTED FOR THESE REASONS; FIX THEM:\n" + feedback
    return rules


def _digits_licensed(ftype: str, value: Any, utt: str) -> bool:
    """For number/date/time gold values, the digits must occur in the setting utterance."""
    u = utt.lower()
    if ftype in ("number", "integer"):
        s = str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)
        return s in u
    if ftype == "date":
        y, m, d = value.split("-")
        return str(int(d)) in u and (y in u)
    if ftype == "time":
        h, mi = map(int, value.split(":"))
        h12 = h % 12 or 12
        return (f"{h}:{mi:02d}" in u or f"{h12}:{mi:02d}" in u or f"{h:02d}:{mi:02d}" in u
                or (mi == 0 and re.search(rf"\b({h}|{h12})\s*(am|pm|a\.m\.|p\.m\.|o'clock)", u) is not None))
    return True


def build_trajectory(raw: dict[str, Any], qid: str, schema: dict[str, Any], tid: str):
    idx = C.schema_index(schema)
    errs: list[str] = []
    turns_in = raw.get("turns") or []
    if len(turns_in) != N_TURNS:
        errs.append(f"expected {N_TURNS} turns, got {len(turns_in)}")
    state = C.empty_record(schema)
    turns_out = []
    touched_by_turn: list[set[str]] = []
    set_turn: dict[str, int] = {}
    corrections: list[dict[str, Any]] = []
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
            value, e = M.coerce_and_check(path, value, idx)
            if e:
                errs.append(f"turn {t}: {e}")
                continue
            before = C.get_path(state, path)
            is_addition = isinstance(before, list) and isinstance(value, list) and set(before) < set(value)
            if t > CORRUPT_AFTER and before not in (None, [], "") and before != value and not is_addition:
                corrections.append({"turn": t, "path": path, "before": before, "after": value,
                                    "marker": any(mk in utt.lower() for mk in CORRECTION_MARKERS)})
            try:
                C.set_path(state, path, value, idx)
            except (KeyError, IndexError) as exc:
                errs.append(f"turn {t}: {exc}")
                continue
            n_updates += 1
            touched.add(path)
            set_turn[path] = t
            info = idx["fields"].get(C.leaf_field_id(path)) or {}
            if info.get("type") in ("text", "string") and isinstance(value, str):
                if value.lower() not in utt.lower():
                    text_not_verbatim.append(f"t{t}:{path}={value!r}")
        M.materialize_counts(state, idx)
        errs.extend(M.check_state(state, schema, idx, f"after turn {t}"))
        touched_by_turn.append(touched)
        turns_out.append({
            "turn": t, "assistant": ast, "utterance": utt,
            "updates": ups, "note": turn.get("note", ""), "gold_state": deepcopy(state),
        })

    late = [c for c in corrections if c["turn"] >= 6]
    if not late:
        errs.append("no explicit correction of an earlier value in turns 6-15 (rule 7)")
    elif not any(c["marker"] for c in late):
        errs.append("the turn 6-15 value change is not phrased as an explicit correction ('Actually ...', rule 7)")
    if len(corrections) > 3:
        errs.append(f"{len(corrections)} earlier values were changed in turns 4-15 "
                    f"({', '.join(c['path'] + '@t' + str(c['turn']) for c in corrections[:6])}); "
                    "allowed: one or two explicit corrections (rule 7)")
    if len(text_not_verbatim) > 4:
        errs.append("text values not copied verbatim from the user's words (rule 3): " + "; ".join(text_not_verbatim[:5]))

    cands = []
    dropped_unlicensed = []
    if len(turns_out) == N_TURNS:
        K = CORRUPT_AFTER
        gold_k = C.flatten_state(turns_out[K - 1]["gold_state"])
        later_touched = set().union(*touched_by_turn[K:])
        later_text = " ".join(t["utterance"] + " " + t["assistant"] for t in turns_out[K:]).lower()
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
            if any(C.flatten_state(turns_out[j]["gold_state"]).get(leaf) != v for j in range(K, N_TURNS)):
                continue
            if isinstance(v, str) and len(v) >= 4 and v.lower() in later_text:
                continue  # value re-mentioned later -> not a silent slot
            st = set_turn.get(leaf)
            if st is None:
                continue  # materialized shell leaf, never stated
            if not _digits_licensed(ftype, v, turns_out[st - 1]["utterance"]):
                dropped_unlicensed.append(f"{leaf}={v!r}@t{st}")
                continue
            wv = M.wrong_value_for(leaf, v, idx)
            if wv is None:
                continue
            prio = {"single_choice": 0, "number": 1, "integer": 1, "date": 2, "time": 2, "bool": 3}[ftype]
            cands.append({"path": leaf, "gold_value": v, "wrong_value": wv, "field_type": ftype,
                          "set_turn": st, "source_utterance": turns_out[st - 1]["utterance"], "_prio": prio})
        cands.sort(key=lambda c: (c["set_turn"], c["_prio"], c["path"]))
        for c in cands:
            c.pop("_prio")
        if len(cands) < 2:
            errs.append(f"only {len(cands)} silent corruption candidate(s); need >= 2 (rules 6 and 8): "
                        "keep at least 4 choice/number/date/time facts from turns 1-3 completely unmentioned later"
                        + (f"; digits not stated by the user for {dropped_unlicensed}" if dropped_unlicensed else ""))

    stats = {
        "n_updates": n_updates,
        "corrections_t4plus": corrections,
        "text_values_not_verbatim": text_not_verbatim,
        "n_corruption_candidates": len(cands),
        "candidates_dropped_digits_not_in_utterance": dropped_unlicensed,
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
        "human_review": {"reviewed_by": None, "note": "validators only; gold NOT human-reviewed (Round 2 part 4)"},
    }
    return traj, [], stats


def generate(qid, seed, tid, max_attempts, max_tokens, log, log_lock):
    from langchain_core.messages import HumanMessage, SystemMessage
    from llm import get_chat_model_with_config, response_text

    schema = C.load_schema(qid)
    model, cfg = get_chat_model_with_config(max_tokens=max_tokens)
    feedback = None
    for attempt in range(1, max_attempts + 1):
        msgs = [SystemMessage(content=M.GEN_SYSTEM), HumanMessage(content=build_prompt(qid, schema, seed, feedback))]
        t0 = time.time()
        try:
            resp = model.invoke(msgs)
        except Exception as exc:
            with log_lock:
                log.append({"tid": tid, "qid": qid, "attempt": attempt, "error": f"{type(exc).__name__}: {str(exc)[:300]}"})
            continue
        usage = (getattr(resp, "usage_metadata", None) or {})
        rec = {"tid": tid, "qid": qid, "attempt": attempt, "model": cfg.get("model"),
               "input_tokens": usage.get("input_tokens", 0), "output_tokens": usage.get("output_tokens", 0),
               "reasoning_tokens": (usage.get("output_token_details") or {}).get("reasoning", 0),
               "finish_reason": (getattr(resp, "response_metadata", None) or {}).get("finish_reason"),
               "thinking": C.llm_patch.thinking_mode(), "latency_s": round(time.time() - t0, 1)}
        try:
            raw = M._extract_json(response_text(resp))
        except Exception as exc:
            rec["rejected"] = [f"unparseable JSON: {exc}"]
            with log_lock:
                log.append(rec)
            feedback = "- Output was not valid JSON (keep it compact; output the JSON object only)."
            continue
        traj, errs, stats = build_trajectory(raw, qid, schema, tid)
        rec["stats"] = stats
        if traj is None:
            rec["rejected"] = errs[:15]
            with log_lock:
                log.append(rec)
            feedback = "\n".join(f"- {e}" for e in errs[:15])
            print(f"[{tid}] attempt {attempt} rejected: {errs[:3]}", flush=True)
            continue
        rec["accepted"] = True
        with log_lock:
            log.append(rec)
        traj["generator"] = {"model": cfg.get("model"), "attempts": attempt, "seed": seed}
        print(f"[{tid}] accepted at attempt {attempt}; candidates "
              f"{[(c['path'], c['set_turn']) for c in traj['corruption']['candidates']]}", flush=True)
        return traj
    print(f"[{tid}] FAILED after {max_attempts} attempts", flush=True)
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", default="patient_admin:4,crash_report:4")
    ap.add_argument("--out", default=str(C.RUNS_DIR / "long" / "trajectories_long.jsonl"))
    ap.add_argument("--max-attempts", type=int, default=6)
    ap.add_argument("--max-tokens", type=int, default=12000)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args(argv)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not C.env_key_present():
        raise SystemExit("OPENAI_API_KEY missing in conformbench/.env")
    jobs = []
    for part in args.plan.split(","):
        qid, n = part.split(":")
        for i in range(int(n)):
            jobs.append((qid, SEEDS[qid][i % len(SEEDS[qid])], f"{qid[:2]}_long_{i + 1:02d}"))
    log: list = []
    log_lock = threading.Lock()
    from concurrent.futures import ThreadPoolExecutor

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(
            lambda j: generate(j[0], j[1], j[2], args.max_attempts, args.max_tokens, log, log_lock), jobs))
    accepted = [r for r in results if r]
    with out.open("w", encoding="utf-8") as fh:
        for r in accepted:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    log_path = out.with_name(out.stem + "_generation_log.json")
    summary = {
        "requested": len(jobs), "accepted": len(accepted),
        "accepted_ids": [r["trajectory_id"] for r in accepted],
        "failed_ids": [j[2] for j, r in zip(jobs, results) if not r],
        "attempts_total": len(log),
        "attempts_by_tid": {j[2]: sum(1 for r in log if r.get("tid") == j[2]) for j in jobs},
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
