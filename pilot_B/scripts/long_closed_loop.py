#!/usr/bin/env python
"""Round 2 part 4: closed-loop runner for 15-turn trajectories with history regimes.

Copy of closed_loop.py (conditions incremental / rebuild / oracle; modes clean /
corrupt; repo public deterministic evaluator; content-hash solver cache) plus a
history REGIME option, run for several regimes in one process so that all
regimes share ONE solver cache (<out-dir>/solver_cache.jsonl). The cache key
contains the visible history, so a call is shared only when the solver input is
byte-identical (e.g. turns 1..4 under full and w3, where the window still covers
the whole dialogue; turns 1..K between clean and corrupt).

Regimes (visible history at turn t; utterance = u_t in all regimes):
  full        : a1,u1,...,a_{t-1},u_{t-1},a_t
  w3          : last 3 exchanges + a_t                      (closed_loop --history-window 3)
  w3+summary  : [assistant] "Summary of the earlier conversation: ..." + w3,
                where the summary is ONE deepseek-flash call (thinking disabled
                via llm_patch) over the turns that fell out of the window
                (turns 1..t-4). Summaries are cached per (trajectory, last
                covered turn) in <out-dir>/summaries.jsonl, so clean and corrupt
                runs (and every injection point) share them.
  w0          : a_t only (state only; closed_loop --history-window 0)

Injection: after turn K (default: the trajectory's corruption.after_turn = 3;
--inject-after overrides, e.g. 6 for the late-injection variant), one corruption
candidate that the system holds correctly at K (vs generator gold) is overwritten
with its wrong value in the prior of turn K+1. Persistence / restoration are
measured against the injected value and the system's OWN pre-injection value
(its turn-K output), so they do not depend on gold correctness.
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

# regime -> (history window, prepend summary)
REGIMES = {"full": (None, False), "w3": (3, False), "w3+summary": (3, True), "w0": (0, False)}
REGIME_DIR = {"full": "full", "w3": "w3", "w3+summary": "w3sum", "w0": "w0"}
SUMMARY_PREFIX = "Summary of the earlier conversation: "
SUMMARY_SYSTEM = ("You summarize conversations faithfully. You never add, infer, interpret or classify "
                  "information; you only restate what was said.")
SUMMARY_PROMPT = """Below is the earlier part (turns 1-{upto}) of a conversation between a form-filling ASSISTANT and a USER.

Write a faithful bullet list of ALL facts the USER stated, in the user's own terms: keep their words, numbers,
dates, times and qualifiers (e.g. "moderate", "about two weeks", "wet", "just after 6:45 pm"). One fact per
bullet. Include yes/no answers in a self-contained way (e.g. "No falls in the last year"). If the user corrected
something, give only the corrected fact and note that it was corrected. Do not infer, interpret, classify or add
anything the user did not say. Output only the bullet list.

CONVERSATION:
{transcript}"""

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
    # long-run additions
    "regime", "inject_after", "pre_injection_value", "restored_pre_injection",
    "history_messages", "summary_upto", "summary_chars", "summary_cache_hit",
    "summary_input_tokens", "summary_output_tokens",
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


ABORT = threading.Event()


class BillingAbort(RuntimeError):
    """Raised to stop the whole run on a billing/auth error (HTTP 402/401) or, with
    --abort-on-error (default on), on any solver transport error. Nothing failed is
    cached, so rerunning the same command resumes from the persisted caches."""


def is_billing_error(msg: Any) -> bool:
    m = str(msg or "")
    return any(s in m for s in ("Error code: 402", "Insufficient Balance", "Error code: 401", "AuthenticationError"))


class Summarizer:
    """One deepseek-flash call per (trajectory, last covered turn); cached on disk (JSONL)."""

    def __init__(self, path: Path, max_tokens: int = 2000):
        self.cache = SolverCache(path)
        self.max_tokens = max_tokens
        self._model = None
        self._lock = threading.Lock()

    def model(self):
        with self._lock:
            if self._model is None:
                from llm import get_chat_model_with_config
                self._model, self.cfg = get_chat_model_with_config(max_tokens=self.max_tokens)
            return self._model

    def get(self, traj: dict[str, Any], upto: int) -> tuple[dict[str, Any], bool]:
        key = f"{traj['trajectory_id']}|upto={upto}"
        return self.cache.get_or_compute(key, lambda: self._compute(traj, upto))

    def _compute(self, traj, upto):
        from langchain_core.messages import HumanMessage, SystemMessage
        from llm import response_text

        lines = []
        for turn in traj["turns"][:upto]:
            lines.append(f"[assistant]: {turn['assistant']}")
            lines.append(f"[user]: {turn['utterance']}")
        prompt = SUMMARY_PROMPT.format(upto=upto, transcript="\n".join(lines))
        last_exc = None
        for attempt in range(1, 4):
            if ABORT.is_set():
                raise BillingAbort("aborted earlier (billing / auth error); not calling the API")
            t0 = time.time()
            try:
                resp = self.model().invoke([SystemMessage(content=SUMMARY_SYSTEM), HumanMessage(content=prompt)])
            except Exception as exc:  # transport failure -> retry, except billing/auth errors
                if is_billing_error(repr(exc)):
                    ABORT.set()
                    raise BillingAbort(f"summary call: {exc!r}") from exc
                last_exc = exc
                time.sleep(2 * attempt)
                continue
            usage = getattr(resp, "usage_metadata", None) or {}
            text = response_text(resp).strip()
            return {
                "trajectory_id": traj["trajectory_id"], "upto": upto, "summary": text,
                "input_tokens": int(usage.get("input_tokens", 0) or 0),
                "output_tokens": int(usage.get("output_tokens", 0) or 0),
                "reasoning_tokens": int(((usage.get("output_token_details") or {}).get("reasoning")) or 0),
                "finish_reason": (getattr(resp, "response_metadata", None) or {}).get("finish_reason"),
                "latency_s": round(time.time() - t0, 2), "attempts": attempt, "solver_error": None,
            }
        raise RuntimeError(f"summary failed for {traj['trajectory_id']} upto={upto}: {last_exc!r}")


def build_regime_history(turns, t, regime, traj=None, summarizer=None):
    """Return (history, summary_info) for a regime at turn t."""
    window, use_summary = REGIMES[regime]
    hist = build_history(turns, t, window)
    info = {"summary_upto": "", "summary_chars": "", "summary_cache_hit": "", "summary_input_tokens": 0,
            "summary_output_tokens": 0, "summary_text": None}
    if use_summary:
        upto = t - window - 1  # turns strictly before the window start
        if upto >= 1:
            res, hit = summarizer.get(traj, upto)
            hist = [{"role": "assistant", "content": SUMMARY_PREFIX + res["summary"]}] + hist
            info.update({"summary_upto": upto, "summary_chars": len(res["summary"]), "summary_cache_hit": int(hit),
                         "summary_input_tokens": 0 if hit else res.get("input_tokens", 0),
                         "summary_output_tokens": 0 if hit else res.get("output_tokens", 0),
                         "summary_text": res["summary"]})
    return hist, info


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
        self.cache = SolverCache(Path(args.cache_path) if args.cache_path else Path(args.out_dir) / "solver_cache.jsonl")
        self.summarizer = Summarizer(Path(args.out_dir) / "summaries.jsonl", max_tokens=args.summary_max_tokens)
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

        def compute():
            if ABORT.is_set():
                raise BillingAbort("aborted earlier (billing / auth error); not calling the API")
            res = call_solver(
                self.solver, item_id=f"{traj['trajectory_id']}_t{t}", qid=qid, schema=schema,
                prior=prior, history=history, utt=utt, metadata=metadata,
            )
            if is_billing_error(res.get("solver_error")):
                ABORT.set()
                raise BillingAbort(res["solver_error"])
            return res

        res, hit = self.cache.get_or_compute(key, compute)
        if res.get("solver_error") and not str(res["solver_error"]).startswith("shape:") and self.args.abort_on_error:
            ABORT.set()  # any transport failure: stop instead of scoring it as a no-update turn
            raise BillingAbort(f"solver transport error, aborting (rerun resumes from cache): {res['solver_error']}")
        return res, hit

    # ------------------------------------------------------------------
    def run_condition(self, traj, cond, mode, corr=None, regime="full", tag="k3"):
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
            history, sinfo = build_regime_history(turns, t, regime, traj, self.summarizer)
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
                "candidate_value_of_corrupted", "prior_had_wrong_value", "persisted_error", "silent_recovery",
                "inject_after", "pre_injection_value", "restored_pre_injection")}
            if corr and mode == "corrupt" and cond in ("incremental", "oracle"):
                corr_cols["corrupted_field"] = corr["path"]
                corr_cols["injected_value"] = json.dumps(corr["wrong_value"])
                corr_cols["gold_value_of_corrupted"] = json.dumps(C.get_path(gold_t, corr["path"]))
                corr_cols["candidate_value_of_corrupted"] = json.dumps(C.get_path(cand, corr["path"]))
                corr_cols["inject_after"] = corr["after_turn"]
                corr_cols["pre_injection_value"] = json.dumps(corr.get("pre_injection_value"))
                if t - 1 >= corr["after_turn"]:
                    prior_wrong = same_value(C.get_path(prior, corr["path"]), corr["wrong_value"])
                    persisted = same_value(C.get_path(cand, corr["path"]), corr["wrong_value"])
                    recovered = verdicts.get(corr["path"]) == "correct"
                    corr_cols["prior_had_wrong_value"] = int(prior_wrong)
                    corr_cols["persisted_error"] = int(persisted)
                    corr_cols["silent_recovery"] = int(recovered and prior_wrong)
                    corr_cols["restored_pre_injection"] = int(
                        corr.get("pre_injection_value") is not None
                        and same_value(C.get_path(cand, corr["path"]), corr["pre_injection_value"]))

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
                "regime": regime, "history_messages": len(history),
                **{k: sinfo[k] for k in ("summary_upto", "summary_chars", "summary_cache_hit",
                                         "summary_input_tokens", "summary_output_tokens")},
            }
            rows.append(row)
            wrong = {k: {"cand": cand_flat.get(k), "gold": gold_t_flat.get(k), "verdict": v}
                     for k, v in verdicts.items() if v != "correct"}
            trace.append({
                "turn": t, "utterance": utt, "prior_state": prior, "candidate_state": cand,
                "gold_state": gold_t, "wrong_leaves": wrong, "collateral_leaves": coll_leaves,
                "history": history, "summary_text": sinfo["summary_text"],
                "natural_persisted_examples": nat_examples, "row": row,
            })
            prev_out = cand
            prev_verdicts = verdicts
        out = Path(self.args.out_dir) / f"{tag}_{REGIME_DIR[regime]}" / "traces" / traj["trajectory_id"]
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{cond}_{mode}.json").write_text(json.dumps(trace, indent=1, ensure_ascii=False), encoding="utf-8")
        return rows, trace


def choose_corruption(traj, inc_clean_trace, idx, k_override: int | None = None) -> dict[str, Any] | None:
    """First candidate (sorted by set turn, then type) that the system holds correctly at turn K;
    fallback: first candidate whose system value at K is non-null and differs from the wrong value."""
    spec = traj.get("corruption") or {}
    k = int(k_override or spec.get("after_turn", 3))
    cands = spec.get("candidates") or []
    if not cands or len(inc_clean_trace) < k:
        return None
    turn_k = inc_clean_trace[k - 1]
    wrong_leaves = turn_k["wrong_leaves"]
    for c in cands:
        pre = C.get_path(turn_k["candidate_state"], c["path"])
        if c["path"] not in wrong_leaves and pre is not None:
            return {"after_turn": k, "path": c["path"], "wrong_value": c["wrong_value"], "gold_value": c["gold_value"],
                    "set_turn": c.get("set_turn"), "pre_injection_value": pre, "system_correct_before": True}
    for c in cands:
        pre = C.get_path(turn_k["candidate_state"], c["path"])
        if pre is not None and not same_value(pre, c["wrong_value"]):
            return {"after_turn": k, "path": c["path"], "wrong_value": c["wrong_value"], "gold_value": c["gold_value"],
                    "set_turn": c.get("set_turn"), "pre_injection_value": pre, "system_correct_before": False}
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trajectories", default=str(C.RUNS_DIR / "long" / "trajectories_long.jsonl"))
    ap.add_argument("--out-dir", default=str(C.RUNS_DIR / "long"))
    ap.add_argument("--cache-path", default=None, help="solver cache (default <out-dir>/solver_cache.jsonl, shared by regimes)")
    ap.add_argument("--solver", default="conformbench.systems.direct:solve")
    ap.add_argument("--regimes", default="full,w3,w3+summary,w0")
    ap.add_argument("--conditions", default="incremental")
    ap.add_argument("--modes", default="clean,corrupt")
    ap.add_argument("--inject-after", type=int, default=None, help="override corruption.after_turn (K)")
    ap.add_argument("--tag", default=None, help="output tag (default k<K>)")
    ap.add_argument("--limit", type=int, default=0, help="only the first N trajectories")
    ap.add_argument("--only", default="", help="comma-separated trajectory ids")
    ap.add_argument("--max-turns", type=int, default=0, help="truncate trajectories (smoke tests only)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--max-tokens", type=int, default=8192, help="cap on solver max_tokens (llm.MAX_TOKENS)")
    ap.add_argument("--summary-max-tokens", type=int, default=2000)
    ap.add_argument("--mock-gold", action="store_true", help="pass gold to a MOCK solver (offline harness test)")
    ap.add_argument("--no-abort-on-error", dest="abort_on_error", action="store_false",
                    help="score transport failures as no-update turns instead of aborting the run")
    args = ap.parse_args(argv)

    import llm  # repo's llm.py; loads .env (never printed)
    llm.MAX_TOKENS = args.max_tokens

    if "direct" in args.solver and args.mock_gold:
        raise SystemExit("--mock-gold must never be combined with an LLM solver")

    regimes = [r for r in args.regimes.split(",") if r]
    for r in regimes:
        if r not in REGIMES:
            raise SystemExit(f"unknown regime {r!r}; choose from {list(REGIMES)}")
    Path(args.out_dir).mkdir(parents=True, exist_ok=True)
    trajs = C.read_jsonl(Path(args.trajectories))
    if args.only:
        keep = set(args.only.split(","))
        trajs = [t for t in trajs if t["trajectory_id"] in keep]
    if args.limit:
        trajs = trajs[: args.limit]
    if args.max_turns:
        for t in trajs:
            t["turns"] = t["turns"][: args.max_turns]
    tag = args.tag or f"k{args.inject_after or (trajs[0].get('corruption') or {}).get('after_turn', 3)}"
    conditions = [c for c in args.conditions.split(",") if c]
    modes = [m for m in args.modes.split(",") if m]
    runner = Runner(args)
    t0 = time.time()

    all_rows: list[dict[str, Any]] = []
    clean_traces: dict[tuple[str, str, str], list] = {}
    aborted: list[str] = []

    def stop_if_aborted(phase):
        if aborted:
            raise SystemExit(f"ABORTED during {phase}: {aborted[0][:300]}. "
                             f"Completed solver calls and summaries are cached in {runner.cache.path} and "
                             f"{runner.summarizer.cache.path}; rerun the same command to resume (no CSV written).")

    def job_clean(traj, cond, reg):
        rows, trace = runner.run_condition(traj, cond, "clean", regime=reg, tag=tag)
        return traj["trajectory_id"], cond, reg, rows, trace

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = [pool.submit(job_clean, tr, c, reg) for reg in regimes for tr in trajs for c in conditions]
        for f in futs:
            try:
                tid, cond, reg, rows, trace = f.result()
            except BillingAbort as exc:
                aborted.append(str(exc))
                continue
            all_rows.extend(rows)
            clean_traces[(tid, cond, reg)] = trace
            print(f"[clean {reg}] {tid} {cond}: struct acc by turn = {[r['structured_acc'] for r in rows]}", flush=True)

    stop_if_aborted("clean runs")
    corruptions: dict[str, dict[str, Any]] = {reg: {} for reg in regimes}
    if "corrupt" in modes:
        jobs = []
        for reg in regimes:
            for tr in trajs:
                _, idx = runner.schema(tr["questionnaire_id"])
                inc = clean_traces.get((tr["trajectory_id"], "incremental", reg))
                if inc is None:
                    continue
                corr = choose_corruption(tr, inc, idx, args.inject_after)
                corruptions[reg][tr["trajectory_id"]] = corr
                if corr is None:
                    continue
                for cond in ("incremental", "oracle"):
                    if cond in conditions:
                        jobs.append((tr, cond, corr, reg))

        def job_corrupt(tr, cond, corr, reg):
            rows, _ = runner.run_condition(tr, cond, "corrupt", corr, regime=reg, tag=tag)
            return tr["trajectory_id"], cond, reg, rows

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = [pool.submit(job_corrupt, *j) for j in jobs]
            for f in futs:
                try:
                    tid, cond, reg, rows = f.result()
                except BillingAbort as exc:
                    aborted.append(str(exc))
                    continue
                all_rows.extend(rows)
                print(f"[corrupt {reg}] {tid} {cond} field={corruptions[reg][tid]['path']}: persisted by turn = "
                      f"{[r['persisted_error'] for r in rows]}", flush=True)

    stop_if_aborted("corrupt runs")
    all_rows.sort(key=lambda r: (r["regime"], r["trajectory_id"], r["mode"], r["condition"], r["turn"]))
    csv_path = Path(args.out_dir) / f"long_results_{tag}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(all_rows)

    def billed(sel):
        sel = list(sel)
        return {
            # billed = only rows whose call was not served from the cache in this run
            "billed_solver_calls": sum(int(r["model_calls"] or 0) for r in sel if not r["cache_hit"]),
            "billed_input_tokens": sum(int(r["input_tokens"] or 0) for r in sel if not r["cache_hit"]),
            "billed_output_tokens": sum(int(r["output_tokens"] or 0) for r in sel if not r["cache_hit"]),
            "billed_reasoning_tokens": sum(int(r["reasoning_tokens"] or 0) for r in sel if not r["cache_hit"]),
            "summary_calls": sum(1 for r in sel if r["summary_cache_hit"] == 0),
            "summary_input_tokens": sum(int(r["summary_input_tokens"] or 0) for r in sel),
            "summary_output_tokens": sum(int(r["summary_output_tokens"] or 0) for r in sel),
            "solver_errors": sum(1 for r in sel if r["solver_error"]),
            "fallbacks": sum(int(r["fallback_used"] or 0) for r in sel),
        }

    meta = {
        "solver": args.solver, "model": runner.model_tag, "max_tokens": args.max_tokens,
        "regimes": regimes, "tag": tag, "inject_after_override": args.inject_after,
        "n_trajectories": len(trajs), "conditions": conditions, "modes": modes,
        "corruptions": corruptions, "elapsed_s": round(time.time() - t0, 1),
        "deepseek_thinking": C.llm_patch.thinking_mode(),
        "totals": billed(all_rows),
        "by_regime": {reg: billed(r for r in all_rows if r["regime"] == reg) for reg in regimes},
    }
    (Path(args.out_dir) / f"run_meta_{tag}.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    # readable dump of every summary produced so far (all tags)
    summ = sorted(runner.summarizer.cache.data.values(), key=lambda r: (r["trajectory_id"], r["upto"]))
    (Path(args.out_dir) / "summaries_readable.json").write_text(json.dumps(summ, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in meta.items() if k != "corruptions"}, indent=1))
    print("wrote", csv_path)


if __name__ == "__main__":
    main()
