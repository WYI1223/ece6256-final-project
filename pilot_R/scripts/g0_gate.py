"""Step 3: G0 identity gate (enrolled-speaker gating baseline, in the spirit of pVAD / IRAF).

For every clip:
  1. enrollment embedding = ECAPA(input.wav[0:t0] minus silence)  (user's own pre-overlap speech)
  2. chunk input.wav into non-overlapping 0.5 s windows; for each window with speech energy,
     compute ECAPA cosine to the enrollment embedding.  (--ctx S optionally uses a causal
     S-second context window ending at the current window's end, for a more stable embedding.)
  3. mute (zero) windows whose similarity < threshold; silent windows are left untouched.
  4. write gated wav to runs/g0/<tag>/<scenario>/<id>.wav (same sr/length -> can be fed to Moshi
     as the gated user channel later).

Metrics per scenario (on speech-active 20 ms frames only):
  muted_overlap_frac : fraction of active overlap-window audio [t0,t1] zeroed
  muted_preoverlap_frac : fraction of active pre-overlap user speech zeroed
  clip_overlap_mostly_muted : fraction of clips with >=50% of overlap audio muted

Threshold: by default chosen on even-id clips as the window-level EER between bkg_speech overlap
windows (should be muted) and user_interruption overlap windows (must pass); reported on all clips
and on the odd-id held-out half. A fixed-threshold sweep is also written.

Usage: python -I scripts/g0_gate.py [--win 0.5] [--ctx 0] [--thr auto|<float>] [--write_wavs 1]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import soundfile as sf
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RUNS, SCENARIOS, ensure_16k, list_ids, load_clip, mono  # noqa: E402
from spk_similarity import drop_silence, embed, load_ecapa  # noqa: E402


def active_mask(x, sr, frame=0.02, abs_db=-50.0, rel_db=-40.0, ref_db=None):
    n = int(frame * sr)
    nf = len(x) // n
    fr = x[: nf * n].reshape(nf, n)
    e = 10 * np.log10((fr.astype(np.float64) ** 2).mean(axis=1) + 1e-12)
    ref = e.max() if ref_db is None else ref_db
    return (e > abs_db) & (e > ref + rel_db), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--win", type=float, default=0.5)
    ap.add_argument("--ctx", type=float, default=0.0, help="causal context seconds for the embedding (0 = window only)")
    ap.add_argument("--thr", default="auto")
    ap.add_argument("--write_wavs", type=int, default=1)
    ap.add_argument("--min_active", type=float, default=0.2, help="min active fraction for a window to be scored")
    args = ap.parse_args()
    tag = f"win{args.win}_ctx{args.ctx}"
    out = RUNS / "g0" / tag
    out.mkdir(parents=True, exist_ok=True)
    model = load_ecapa()

    # ---------- pass 1: per-window similarities ----------
    clips = []
    for scn in SCENARIOS:
        for cid in list_ids(scn):
            c = load_clip(scn, cid)
            x, sr = c["input.wav"]
            x = mono(x).astype(np.float32)
            t0, t1 = c["meta"]["timestamps"][:2]
            e_enr = embed(model, ensure_16k(drop_silence(x[: int(t0 * sr)], sr), sr))
            act, fn = active_mask(x, sr)
            W = int(args.win * sr)
            C = int(args.ctx * sr)
            L = max(W, C)                     # fixed segment length -> batchable
            wins, segs, idx = [], [], []
            for ws in range(0, len(x), W):
                we = min(ws + W, len(x))
                f0, f1 = ws // fn, min(we // fn, len(act))
                af = act[f0:f1].mean() if f1 > f0 else 0.0
                if af < args.min_active or (we - ws) < W:
                    wins.append([ws, we, np.nan, af])
                    continue
                s0 = we - L if we - L >= 0 else ws   # causal context window ending at window end
                segs.append(x[s0:s0 + L] if we - L >= 0 else x[ws:we])
                idx.append(len(wins))
                wins.append([ws, we, np.nan, af])
            by_len = {}
            for j, sg in zip(idx, segs):
                by_len.setdefault(len(sg), []).append((j, sg))
            for _, items in by_len.items():
                B = torch.from_numpy(np.stack([ensure_16k(sg, sr) for _, sg in items]).astype(np.float32))
                Emb = torch.nn.functional.normalize(model.encode_batch(B).squeeze(1), dim=-1).numpy()
                for (j, _), e in zip(items, Emb):
                    wins[j][2] = float(np.dot(e_enr, e))
            wins = [tuple(w) for w in wins]
            clips.append(dict(scn=scn, id=cid, sr=sr, x=x, t0=t0, t1=t1, act=act, fn=fn, wins=wins))
        print(scn, "windows scored", flush=True)

    def win_label(cl, ws, we):
        t0s, t1s = int(cl["t0"] * cl["sr"]), int(cl["t1"] * cl["sr"])
        ov = max(0, min(we, t1s) - max(ws, t0s)) / (we - ws)
        return "overlap" if ov >= 0.5 else ("pre" if we <= t0s else "other")

    wrows = []
    for cl in clips:
        for ws, we, s, af in cl["wins"]:
            wrows.append(dict(scenario=cl["scn"], id=cl["id"], ws=ws / cl["sr"], we=we / cl["sr"], sim=s,
                              active=af, region=win_label(cl, ws, we)))
    wdf = pd.DataFrame(wrows)
    wdf.to_csv(out / "windows.csv", index=False)
    scored = wdf.dropna(subset=["sim"])

    # ---------- threshold ----------
    grid = np.linspace(-0.2, 1.0, 601)
    def eer_thr(sub):
        pos = sub[(sub.scenario == "user_interruption") & (sub.region == "overlap")].sim.values
        neg = sub[(sub.scenario == "bkg_speech") & (sub.region == "overlap")].sim.values
        d = [abs((pos < t).mean() - (neg >= t).mean()) for t in grid]
        return float(grid[int(np.argmin(d))])
    even = scored.id.astype(int) % 2 == 0
    thr = eer_thr(scored[even]) if args.thr == "auto" else float(args.thr)

    # ---------- pass 2: gate + metrics ----------
    def gate_and_score(t, write=False):
        rows = []
        for cl in clips:
            x, sr, fn, act = cl["x"], cl["sr"], cl["fn"], cl["act"]
            keep = np.ones(len(x), dtype=bool)
            for ws, we, s, af in cl["wins"]:
                if not np.isnan(s) and s < t:
                    keep[ws:we] = False
            y = np.where(keep, x, 0.0).astype(np.float32)
            fkeep = keep[: len(act) * fn].reshape(len(act), fn).mean(axis=1) > 0.5
            fidx = np.arange(len(act)) * fn
            t0s, t1s = int(cl["t0"] * sr), int(cl["t1"] * sr)
            ov = act & (fidx >= t0s) & (fidx < t1s)
            pre = act & (fidx < t0s)
            m_ov = float((~fkeep[ov]).mean()) if ov.any() else np.nan
            m_pre = float((~fkeep[pre]).mean()) if pre.any() else np.nan
            rows.append(dict(scenario=cl["scn"], id=cl["id"], muted_overlap_frac=m_ov, muted_preoverlap_frac=m_pre))
            if write:
                d = out / "wavs" / cl["scn"]
                d.mkdir(parents=True, exist_ok=True)
                sf.write(d / f"{cl['id']}.wav", y, sr, subtype="PCM_16")
        return pd.DataFrame(rows)

    def summarize(df):
        res = {}
        for scn, g in df.groupby("scenario", sort=False):
            res[scn] = {
                "n": int(len(g)),
                "muted_overlap_frac_mean": round(float(g.muted_overlap_frac.mean()), 3),
                "muted_overlap_frac_median": round(float(g.muted_overlap_frac.median()), 3),
                "clips_overlap_mostly_muted(>=50%)": round(float((g.muted_overlap_frac >= 0.5).mean()), 3),
                "muted_preoverlap_user_speech_frac_mean": round(float(g.muted_preoverlap_frac.mean()), 4),
            }
        return res

    cdf = gate_and_score(thr, write=bool(args.write_wavs))
    cdf.to_csv(out / "clips.csv", index=False)
    res = {"tag": tag, "threshold": round(thr, 3),
           "threshold_rule": "window-level EER (bkg_speech overlap vs user_interruption overlap), tuned on even ids" if args.thr == "auto" else "fixed",
           "all": summarize(cdf), "heldout_odd_ids": summarize(cdf[cdf.id.astype(int) % 2 == 1])}
    # window-level stats
    res["window_sim_by_scenario_region"] = {
        f"{s}/{r}": {"n": int(len(g)), "median": round(float(g.sim.median()), 3),
                     "p10": round(float(g.sim.quantile(.1)), 3), "p90": round(float(g.sim.quantile(.9)), 3)}
        for (s, r), g in scored.groupby(["scenario", "region"]) if r != "other"}
    sweep = []
    for t in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]:
        sm = summarize(gate_and_score(t))
        sweep.append({"thr": t, **{f"{k}_muted_ovl": v["muted_overlap_frac_mean"] for k, v in sm.items()},
                      **{f"{k}_muted_pre": v["muted_preoverlap_user_speech_frac_mean"] for k, v in sm.items()}})
    res["sweep"] = sweep
    (out / "summary.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        order = ["bkg_speech", "talking_other", "user_interruption", "user_backchannel"]
        vals = [res["all"][s]["muted_overlap_frac_mean"] for s in order]
        cols = ["#36c", "#d52", "#2a7", "#7a2"]
        fig, ax = plt.subplots(figsize=(6.4, 3.4))
        b = ax.bar(order, vals, color=cols)
        for r, v in zip(b, vals):
            ax.text(r.get_x() + r.get_width() / 2, v + 0.02, f"{v:.2f}", ha="center")
        ax.set_ylim(0, 1.08)
        ax.set_ylabel("fraction of overlap speech muted")
        ax.set_title(f"G0 identity gate ({args.win}s windows, ctx={args.ctx}s, thr={thr:.2f})", fontsize=10)
        fig.tight_layout()
        fig.savefig(out / "g0_mute_rates.png", dpi=130)
    except Exception as ex:  # noqa: BLE001
        print("plot failed", ex)


if __name__ == "__main__":
    with torch.no_grad():
        main()
