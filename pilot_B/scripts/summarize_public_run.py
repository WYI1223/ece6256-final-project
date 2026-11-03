"""Summarize a `python -m conformbench run --score` directory: all-field accuracy,
fully-correct rate (repo evaluator verdicts) and token usage from turn_result.json."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cfb_common as C  # noqa: E402

run = Path(sys.argv[1])
T = Cn = P = full = n = 0
tok_in = tok_out = tok_reason = calls = attempts_gt1 = fallbacks = 0
rows = []
for ev_path in sorted(run.rglob("evaluation.json")):
    ev = json.loads(ev_path.read_text(encoding="utf-8"))
    s = ev["summary"]
    tr = json.loads((ev_path.parent / "turn_result.json").read_text(encoding="utf-8"))
    ar = tr.get("agent_response") or {}
    mc = ar.get("model_calls") or []
    ti = sum((c.get("usage") or {}).get("prompt_tokens", 0) for c in mc)
    to = sum((c.get("usage") or {}).get("completion_tokens", 0) for c in mc)
    trn = sum(C.llm_patch.reasoning_tokens_from_snapshot(c) for c in mc)
    fb = bool(((tr.get("provenance") or {}).get("generation") or {}).get("fallback"))
    n += 1; T += s["total"]; Cn += s["correct"]; P += s["partially_correct"]
    ok = s["incorrect"] == 0 and s["partially_correct"] == 0
    full += ok; tok_in += ti; tok_out += to; tok_reason += trn; calls += len(mc)
    attempts_gt1 += (ar.get("attempts") or 1) > 1; fallbacks += fb
    rows.append((tr["scenario_id"], s["correct"], s["total"], ok, ti, to, trn, ar.get("attempts")))
print(f"{'item':24s} correct/total fully in_tok out_tok reason_tok attempts")
for r in rows:
    print(f"{r[0]:24s} {r[1]:3d}/{r[2]:<3d}    {int(r[3])}    {r[4]:6d} {r[5]:6d} {r[6]:6d} {r[7]}")
print(json.dumps({
    "items": n, "all_field_acc": round(Cn / T, 4) if T else None, "correct": Cn, "total": T, "partial": P,
    "fully_correct": full, "fully_correct_rate": round(full / n, 4) if n else None,
    "input_tokens": tok_in, "output_tokens": tok_out, "reasoning_tokens": tok_reason, "model_calls": calls,
    "items_needing_retry": attempts_gt1, "fallbacks": fallbacks,
}, indent=1))
