#!/usr/bin/env python
"""Summarize closed_loop_results.csv into markdown tables (Pilot B).

Usage: python summarize_closed_loop.py ../runs/closed_loop [--price-in 0.3 --price-out 1.2]
Writes <run>/closed_loop_summary.md and prints it.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import statistics as st
from collections import defaultdict
from pathlib import Path

CONDS = ["incremental", "rebuild", "oracle"]


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def fmt(x, pct=False, nd=3):
    if x is None:
        return "-"
    return f"{100 * x:.1f}" if pct else f"{x:.{nd}f}"


def boot_diff(a: dict, b: dict, n=5000, seed=0):
    """Paired bootstrap over trajectories of mean(a - b)."""
    keys = sorted(set(a) & set(b))
    diffs = [a[k] - b[k] for k in keys]
    if not diffs:
        return None, None, None
    rng = random.Random(seed)
    samples = []
    for _ in range(n):
        s = [diffs[rng.randrange(len(diffs))] for _ in diffs]
        samples.append(sum(s) / len(s))
    samples.sort()
    return sum(diffs) / len(diffs), samples[int(0.025 * n)], samples[int(0.975 * n) - 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--price-in", type=float, default=0.30, help="USD per 1M input tokens (assumed)")
    ap.add_argument("--price-out", type=float, default=1.20, help="USD per 1M output tokens (assumed)")
    args = ap.parse_args()
    run = Path(args.run_dir)
    rows = list(csv.DictReader((run / "closed_loop_results.csv").open(encoding="utf-8")))
    meta = json.loads((run / "run_meta.json").read_text(encoding="utf-8"))
    for r in rows:
        r["turn"] = int(r["turn"])
    turns = sorted({r["turn"] for r in rows})
    trajs = sorted({r["trajectory_id"] for r in rows})
    out: list[str] = []
    P = out.append

    P(f"# Closed-loop pilot summary ({run.name})\n")
    P(f"solver `{meta['solver']}`, model `{meta['model']}`, {meta['n_trajectories']} trajectories, "
      f"{len(turns)} turns, elapsed {meta['elapsed_s']} s, solver errors {meta['solver_errors']}.\n")

    def table(mode, metric, title, pct=True):
        P(f"\n### {title} ({mode})\n")
        P("| condition | " + " | ".join(f"T{t}" for t in turns) + " | mean T2-T5 |")
        P("|---|" + "---|" * (len(turns) + 1))
        for c in CONDS:
            sel = [r for r in rows if r["mode"] == mode and r["condition"] == c]
            if not sel:
                continue
            vals = [mean([f(r[metric]) for r in sel if r["turn"] == t]) for t in turns]
            m25 = mean([f(r[metric]) for r in sel if r["turn"] >= 2])
            P(f"| {c} | " + " | ".join(fmt(v, pct) for v in vals) + f" | {fmt(m25, pct)} |")

    P("\n## 1. Accuracy vs turn (macro mean over trajectories; percentages)\n")
    P("all_field_acc = correct leaf verdicts / all scored leaves (repo public evaluator, strict exact "
      "match; open-text paraphrases count as wrong). structured_acc = same restricted to "
      "bool/number/choice/date/time leaves. fully_correct = every leaf correct.")
    for mode in ("clean", "corrupt"):
        if any(r["mode"] == mode for r in rows):
            table(mode, "all_field_acc", "all-field accuracy")
            table(mode, "structured_acc", "structured-field accuracy")
            table(mode, "fully_correct", "fully-correct record rate")

    # micro accuracy
    P("\n### micro all-field accuracy, clean (sum correct / sum leaves, T1-T5)\n")
    P("| condition | correct/total | micro acc |\n|---|---|---|")
    for c in CONDS:
        sel = [r for r in rows if r["mode"] == "clean" and r["condition"] == c]
        if sel:
            a = sum(int(r["n_correct"]) for r in sel)
            b = sum(int(r["n_fields"]) for r in sel)
            P(f"| {c} | {a}/{b} | {fmt(a / b, True)} |")

    # gaps with paired bootstrap
    P("\n## 2. Condition gaps (clean; per-trajectory mean over T2-T5; paired bootstrap 95% CI over trajectories)\n")
    P("| comparison | metric | mean diff (pp) | 95% CI (pp) | n traj |\n|---|---|---|---|---|")
    per = defaultdict(dict)
    for metric in ("all_field_acc", "structured_acc", "fully_correct"):
        for c in CONDS:
            for tid in trajs:
                v = mean([f(r[metric]) for r in rows if r["mode"] == "clean" and r["condition"] == c
                          and r["trajectory_id"] == tid and r["turn"] >= 2])
                if v is not None:
                    per[(metric, c)][tid] = v
        for a, b in (("incremental", "oracle"), ("rebuild", "oracle"), ("incremental", "rebuild")):
            d, lo, hi = boot_diff(per[(metric, a)], per[(metric, b)])
            if d is not None:
                P(f"| {a} - {b} | {metric} | {100 * d:+.1f} | [{100 * lo:+.1f}, {100 * hi:+.1f}] | "
                  f"{len(set(per[(metric, a)]) & set(per[(metric, b)]))} |")

    # injected corruption
    P("\n## 3. Injected corruption (one structured field overwritten after T2; never mentioned again)\n")
    P("| trajectory | condition | field | injected | gold | system had it right at T2 | persisted T3/T4/T5 | persistence length | recovered at |")
    P("|---|---|---|---|---|---|---|---|---|")
    corr = meta.get("corruptions") or {}
    agg = defaultdict(lambda: {"n": 0, "p3": 0, "len": [], "rec": 0, "never": 0})
    for tid in trajs:
        for c in ("incremental", "oracle"):
            sel = sorted([r for r in rows if r["mode"] == "corrupt" and r["condition"] == c
                          and r["trajectory_id"] == tid], key=lambda r: r["turn"])
            if not sel:
                continue
            post = [r for r in sel if r["persisted_error"] != ""]
            pers = [int(r["persisted_error"]) for r in post]
            length = 0
            for p in pers:
                if p:
                    length += 1
                else:
                    break
            rec_turn = next((r["turn"] for r in post if r["silent_recovery"] == "1"), None)
            info = corr.get(tid) or {}
            P(f"| {tid} | {c} | `{post[0]['corrupted_field']}` | {post[0]['injected_value']} | "
              f"{post[0]['gold_value_of_corrupted']} | {info.get('system_correct_before')} | "
              f"{'/'.join(str(p) for p in pers)} | {length} | {rec_turn or 'never'} |")
            a = agg[c]
            a["n"] += 1
            a["p3"] += pers[0] if pers else 0
            a["len"].append(length)
            a["rec"] += 1 if rec_turn else 0
            a["never"] += 0 if rec_turn else 1
    P("\n| condition | n | wrong value survived T3 | mean persistence length (0-3 turns) | silently recovered by T5 | never recovered |")
    P("|---|---|---|---|---|---|")
    for c, a in agg.items():
        P(f"| {c} | {a['n']} | {a['p3']}/{a['n']} | {fmt(mean(a['len']), nd=2)} | {a['rec']}/{a['n']} | {a['never']}/{a['n']} |")
    P("\nrebuild: not applicable (no state channel; a corrupted record is discarded each turn by construction).")

    # accuracy effect of corruption
    P("\n### accuracy cost of the injection (corrupt - clean, all_field_acc, mean over T3-T5, pp)\n")
    P("| condition | clean | corrupt | diff |\n|---|---|---|---|")
    for c in ("incremental", "oracle"):
        cl = mean([f(r["all_field_acc"]) for r in rows if r["mode"] == "clean" and r["condition"] == c and r["turn"] >= 3])
        co = mean([f(r["all_field_acc"]) for r in rows if r["mode"] == "corrupt" and r["condition"] == c and r["turn"] >= 3])
        if cl is not None and co is not None:
            P(f"| {c} | {fmt(cl, True)} | {fmt(co, True)} | {100 * (co - cl):+.1f} |")

    # collateral and natural persistence
    P("\n## 4. Collateral edits and natural (non-injected) error persistence, clean mode, T2-T5\n")
    P("collateral: leaves correct in the previous record (incremental/oracle: the prior handed in; rebuild: its own "
      "previous output) and unchanged in gold this turn, but wrong after the turn. natural persistence: structured "
      "leaves wrong in the system's own previous output, gold unchanged this turn -> still the same wrong value.\n")
    P("| condition | collateral edits / opportunities | of which non-empty gold | natural: opportunities | persisted | recovered | persist rate |")
    P("|---|---|---|---|---|---|---|")
    for c in CONDS:
        sel = [r for r in rows if r["mode"] == "clean" and r["condition"] == c and r["turn"] >= 2]
        if not sel:
            continue
        ce = sum(int(r["collateral_edits"]) for r in sel)
        co = sum(int(r["collateral_opportunities"]) for r in sel)
        cn = sum(int(r["collateral_edits_nonempty"]) for r in sel)
        no = sum(int(r["nat_opportunities"]) for r in sel)
        npers = sum(int(r["nat_persisted"]) for r in sel)
        nrec = sum(int(r["nat_recovered"]) for r in sel)
        P(f"| {c} | {ce}/{co} ({fmt(ce / co if co else None, True)}%) | {cn} | {no} | {npers} | {nrec} | "
          f"{fmt(npers / no if no else None, True)}% |")

    # per questionnaire
    P("\n## 5. Per questionnaire (clean, mean all_field_acc over T1-T5, %)\n")
    P("| questionnaire | n traj | " + " | ".join(CONDS) + " |\n|---|---|" + "---|" * len(CONDS))
    for q in sorted({r["questionnaire_id"] for r in rows}):
        nt = len({r["trajectory_id"] for r in rows if r["questionnaire_id"] == q})
        vals = [mean([f(r["all_field_acc"]) for r in rows if r["mode"] == "clean" and r["condition"] == c
                      and r["questionnaire_id"] == q]) for c in CONDS]
        P(f"| {q} | {nt} | " + " | ".join(fmt(v, True) for v in vals) + " |")

    # tokens
    P("\n## 6. Tokens and cost (this run, cache hits excluded)\n")
    P("| condition | mode | billed calls | input tok | output tok | reasoning tok | mean in/call | mean out/call |")
    P("|---|---|---|---|---|---|---|---|")
    tin = tout = 0
    for mode in ("clean", "corrupt"):
        for c in CONDS:
            sel = [r for r in rows if r["mode"] == mode and r["condition"] == c and r["cache_hit"] == "0"]
            if not sel:
                continue
            ci = sum(int(r["input_tokens"]) for r in sel)
            cu = sum(int(r["output_tokens"]) for r in sel)
            cr = sum(int(r.get("reasoning_tokens") or 0) for r in sel)
            calls = sum(int(r["model_calls"]) for r in sel)
            tin += ci
            tout += cu
            P(f"| {c} | {mode} | {calls} | {ci} | {cu} | {cr} | {ci // max(calls, 1)} | {cu // max(calls, 1)} |")
    cost = tin / 1e6 * args.price_in + tout / 1e6 * args.price_out
    P(f"\nTotal billed: {tin} input + {tout} output tokens -> ~${cost:.3f} at assumed "
      f"${args.price_in}/M in, ${args.price_out}/M out.")
    retries = sum(1 for r in rows if r["cache_hit"] == "0" and int(r["attempts"] or 1) > 1)
    fallbacks = sum(1 for r in rows if r["fallback_used"] == "1")
    P(f"Turns needing a Direct retry (invalid JSON/shape): {retries}; prior-state fallbacks: {fallbacks}.")

    text = "\n".join(out) + "\n"
    (run / "closed_loop_summary.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
