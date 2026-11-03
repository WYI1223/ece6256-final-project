#!/usr/bin/env python
"""Round 2 part 4 analysis: persistence / restoration of the injected value per history regime,
summary fidelity for w3+summary, natural-error persistence, tokens and cost. No API calls.

Usage: python long_summarize.py ../runs/long [--tag k3] [--price-in 0.30 --price-out 1.20]
Writes <run>/long_summary_<tag>.md (+ summary_fidelity_<tag>.json) and prints the markdown.

Headline metrics need only the injected value and the system's OWN pre-injection value
(its turn-K output), not gold:
  survived    : candidate value at K+1 == injected value
  persistence : consecutive turns from K+1 on which the candidate still holds the injected value
  restored    : candidate == pre-injection value (first turn; and at the final turn)
Summary fidelity: a summary that covers the turn which set the corrupted fact "mentions the true
value" if a bullet line contains a surface form of the gold value (dates: ISO / "March 14" / "14 March"
/ "14th of March" / "3/14"; times: "18:45" / "6:45"; choices: the option word or a listed paraphrase)
AND, for repeat-row fields, the row anchor (last word of the row's text key, e.g. "knee"). Every
automatic label is printed with its matching line so that it can be checked by hand.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from collections import defaultdict
from pathlib import Path

REG_ORDER = ["full", "w3", "w3+summary", "w0"]
PARAPHRASE = {  # option -> extra surface forms accepted as an obvious paraphrase
    "high": ["severe", "pretty bad", "really bad", "badly", "bad"],
    "mild": ["slight", "a bit"],
    "moderate": [],
    "dark–unlit": ["unlit", "no street light", "no lights"],
    "dark–lit": ["street lights", "streetlights", "lit"],
    "dusk / dawn": ["dusk", "dawn", "twilight"],
    "snow / ice": ["snow", "ice", "icy"],
}
ROW_ANCHOR_FIELD = {"pain_details": "pain_part", "allergies": "allergen", "current_medications": "medication_name",
                    "vehicles": "role", "dietary_preferences_and_restrictions": "food_item"}


def surface_forms(gold, ftype):
    g = str(gold)
    if ftype == "date":
        d = dt.date.fromisoformat(g)
        mon = d.strftime("%B").lower()
        day = d.day
        suf = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return [g, f"{mon} {day}", f"{day} {mon}", f"{day}{suf} of {mon}", f"{mon} {day}{suf}", f"{d.month}/{day}"]
    if ftype == "time":
        h, m = map(int, g.split(":"))
        return [g, f"{h % 12 or 12}:{m:02d}"]
    if ftype in ("number", "integer"):
        return [g[:-2] if g.endswith(".0") else g]
    low = g.lower()
    return [low] + PARAPHRASE.get(low, [])


def row_anchor(traj, path):
    m = re.match(r"^(\w+)\[(\d+)\]\.(\w+)$", path)
    if not m:
        return None
    grp, i = m.group(1), int(m.group(2))
    key = ROW_ANCHOR_FIELD.get(grp)
    row = (traj["turns"][-1]["gold_state"].get(grp) or [{}])[i] if key else {}
    val = (row or {}).get(key)
    return str(val).split()[-1].lower() if val else None


def fidelity(summary_text, forms, anchor):
    for line in summary_text.splitlines():
        low = line.lower()
        if anchor and anchor not in low:
            continue
        for f in forms:
            if re.search(r"(?<![a-z0-9])" + re.escape(f.lower()) + r"(?![a-z0-9])", low):
                return True, line.strip(), f
    return False, None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--tag", default="k3")
    ap.add_argument("--price-in", type=float, default=0.30)
    ap.add_argument("--price-out", type=float, default=1.20)
    a = ap.parse_args()
    run = Path(a.run_dir)
    rows = list(csv.DictReader((run / f"long_results_{a.tag}.csv").open(encoding="utf-8")))
    meta = json.loads((run / f"run_meta_{a.tag}.json").read_text(encoding="utf-8"))
    trajs = {}
    tpath = run / "trajectories_long.jsonl"
    if tpath.exists():
        for line in tpath.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                trajs[d["trajectory_id"]] = d
    for r in rows:
        r["turn"] = int(r["turn"])
    regimes = [g for g in REG_ORDER if g in {r["regime"] for r in rows}]
    out = []
    P = out.append
    P(f"# Long-dialogue regime summary ({a.tag})\n")
    P(f"solver `{meta['solver']}`, model `{meta['model']}`, {meta['n_trajectories']} trajectories, "
      f"elapsed {meta['elapsed_s']} s, solver errors {meta['totals']['solver_errors']}.\n")

    # ---------------- injected value: persistence / restoration
    per = {}  # (regime, tid) -> dict
    for reg in regimes:
        for tid, corr in (meta["corruptions"].get(reg) or {}).items():
            if not corr:
                continue
            k = corr["after_turn"]
            sel = sorted((r for r in rows if r["regime"] == reg and r["trajectory_id"] == tid and r["mode"] == "corrupt"
                          and r["condition"] == "incremental" and r["turn"] > k), key=lambda r: r["turn"])
            if not sel:
                continue
            pers = [int(r["persisted_error"] or 0) for r in sel]
            rest = [int(r["restored_pre_injection"] or 0) for r in sel]
            streak = 0
            for p in pers:
                if not p:
                    break
                streak += 1
            first_rest = next((r["turn"] for r, x in zip(sel, rest) if x), None)
            final = sel[-1]
            outcome = ("restored" if rest[-1] else "persisted" if pers[-1] else
                       f"other:{final['candidate_value_of_corrupted']}")
            per[(reg, tid)] = {
                "field": corr["path"], "set_turn": corr.get("set_turn"), "K": k,
                "injected": corr["wrong_value"], "pre": corr.get("pre_injection_value"),
                "system_correct_before": corr.get("system_correct_before"),
                "survived_first": pers[0], "persistence": streak, "max_persistence": len(pers),
                "restored_final": rest[-1], "first_restored_turn": first_rest, "final_outcome": outcome,
                "relapse": int(any(p for p in pers[streak:]) and streak < len(pers)),
                "persist_seq": "".join(str(p) for p in pers), "restore_seq": "".join(str(x) for x in rest),
            }
    P("\n## Injected value (incremental, corrupt mode)\n")
    P("survived = still holds the injected value at the first post-injection turn; persistence = consecutive turns "
      "holding it; restored = equals the system's own pre-injection value (not gold).\n")
    P("| regime | n | survived first turn | mean persistence (max) | restored by T15 | first-restore turns | persisted to T15 | other final value |")
    P("|---|---|---|---|---|---|---|---|")
    for reg in regimes:
        d = [v for (g, _), v in per.items() if g == reg]
        if not d:
            continue
        n = len(d)
        mx = d[0]["max_persistence"]
        P(f"| {reg} | {n} | {sum(x['survived_first'] for x in d)}/{n} | "
          f"{sum(x['persistence'] for x in d) / n:.2f} ({mx}) | {sum(x['restored_final'] for x in d)}/{n} | "
          f"{sorted(x['first_restored_turn'] for x in d if x['first_restored_turn'])} | "
          f"{sum(1 for x in d if x['final_outcome'] == 'persisted')}/{n} | "
          f"{sum(1 for x in d if x['final_outcome'].startswith('other'))}/{n} |")
    P("\n### Per trajectory (persist sequence from turn K+1; 1 = injected value held)\n")
    P("| regime | trajectory | field (set turn) | injected -> pre | persist seq | restore seq | first restored | final |")
    P("|---|---|---|---|---|---|---|---|")
    for (reg, tid), v in sorted(per.items(), key=lambda kv: (REG_ORDER.index(kv[0][0]), kv[0][1])):
        P(f"| {reg} | {tid} | {v['field']} (t{v['set_turn']}) | {v['injected']} -> {v['pre']} | {v['persist_seq']} | "
          f"{v['restore_seq']} | {v['first_restored_turn'] or '-'} | {v['final_outcome']} |")

    # ---------------- natural persistence + clean structured accuracy (gold NOT reviewed)
    P("\n## Natural structured errors and clean accuracy (vs UNREVIEWED generator gold; secondary)\n")
    P("| regime | nat. carried | persisted | recovered | clean structured acc, mean T4-T15 | clean all-field acc, mean T4-T15 |")
    P("|---|---|---|---|---|---|")
    for reg in regimes:
        sel = [r for r in rows if r["regime"] == reg and r["mode"] == "clean" and r["condition"] == "incremental"]
        no = sum(int(r["nat_opportunities"] or 0) for r in sel)
        npers = sum(int(r["nat_persisted"] or 0) for r in sel)
        nrec = sum(int(r["nat_recovered"] or 0) for r in sel)
        late = [r for r in sel if r["turn"] >= 4]
        sa = [float(r["structured_acc"]) for r in late if r["structured_acc"] not in ("", None)]
        aa = [float(r["all_field_acc"]) for r in late if r["all_field_acc"] not in ("", None)]
        P(f"| {reg} | {no} | {npers} ({100 * npers / no:.0f}%) | {nrec} | {100 * sum(sa) / len(sa):.1f} | "
          f"{100 * sum(aa) / len(aa):.1f} |" if no and sa else f"| {reg} | {no} | {npers} | {nrec} | - | - |")

    # ---------------- summary fidelity
    fid_records = []
    summ_path = run / "summaries.jsonl"
    if "w3+summary" in regimes and summ_path.exists():
        summaries = {}
        for line in summ_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)["result"]
                summaries[(rec["trajectory_id"], rec["upto"])] = rec["summary"]
        for tid, corr in (meta["corruptions"].get("w3+summary") or {}).items():
            if not corr or tid not in trajs:
                continue
            ftype = next((c["field_type"] for c in trajs[tid]["corruption"]["candidates"] if c["path"] == corr["path"]), "")
            forms = surface_forms(corr["gold_value"], ftype)
            anchor = row_anchor(trajs[tid], corr["path"])
            for (t2, upto), text in sorted(summaries.items()):
                if t2 != tid or upto < (corr.get("set_turn") or 1):
                    continue
                ok, line, form = fidelity(text, forms, anchor)
                v = per.get(("w3+summary", tid), {})
                turn = upto + 4  # summary covering turns 1..upto is used at turn upto+4
                fid_records.append({"trajectory_id": tid, "field": corr["path"], "gold": corr["gold_value"],
                                    "summary_upto": upto, "used_at_turn": turn, "auto_mentions_true_value": ok,
                                    "matched_form": form, "matched_line": line, "anchor": anchor})
        P("\n## Summary fidelity (w3+summary): does the summary state the corrupted field's TRUE value?\n")
        P("Only summaries that cover the turn that set the fact are counted (the fact is out of the window). "
          "Auto label = bullet line containing a surface form of the gold value (and the row anchor for repeat rows); "
          "every label is listed in summary_fidelity_<tag>.json with its matched line for hand checking.\n")
        P("| trajectory | field | anchor | summaries covering fact | mention true value (auto) | used at turns |")
        P("|---|---|---|---|---|---|")
        by = defaultdict(list)
        for f in fid_records:
            by[f["trajectory_id"]].append(f)
        tot = hit = 0
        for tid, fs in sorted(by.items()):
            k = sum(1 for f in fs if f["auto_mentions_true_value"])
            tot += len(fs)
            hit += k
            P(f"| {tid} | {fs[0]['field']} | {fs[0]['anchor'] or '-'} | {len(fs)} | {k} | "
              f"{fs[0]['used_at_turn']}-{fs[-1]['used_at_turn']} |")
        if tot:
            P(f"\nOverall: {hit}/{tot} summaries ({100 * hit / tot:.0f}%) mention the true value.\n")
        (run / f"summary_fidelity_{a.tag}.json").write_text(json.dumps(fid_records, indent=1, ensure_ascii=False),
                                                         encoding="utf-8")

    # ---------------- cost
    P("\n## Tokens and cost (this tag's run; cache hits excluded)\n")
    P("| regime | billed solver calls | input tok | output tok | summary calls | summary in | summary out | USD |")
    P("|---|---|---|---|---|---|---|---|")
    for reg in regimes:
        b = meta["by_regime"][reg]
        usd = ((b["billed_input_tokens"] + b["summary_input_tokens"]) * a.price_in
               + (b["billed_output_tokens"] + b["summary_output_tokens"]) * a.price_out) / 1e6
        P(f"| {reg} | {b['billed_solver_calls']} | {b['billed_input_tokens']:,} | {b['billed_output_tokens']:,} | "
          f"{b['summary_calls']} | {b['summary_input_tokens']:,} | {b['summary_output_tokens']:,} | {usd:.3f} |")
    b = meta["totals"]
    usd = ((b["billed_input_tokens"] + b["summary_input_tokens"]) * a.price_in
           + (b["billed_output_tokens"] + b["summary_output_tokens"]) * a.price_out) / 1e6
    P(f"| **total** | {b['billed_solver_calls']} | {b['billed_input_tokens']:,} | {b['billed_output_tokens']:,} | "
      f"{b['summary_calls']} | {b['summary_input_tokens']:,} | {b['summary_output_tokens']:,} | {usd:.3f} |")
    # cache-wide totals: every persisted cache entry was billed exactly once, whichever invocation made it
    ci = co = cn = 0
    for name in ("solver_cache.jsonl", "summaries.jsonl"):
        f = run / name
        if f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)["result"]
                    ci += int(r.get("input_tokens") or 0)
                    co += int(r.get("output_tokens") or 0)
                    cn += 1
    P(f"\nAll runs in this out-dir so far (solver_cache.jsonl + summaries.jsonl, {cn} billed calls): "
      f"{ci:,} in / {co:,} out = ${(ci * a.price_in + co * a.price_out) / 1e6:.3f}.")
    gl = run / "trajectories_long_generation_log.json"
    if gl.exists():
        g = json.loads(gl.read_text(encoding="utf-8"))["summary"]
        P(f"\nTrajectory generation: {g['attempts_total']} calls, {g['input_tokens']:,} in / {g['output_tokens']:,} out "
          f"= ${(g['input_tokens'] * a.price_in + g['output_tokens'] * a.price_out) / 1e6:.3f}.")
    text = "\n".join(out) + "\n"
    (run / f"long_summary_{a.tag}.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
