#!/usr/bin/env python
"""Closed-loop multi-turn runner for ConFormBench (ECE 6256 Pilot B).

For each synthetic trajectory (JSONL; one per line) this runs three conditions:

  incremental : prior_state(t) = the system's own output at t-1 (closed loop)
  rebuild     : prior_state(t) = empty initial record; visible_history = all turns so far
  oracle      : prior_state(t) = GOLD record after t-1 (single-turn ConFormBench setting)

and two modes:

  clean   : no intervention
  corrupt : after turn K (default 2), one structured scalar field that the
            system got right is overwritten with a wrong value in the state
            handed to turn K+1; later user utterances are unchanged and never
            mention that field.
              - incremental: the corrupted record is the prior for K+1, and
                whatever the system outputs is carried forward as usual.
              - oracle: prior(t) = gold(t-1) except the corrupted field, which
                carries the system's own previous value for it (so the only
                state error is the injected one).
              - rebuild: not applicable (no state channel; immune by design).

All conditions use visible_history = [a1, u1, ..., a_t] and current_utterance = u_t.
The solver is any ConFormBench `solve(turn)` (default: the paper's Direct JSON
baseline, conformbench.systems.direct:solve). Every turn is scored with the
repo's own evaluator (conformbench.evaluator.pipeline.evaluate_solver_turn,
public deterministic route; no LLM judge).

Identical solver inputs are cached (by content hash) and the cache is persisted
to <out-dir>/solver_cache.jsonl, so turn 1 is shared by all conditions (its
inputs are identical) and corrupt runs reuse the clean outputs for turns 1..K.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cfb_common as C  # noqa: E402  (sets CONFORMBENCH_DATA_DIR before repo import)

from conformbench.benchmark import load_solver, validate_resulting_state  # noqa: E402

CONDITIONS = ("incremental", "rebuild", "oracle")

CSV_COLUMNS = [
    "trajectory_id", "questionnaire_id", "condition", "mode", "turn",
    "n_fields", "n_correct", "n_partial", "all_field_acc", "fully_correct",
    "structured_n", "structured_correct", "structured_acc",
    "corrupted_field", "injected_value", "gold_value_of_corrupted", "candidate_value_of_corrupted",
    "prior_had_wrong_value", "persisted_error", "silent_recovery",
    "collateral_opportunities", "collateral_edits", "collateral_edits_nonempty",
    "nat_opportunities", "nat_persisted", "nat_recovered",
    "input_tokens", "output_tokens", "reasoning_tokens", "model_calls", "attempts", "fallback_used",
    "solver_error", "cache_hit", "latency_s",
]


# --------------------------------------------------------------------------
# Solver cache with in-flight de-duplication
# --------------------------------------------------------------------------

class SolverCache:
    def __init__(self, path: Path | None):
        self.path = path
        self.data: dict[str, dict[str, Any]] = {}
        self.locks: dict[str, threading.Lock] = {}
        self.meta_lock = threading.Lock()
        self.file_lock = threading.Lock()
        if path and path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = json.loads(line)
                    self.data[rec["key"]] = rec["result"]

    def get_or_compute(self, key: str, fn) -> tuple[dict[str, Any], bool]:
        with self.meta_lock:
            if key in self.data:
                return self.data[key], True
            lock = self.locks.setdefault(key, threading.Lock())
        with lock:
            with self.meta_lock:
                if key in self.data:
                    return self.data[key], True
            result = fn()
            # do not persist transport failures; they can be retried later
            with self.meta_lock:
                self.data[key] = result
            if self.path and not result.get("solver_error"):
                with self.file_lock:
                    with self.path.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps({"key": key, "result": result}, ensure_ascii=False) + "\n")
            return result, False


def cache_key(solver_path: str, model_tag: str, qid: str, prior: Any, history: Any, utt: str) -> str:
    blob = json.dumps(
        {"solver": solver_path, "model": model_tag, "q": qid, "prior": prior, "hist": history, "utt": utt},
        sort_keys=True, ensure_ascii=False,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# Solver call
# --------------------------------------------------------------------------

def call_solver(solver, *, item_id, qid, schema, prior, history, utt, metadata) -> dict[str, Any]:
    turn = SimpleNamespace(
        item_id=item_id,
        questionnaire_id=qid,
        schema=schema,
        form_schema=schema,
        prior_state=deepcopy(prior),
        public_state=deepcopy(prior),
        visible_history=deepcopy(history),
        current_utterance=utt,
        metadata=deepcopy(metadata),
    )
    t0 = time.time()
    try:
        returned = solver(turn)
    except Exception as exc:  # transport failure etc. -> score as no-update
        return {
            "state": deepcopy(prior),
            "solver_error": f"{type(exc).__name__}: {str(exc)[:300]}",
            "traceback": traceback.format_exc()[-2000:],
            "input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0, "model_calls": 0, "attempts": 0,
            "fallback_used": True, "latency_s": round(time.time() - t0, 2), "raw_response": None,
        }
    latency = round(time.time() - t0, 2)
    if isinstance(returned, dict) and isinstance(returned.get("resulting_state"), dict):
        state = returned["resulting_state"]
        agent = returned.get("agent_response") or {}
        prov = (returned.get("provenance") or {}).get("generation") or {}
    else:
        state, agent, prov = returned, {}, {}
    calls = agent.get("model_calls") or []
    in_tok = sum(int((c.get("usage") or {}).get("prompt_tokens", 0)) for c in calls)
    out_tok = sum(int((c.get("usage") or {}).get("completion_tokens", 0)) for c in calls)
    reas_tok = sum(int(C.llm_patch.reasoning_tokens_from_snapshot(c)) for c in calls)
    shape_errors = validate_resulting_state(state, schema)
    return {
        "state": state,
        "solver_error": ("shape: " + "; ".join(shape_errors[:5])) if shape_errors else None,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "reasoning_tokens": reas_tok,
        "model_calls": len(calls),
        "attempts": agent.get("attempts", len(calls)),
        "fallback_used": bool(prov.get("fallback") or agent.get("invalid_output_policy")),
        "latency_s": latency,
        "raw_response": (agent.get("raw_response") or "")[:20000] if agent else None,
    }


# --------------------------------------------------------------------------
# Trajectory helpers
# --------------------------------------------------------------------------

def build_history(turns: list[dict[str, Any]], t: int, window: int | None = None) -> list[dict[str, Any]]:
    """History visible at turn t (1-based): a1,u1,...,a_{t-1},u_{t-1},a_t.

    window=None -> full history (default). window=k -> only the last k previous
    (assistant, user) exchanges plus the current assistant question a_t
    (window=0: state-only design, the system sees just a_t and u_t)."""
    hist: list[dict[str, Any]] = []
    start = 1 if window is None else max(1, t - window)
    for i, turn in enumerate(turns[:t], start=1):
        if i < start:
            continue
        if turn.get("assistant"):
            hist.append({"role": "assistant", "content": turn["assistant"]})
        if i < t:
            hist.append({"role": "user", "content": turn["utterance"]})
    return hist


def norm(v: Any) -> Any:
    if isinstance(v, str):
        return " ".join(v.split()).lower()
    if isinstance(v, list):
        return sorted(json.dumps(norm(x), sort_keys=True) for x in v)
    return v


def same_value(a: Any, b: Any) -> bool:
    if (a in (None, "", [])) and (b in (None, "", [])):
        return True
    return norm(a) == norm(b)


class Runner:
    def __init__(self, args):
        self.args = args
        self.solver_path = args.solver
        self.solver = load_solver(args.solver)
        self.model_tag = (os.environ.get("OPENAI_MODEL", "") + ":thinking=" + C.llm_patch.thinking_mode()) if "direct" in args.solver else "na"
        self.cache = SolverCache(Path(args.out_dir) / "solver_cache.jsonl")
        self.schemas: dict[str, dict[str, Any]] = {}
        self.indexes: dict[str, dict[str, Any]] = {}
        self.lock = threading.Lock()

    def schema(self, qid):
        with self.lock:
            if qid not in self.schemas:
                self.schemas[qid] = C.load_schema(qid)
                self.indexes[qid] = C.schema_index(self.schemas[qid])
            return self.schemas[qid], self.indexes[qid]

    def solve(self, traj, t, prior, history, utt, gold_t, gold_prev):
        qid = traj["questionnaire_id"]
        schema, _ = self.schema(qid)
        metadata = {"direct_invalid_output_policy": "prior_state", "pilot_b": True}
        if self.args.mock_gold:  # offline harness test only; never used with an LLM solver
            metadata["_mock_gold"] = gold_t
            metadata["_mock_gold_prev"] = gold_prev
            metadata["_mock_seed"] = f"{traj['trajectory_id']}:{t}"
        key = cache_key(self.solver_path, self.model_tag, qid, prior, history, utt)
        return self.cache.get_or_compute(
            key,
            lambda: call_solver(
                self.solver, item_id=f"{traj['trajectory_id']}_t{t}", qid=qid, schema=schema,
                prior=prior, history=history, utt=utt, metadata=metadata,
            ),
        )

    # ------------------------------------------------------------------
    def run_condition(self, traj, cond, mode, corr=None):
        qid = traj["questionnaire_id"]
        schema, idx = self.schema(qid)
        turns = traj["turns"]
        initial = deepcopy(traj.get("initial_state") or C.empty_record(schema))
        rows, trace = [], []
        prev_out = None
        prev_verdicts: dict[str, str] = {}
        persisted_streak_open = True
        for t in range(1, len(turns) + 1):
            turn = turns[t - 1]
            utt = turn["utterance"]
            history = build_history(turns, t, self.args.history_window)
            gold_t = turn["gold_state"]
            gold_prev = initial if t == 1 else turns[t - 2]["gold_state"]

            if t == 1 or cond == "rebuild":
                prior = deepcopy(initial)
            elif cond == "incremental":
                prior = deepcopy(prev_out)
            else:  # oracle
                prior = deepcopy(gold_prev)

            corr_active = bool(mode == "corrupt" and corr and cond in ("incremental", "oracle") and t - 1 >= corr["after_turn"])
            if corr_active:
                if t - 1 == corr["after_turn"]:
                    C.set_path(prior, corr["path"], corr["wrong_value"], idx)
                elif cond == "oracle":
                    C.set_path(prior, corr["path"], C.get_path(prev_out, corr["path"]), idx)

            res, hit = self.solve(traj, t, prior, history, utt, gold_t, gold_prev)
            cand = res["state"] if isinstance(res["state"], dict) else deepcopy(prior)
            score = C.score_state(
                item_id=f"{traj['trajectory_id']}_{cond}_{mode}_t{t}", questionnaire_id=qid,
                prior_state=prior, visible_history=history, current_utterance=utt,
                gold_state=gold_t, candidate_state=cand,
            )
            verdicts = score["verdicts"]
            summ = score["summary"]
            n = len(verdicts)
            n_corr = sum(1 for v in verdicts.values() if v == "correct")
            n_part = sum(1 for v in verdicts.values() if v == "partially_correct")
            struct = [k for k in verdicts if C.is_structured_leaf(k, idx)]
            s_corr = sum(1 for k in struct if verdicts[k] == "correct")

            gold_t_flat = C.flatten_state(gold_t)
            gold_prev_flat = C.flatten_state(gold_prev)
            cand_flat = C.flatten_state(cand)

            # --- collateral edits: leaves correct in the previous record and unchanged in gold
            prev_record = prev_out if (cond == "rebuild" and t > 1) else prior
            prev_score = C.score_state(
                item_id=f"{traj['trajectory_id']}_{cond}_{mode}_t{t}_prev", questionnaire_id=qid,
                prior_state=prior, visible_history=history, current_utterance=utt,
                gold_state=gold_t, candidate_state=prev_record,
            )["verdicts"]
            coll_opp = coll = coll_ne = 0
            coll_leaves = []
            for leaf, gv in gold_t_flat.items():
                if leaf not in gold_prev_flat or not same_value(gold_prev_flat[leaf], gv):
                    continue  # gold changed this turn -> not a preservation slot
                if prev_score.get(leaf) != "correct":
                    continue
                coll_opp += 1
                if verdicts.get(leaf) != "correct":
                    coll += 1
                    coll_leaves.append(leaf)
                    if gv not in (None, "", []):
                        coll_ne += 1

            # --- natural (non-injected) persistence on structured leaves
            nat_opp = nat_pers = nat_rec = 0
            nat_examples = []
            if t > 1 and prev_out is not None:
                prev_flat = C.flatten_state(prev_out)
                for leaf, gv in gold_t_flat.items():
                    if not C.is_structured_leaf(leaf, idx):
                        continue
                    if corr and mode == "corrupt" and leaf == corr["path"]:
                        continue
                    if leaf not in gold_prev_flat or not same_value(gold_prev_flat[leaf], gv):
                        continue
                    if prev_verdicts.get(leaf) in (None, "correct"):
                        continue
                    nat_opp += 1
                    if verdicts.get(leaf) == "correct":
                        nat_rec += 1
                    elif same_value(cand_flat.get(leaf), prev_flat.get(leaf)):
                        nat_pers += 1
                        nat_examples.append({"leaf": leaf, "wrong": prev_flat.get(leaf), "gold": gv})

            # --- injected corruption tracking
            corr_cols: dict[str, Any] = {k: "" for k in (
                "corrupted_field", "injected_value", "gold_value_of_corrupted",
                "candidate_value_of_corrupted", "prior_had_wrong_value", "persisted_error", "silent_recovery")}
            if corr and mode == "corrupt" and cond in ("incremental", "oracle"):
                corr_cols["corrupted_field"] = corr["path"]
                corr_cols["injected_value"] = json.dumps(corr["wrong_value"])
                corr_cols["gold_value_of_corrupted"] = json.dumps(C.get_path(gold_t, corr["path"]))
                corr_cols["candidate_value_of_corrupted"] = json.dumps(C.get_path(cand, corr["path"]))
                if t - 1 >= corr["after_turn"]:
                    prior_wrong = same_value(C.get_path(prior, corr["path"]), corr["wrong_value"])
                    persisted = same_value(C.get_path(cand, corr["path"]), corr["wrong_value"])
                    recovered = verdicts.get(corr["path"]) == "correct"
                    corr_cols["prior_had_wrong_value"] = int(prior_wrong)
                    corr_cols["persisted_error"] = int(persisted)
                    corr_cols["silent_recovery"] = int(recovered and prior_wrong)

            row = {
                "trajectory_id": traj["trajectory_id"], "questionnaire_id": qid,
                "condition": cond, "mode": mode, "turn": t,
                "n_fields": n, "n_correct": n_corr, "n_partial": n_part,
                "all_field_acc": round(n_corr / n, 4) if n else "",
                "fully_correct": int(summ.get("incorrect", 0) == 0 and summ.get("partially_correct", 0) == 0),
                "structured_n": len(struct), "structured_correct": s_corr,
                "structured_acc": round(s_corr / len(struct), 4) if struct else "",
                **corr_cols,
                "collateral_opportunities": coll_opp, "collateral_edits": coll,
                "collateral_edits_nonempty": coll_ne,
                "nat_opportunities": nat_opp, "nat_persisted": nat_pers, "nat_recovered": nat_rec,
                # tokens of the (possibly cached) solver call; billed only when cache_hit == 0
                "input_tokens": res.get("input_tokens", 0),
                "output_tokens": res.get("output_tokens", 0),
                "reasoning_tokens": res.get("reasoning_tokens", 0),
                "model_calls": res.get("model_calls", 0),
                "attempts": res.get("attempts", 0),
                "fallback_used": int(bool(res.get("fallback_used"))),
                "solver_error": res.get("solver_error") or "",
                "cache_hit": int(hit),
                "latency_s": 0 if hit else res.get("latency_s", 0),
            }
            rows.append(row)
            wrong = {k: {"cand": cand_flat.get(k), "gold": gold_t_flat.get(k), "verdict": v}
                     for k, v in verdicts.items() if v != "correct"}
            trace.append({
                "turn": t, "utterance": utt, "prior_state": prior, "candidate_state": cand,
                "gold_state": gold_t, "wrong_leaves": wrong, "collateral_leaves": coll_leaves,
                "natural_persisted_examples": nat_examples, "row": row,
            })
            prev_out = cand
            prev_verdicts = verdicts
        out = Path(self.args.out_dir) / "traces" / traj["trajectory_id"]
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{cond}_{mode}.json").write_text(json.dumps(trace, indent=1, ensure_ascii=False), encoding="utf-8")
        return rows, trace


def choose_corruption(traj, inc_clean_trace, idx) -> dict[str, Any] | None:
    spec = traj.get("corruption") or {}
    k = int(spec.get("after_turn", 2))
    cands = spec.get("candidates") or []
    if not cands:
        return None
    if len(inc_clean_trace) < k:
        return None
    turn_k = inc_clean_trace[k - 1]
    wrong_leaves = turn_k["wrong_leaves"]
    for c in cands:
        if c["path"] not in wrong_leaves and C.get_path(turn_k["candidate_state"], c["path"]) is not None:
            return {"after_turn": k, "path": c["path"], "wrong_value": c["wrong_value"],
                    "system_correct_before": True}
    c = cands[0]
    return {"after_turn": k, "path": c["path"], "wrong_value": c["wrong_value"], "system_correct_before": False}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trajectories", default=str(C.RUNS_DIR / "trajectories.jsonl"))
    ap.add_argument("--out-dir", default=str(C.RUNS_DIR / "closed_loop"))
    ap.add_argument("--solver", default="conformbench.systems.direct:solve")
    ap.add_argument("--conditions", default=",".join(CONDITIONS))
    ap.add_argument("--modes", default="clean,corrupt")
    ap.add_argument("--limit", type=int, default=0, help="only the first N trajectories")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--max-tokens", type=int, default=8192, help="cap on solver max_tokens (llm.MAX_TOKENS)")
    ap.add_argument("--mock-gold", action="store_true", help="pass gold to a MOCK solver (offline harness test)")
    ap.add_argument("--csv-name", default="closed_loop_results.csv")
    ap.add_argument("--history-window", type=int, default=None,
                    help="ablation: previous exchanges visible (default full history; 0 = state-only)")
    args = ap.parse_args(argv)

    import llm  # repo's llm.py; loads .env (never printed)
    llm.MAX_TOKENS = args.max_tokens

    if "direct" in args.solver and args.mock_gold:
        raise SystemExit("--mock-gold must never be combined with an LLM solver")

    Path(args.out_dir).mkdir(parents=True, exist_ok=True)
    trajs = C.read_jsonl(Path(args.trajectories))
    if args.limit:
        trajs = trajs[: args.limit]
    conditions = [c for c in args.conditions.split(",") if c]
    modes = [m for m in args.modes.split(",") if m]
    runner = Runner(args)
    t0 = time.time()

    all_rows: list[dict[str, Any]] = []
    clean_traces: dict[tuple[str, str], list] = {}

    def job_clean(traj, cond):
        rows, trace = runner.run_condition(traj, cond, "clean")
        return traj["trajectory_id"], cond, rows, trace

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = [pool.submit(job_clean, tr, c) for tr in trajs for c in conditions]
        for f in futs:
            tid, cond, rows, trace = f.result()
            all_rows.extend(rows)
            clean_traces[(tid, cond)] = trace
            print(f"[clean] {tid} {cond}: acc by turn = {[r['all_field_acc'] for r in rows]}", flush=True)

    corruptions: dict[str, Any] = {}
    if "corrupt" in modes:
        jobs = []
        for tr in trajs:
            _, idx = runner.schema(tr["questionnaire_id"])
            inc = clean_traces.get((tr["trajectory_id"], "incremental"))
            if inc is None:
                continue
            corr = choose_corruption(tr, inc, idx)
            corruptions[tr["trajectory_id"]] = corr
            if corr is None:
                continue
            for cond in ("incremental", "oracle"):
                if cond in conditions:
                    jobs.append((tr, cond, corr))

        def job_corrupt(tr, cond, corr):
            rows, _ = runner.run_condition(tr, cond, "corrupt", corr)
            return tr["trajectory_id"], cond, rows

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = [pool.submit(job_corrupt, *j) for j in jobs]
            for f in futs:
                tid, cond, rows = f.result()
                all_rows.extend(rows)
                print(f"[corrupt] {tid} {cond} field={corruptions[tid]['path']}: persisted by turn = "
                      f"{[r['persisted_error'] for r in rows]}", flush=True)

    all_rows.sort(key=lambda r: (r["trajectory_id"], r["mode"], r["condition"], r["turn"]))
    csv_path = Path(args.out_dir) / args.csv_name
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(all_rows)
    meta = {
        "solver": args.solver, "model": runner.model_tag, "max_tokens": args.max_tokens,
        "history_window": args.history_window,
        "n_trajectories": len(trajs), "conditions": conditions, "modes": modes,
        "corruptions": corruptions, "elapsed_s": round(time.time() - t0, 1),
        # billed = only rows whose solver call was not served from the cache in this run
        "billed_input_tokens": sum(int(r["input_tokens"] or 0) for r in all_rows if not r["cache_hit"]),
        "billed_output_tokens": sum(int(r["output_tokens"] or 0) for r in all_rows if not r["cache_hit"]),
        "billed_model_calls": sum(int(r["model_calls"] or 0) for r in all_rows if not r["cache_hit"]),
        "billed_reasoning_tokens": sum(int(r["reasoning_tokens"] or 0) for r in all_rows if not r["cache_hit"]),
        "deepseek_thinking": C.llm_patch.thinking_mode(),
        "solver_errors": sum(1 for r in all_rows if r["solver_error"]),
    }
    (Path(args.out_dir) / "run_meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(json.dumps(meta, indent=1))
    print("wrote", csv_path)


if __name__ == "__main__":
    main()
