"""Step 1: map the FDB v1.5 overlap data (counts, sr, channels, durations, timestamps,
levels of the overlap relative to the user's own speech, spectral tilt of the overlap).

Usage: python -I scripts/inventory.py   (writes runs/inventory/*.csv + summary.json)
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RUNS, SCENARIOS, active_rms_db, list_ids, load_clip, mono  # noqa: E402

OUT = RUNS / "inventory"
OUT.mkdir(parents=True, exist_ok=True)


def hf_ratio_db(x, sr, cut=4000.0):
    """Energy above `cut` Hz relative to total (dB). Lower => darker (low-pass / shelf cut)."""
    X = np.abs(np.fft.rfft(x.astype(np.float64))) ** 2
    f = np.fft.rfftfreq(len(x), 1 / sr)
    return 10 * np.log10(X[f >= cut].sum() / (X.sum() + 1e-20) + 1e-20)


rows = []
meta_keys = {}
for scn, (folder, ov_name, key) in SCENARIOS.items():
    keys = Counter()
    for cid in list_ids(scn):
        c = load_clip(scn, cid)
        keys.update(c["meta"].keys())
        x, sr = c["input.wav"]
        xc, src = c["clean_input.wav"]
        ctx, srx = c["context.wav"]
        ov, sro = c[ov_name] if ov_name in c else (None, None)
        t0, t1 = c["meta"]["timestamps"][:2]
        xm, xcm = mono(x), mono(xc)
        n = min(len(xm), len(xcm))
        resid = xm[:n] - xcm[:n]
        i0, i1 = int(t0 * sr), int(t1 * sr)
        in_win = resid[i0:i1]
        out_win = np.concatenate([resid[:i0], resid[i1:]])
        ctxm = mono(ctx)
        r = dict(
            scenario=scn, id=cid, sr=sr, channels=x.shape[1], dur_input=len(xm) / sr,
            dur_clean=len(xcm) / src, dur_context=len(ctxm) / srx,
            dur_overlap_wav=(len(ov) / sro) if ov is not None else np.nan,
            t0=t0, t1=t1, win=t1 - t0,
            # residual (input - clean) energy inside vs outside the annotated window
            resid_in_db=active_rms_db(in_win, sr) if len(in_win) else np.nan,
            resid_out_maxabs=float(np.abs(out_win).max()) if len(out_win) else 0.0,
            ctx_active_db=active_rms_db(ctxm, srx),
            ov_raw_active_db=active_rms_db(mono(ov), sro) if ov is not None else np.nan,
            hf_ctx_db=hf_ratio_db(ctxm, srx),
            hf_resid_db=hf_ratio_db(in_win, sr) if len(in_win) > 256 else np.nan,
            overlap_text=c["overlap_text"], context_text=c["context_text"],
        )
        r["overlap_rel_db"] = r["resid_in_db"] - r["ctx_active_db"]  # level of overlap in input vs user speech
        r["hf_tilt_vs_ctx_db"] = r["hf_resid_db"] - r["hf_ctx_db"]
        rows.append(r)
    meta_keys[scn] = dict(keys)

df = pd.DataFrame(rows)
df.to_csv(OUT / "clips.csv", index=False)

summ = {}
for scn, g in df.groupby("scenario", sort=False):
    summ[scn] = {
        "n_clips": int(len(g)), "sr": sorted(g.sr.unique().tolist()), "channels": sorted(g.channels.unique().tolist()),
        "dur_input_mean": round(g.dur_input.mean(), 2), "dur_input_range": [round(g.dur_input.min(), 2), round(g.dur_input.max(), 2)],
        "t0_mean": round(g.t0.mean(), 2), "t0_range": [round(g.t0.min(), 2), round(g.t0.max(), 2)],
        "win_mean": round(g.win.mean(), 2), "win_range": [round(g.win.min(), 2), round(g.win.max(), 2)],
        "dur_context_mean": round(g.dur_context.mean(), 2),
        "gap_ctx_end_to_t0_mean": round((g.t0 - g.dur_context).mean(), 2),
        "overlap_wav_vs_window_absdiff_mean": round((g.dur_overlap_wav - g.win).abs().mean(), 3),
        "resid_outside_window_maxabs_max": round(g.resid_out_maxabs.max(), 5),
        "overlap_rel_db_median": round(g.overlap_rel_db.median(), 2),
        "overlap_rel_db_p10_p90": [round(g.overlap_rel_db.quantile(.1), 2), round(g.overlap_rel_db.quantile(.9), 2)],
        "hf_tilt_vs_ctx_db_median": round(g.hf_tilt_vs_ctx_db.median(), 2),
        "metadata_keys": meta_keys[scn],
    }
(OUT / "summary.json").write_text(json.dumps(summ, indent=2))
print(json.dumps(summ, indent=2))
for scn, g in df.groupby("scenario", sort=False):
    print(f"\n== {scn}: 8 example overlap texts")
    for t in g.overlap_text.head(8):
        print("   ", t)
