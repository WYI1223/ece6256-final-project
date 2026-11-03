"""Step 2b: independent check of the same-voice construction and of user-voice diversity.

(a) F0 (median over voiced frames, torchaudio detect_pitch_frequency) of the user's context.wav vs the
    raw overlap file, per clip -> |dF0| per scenario.  Same TTS voice => small |dF0| (prosody differs a bit).
(b) Voice diversity: distribution of context F0 across clips (one voice => one tight mode).
(c) ECAPA within-clip vs cross-clip: is the overlap closer to ITS OWN user's enrollment than to the
    enrollment of a different clip?  (rank of the true enrollment among all enrollments of the scenario)

Usage: python -I scripts/voice_check.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torchaudio.functional as AF

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RUNS, SCENARIOS, ensure_16k, list_ids, load_clip, mono  # noqa: E402
from spk_similarity import drop_silence, embed, load_ecapa  # noqa: E402

OUT = RUNS / "similarity"


def f0_median(x, sr):
    x = drop_silence(x, sr)
    if len(x) < sr * 0.3:
        return np.nan
    p = AF.detect_pitch_frequency(torch.from_numpy(np.ascontiguousarray(x)).float()[None], sr,
                                  frame_time=0.02, win_length=15, freq_low=65, freq_high=400)[0].numpy()
    p = p[(p > 65) & (p < 400)]
    return float(np.median(p)) if len(p) else np.nan


def main():
    model = load_ecapa()
    rows, emb = [], {}
    for scn, (folder, ov_name, key) in SCENARIOS.items():
        for cid in list_ids(scn):
            c = load_clip(scn, cid)
            ctx, sr = c["context.wav"]
            ov, sro = c[ov_name]
            ctx, ov = mono(ctx), mono(ov)
            x, srx = c["input.wav"]
            x = mono(x)
            t0, t1 = c["meta"]["timestamps"][:2]
            e_enr = embed(model, ensure_16k(drop_silence(x[: int(t0 * srx)], srx), srx))
            e_ovl = embed(model, ensure_16k(drop_silence(x[int(t0 * srx): int(t1 * srx)], srx), srx))
            emb[(scn, cid)] = (e_enr, e_ovl)
            rows.append(dict(scenario=scn, id=cid, f0_ctx=f0_median(ctx, sr), f0_ovl=f0_median(ov, sro)))
        print(scn, "done", flush=True)
    df = pd.DataFrame(rows)
    df["df0_abs"] = (df.f0_ctx - df.f0_ovl).abs()
    df["df0_semitones"] = 12 * np.log2(df.f0_ovl / df.f0_ctx)

    res = {}
    for scn, g in df.groupby("scenario", sort=False):
        keys = [k for k in emb if k[0] == scn]
        E = np.stack([emb[k][0] for k in keys])
        O = np.stack([emb[k][1] for k in keys])
        S = O @ E.T                                     # overlap_i vs enrollment_j
        within = np.diag(S)
        cross = S[~np.eye(len(keys), dtype=bool)]
        rank = (S > within[:, None]).sum(axis=1) + 1    # 1 = own enrollment is the closest
        res[scn] = {
            "f0_ctx_median_hz": round(float(g.f0_ctx.median()), 1),
            "f0_ctx_p10_p90": [round(float(g.f0_ctx.quantile(.1)), 1), round(float(g.f0_ctx.quantile(.9)), 1)],
            "f0_ctx_frac_below_165hz(male-like)": round(float((g.f0_ctx < 165).mean()), 3),
            "f0_ovl_median_hz": round(float(g.f0_ovl.median()), 1),
            "abs_semitone_diff_ctx_vs_ovl_median": round(float(g.df0_semitones.abs().median()), 2),
            "frac_abs_semitone_diff>4": round(float((g.df0_semitones.abs() > 4).mean()), 3),
            "ecapa_within_clip_mean": round(float(within.mean()), 3),
            "ecapa_cross_clip_mean": round(float(cross.mean()), 3),
            "ecapa_cross_clip_p90": round(float(np.quantile(cross, .9)), 3),
            "own_enrollment_rank_median(of_n)": f"{int(np.median(rank))} of {len(keys)}",
            "own_enrollment_top1_frac": round(float((rank == 1).mean()), 3),
            "own_enrollment_top5_frac": round(float((rank <= 5).mean()), 3),
        }
    # cross-scenario: are the users of different scenarios the same voices? (enrollment-enrollment)
    E_all = {s: np.stack([emb[k][0] for k in emb if k[0] == s]) for s in SCENARIOS}
    res["enroll_vs_enroll_mean"] = {f"{a}~{b}": round(float((E_all[a] @ E_all[b].T).mean()), 3)
                                    for a in SCENARIOS for b in SCENARIOS if a <= b}
    df.to_csv(OUT / "voice_check.csv", index=False)
    (OUT / "voice_check.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    # coarse F0 histogram of user voices
    h, edges = np.histogram(df.f0_ctx.dropna(), bins=np.arange(60, 420, 20))
    print("context F0 histogram (all scenarios):")
    for c, e in zip(h, edges):
        print(f"  {int(e):3d}-{int(e) + 20:3d} Hz {'#' * int(c // 4)} {c}")


if __name__ == "__main__":
    with torch.no_grad():
        main()
