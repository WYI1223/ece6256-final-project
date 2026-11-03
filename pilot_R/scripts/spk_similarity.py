"""Step 2: ECAPA-TDNN speaker similarity between the user's enrollment speech and the overlap.

Enrollment  = input.wav[0 : t0] (everything the user said before the overlap onset; in FDB v1.5
              this is the context question followed by silence), with silent 20 ms frames dropped.
Overlap     = input.wav[t0 : t1] using the metadata timestamps (exact, provided by FDB).
Also        = the raw overlap file (current_turn.wav / background.wav / backchannel.wav /
              interrupt.wav) BEFORE mixing, to separate "voice identity" from "mixing/processing".
Impostor    = enrollment of clip i vs overlap of a random other clip j in the same scenario
              (gives a different-voice reference distribution if the clips use several voices).

Usage: python -I scripts/spk_similarity.py [--max_per_scn N]
Outputs: runs/similarity/sims.csv, summary.json, threshold.json, hist.png
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RUNS, SCENARIOS, ensure_16k, list_ids, load_clip, mono  # noqa: E402

OUT = RUNS / "similarity"
OUT.mkdir(parents=True, exist_ok=True)


def load_ecapa():
    from speechbrain.inference.speaker import EncoderClassifier
    from speechbrain.utils.fetching import LocalStrategy  # COPY: Windows has no unprivileged symlinks
    return EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir=str(RUNS / "models" / "spkrec-ecapa-voxceleb"),
        run_opts={"device": "cpu"},
        local_strategy=LocalStrategy.COPY,
    )


def drop_silence(x, sr, frame=0.02, rel_db=-40.0, abs_db=-60.0):
    n = int(frame * sr)
    if len(x) < n:
        return x
    fr = x[: len(x) // n * n].reshape(-1, n)
    e = 10 * np.log10((fr.astype(np.float64) ** 2).mean(axis=1) + 1e-12)
    keep = (e > e.max() + rel_db) & (e > abs_db)
    return fr[keep].reshape(-1) if keep.any() else x


@torch.no_grad()
def embed(model, x16):
    w = torch.from_numpy(np.ascontiguousarray(x16, dtype=np.float32))[None]
    e = model.encode_batch(w).squeeze()
    return torch.nn.functional.normalize(e, dim=-1).numpy()


def cos(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max_per_scn", type=int, default=0, help="0 = all clips")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    model = load_ecapa()

    rows, store = [], {}
    for scn, (folder, ov_name, key) in SCENARIOS.items():
        ids = list_ids(scn)
        if args.max_per_scn:
            ids = ids[: args.max_per_scn]
        for cid in ids:
            c = load_clip(scn, cid)
            x, sr = c["input.wav"]
            x = mono(x)
            t0, t1 = c["meta"]["timestamps"][:2]
            enr = drop_silence(x[: int(t0 * sr)], sr)
            ovl = x[int(t0 * sr): int(t1 * sr)]
            ovl_ns = drop_silence(ovl, sr)
            e_enr = embed(model, ensure_16k(enr, sr))
            e_ovl = embed(model, ensure_16k(ovl_ns, sr))
            raw = mono(c[ov_name][0]) if ov_name in c else None
            e_raw = embed(model, ensure_16k(drop_silence(raw, c[ov_name][1]), c[ov_name][1])) if raw is not None else None
            ctx = mono(c["context.wav"][0])
            e_ctx = embed(model, ensure_16k(drop_silence(ctx, c["context.wav"][1]), c["context.wav"][1]))
            store[(scn, cid)] = (e_enr, e_ovl)
            rows.append(dict(
                scenario=scn, id=cid, t0=t0, t1=t1,
                enr_sec=len(enr) / sr, ovl_sec=len(ovl_ns) / sr,
                sim=cos(e_enr, e_ovl),                      # main: enrollment vs overlap as heard in input.wav
                sim_raw=cos(e_enr, e_raw) if e_raw is not None else np.nan,  # vs un-mixed overlap file
                sim_ctxfile_raw=cos(e_ctx, e_raw) if e_raw is not None else np.nan,  # both raw files
                overlap_text=c["overlap_text"],
            ))
        print(scn, len(ids), "done", flush=True)

    df = pd.DataFrame(rows)
    # impostor: enrollment of clip i vs overlap of another random clip j (same scenario)
    imp = []
    for scn in SCENARIOS:
        keys = [k for k in store if k[0] == scn]
        for k in keys:
            j = keys[rng.integers(len(keys))]
            while j == k:
                j = keys[rng.integers(len(keys))]
            imp.append(cos(store[k][0], store[j][1]))
    df_imp = pd.DataFrame({"scenario": "impostor_crossclip", "sim": imp})
    df.to_csv(OUT / "sims.csv", index=False)
    df_imp.to_csv(OUT / "impostor.csv", index=False)

    # enrollment-vs-enrollment across clips: how many distinct user voices?
    enr_keys = [k for k in store if k[0] == "talking_other"]
    E = np.stack([store[k][0] for k in enr_keys])
    S = E @ E.T
    iu = np.triu_indices(len(E), 1)
    voice = {"talking_other_enrollment_crossclip_sim_mean": float(S[iu].mean()),
             "p10": float(np.quantile(S[iu], .1)), "p90": float(np.quantile(S[iu], .9))}
    try:
        from scipy.cluster.hierarchy import fcluster, linkage
        Z = linkage(E, "average", metric="cosine")
        for thr in (0.3, 0.4, 0.5):
            voice[f"n_clusters_cosdist<{thr}"] = int(fcluster(Z, t=thr, criterion="distance").max())
    except Exception as ex:  # noqa: BLE001
        voice["cluster_error"] = str(ex)

    def dist(s):
        s = np.asarray(s, dtype=float)
        s = s[~np.isnan(s)]
        return {"n": int(len(s)), "mean": round(float(s.mean()), 3), "median": round(float(np.median(s)), 3),
                "p10": round(float(np.quantile(s, .1)), 3), "p90": round(float(np.quantile(s, .9)), 3),
                "min": round(float(s.min()), 3), "max": round(float(s.max()), 3)}

    summ = {scn: {"sim_input_window": dist(g.sim), "sim_raw_overlap_file": dist(g.sim_raw),
                  "ovl_speech_sec_median": round(float(g.ovl_sec.median()), 2)}
            for scn, g in df.groupby("scenario", sort=False)}
    summ["impostor_crossclip"] = {"sim_input_window": dist(imp)}
    summ["voice_diversity"] = voice

    # ---- threshold analysis: tune on bkg_speech (negative) vs user_interruption (positive) ----
    pos = df[df.scenario == "user_interruption"].sim.values
    neg = df[df.scenario == "bkg_speech"].sim.values
    grid = np.linspace(-0.2, 1.0, 1201)
    tpr = np.array([(pos >= t).mean() for t in grid])
    fpr = np.array([(neg >= t).mean() for t in grid])
    i_eer = int(np.argmin(np.abs((1 - tpr) - fpr)))
    i_bal = int(np.argmax(tpr - fpr))
    ok95 = np.where(tpr >= 0.95)[0]
    i_95 = int(ok95[-1]) if len(ok95) else 0
    auc = float(np.mean([(p > n) + 0.5 * (p == n) for p in pos for n in neg]))
    thr = {}
    for name, i in [("eer", i_eer), ("youden", i_bal), ("tpr95_interruption", i_95)]:
        t = float(grid[i])
        thr[name] = {
            "threshold": round(t, 3),
            "interruption_accepted": round(float((pos >= t).mean()), 3),
            "bkg_speech_accepted": round(float((neg >= t).mean()), 3),
            "talking_other_accepted_as_user": round(float((df[df.scenario == "talking_other"].sim >= t).mean()), 3),
            "backchannel_accepted": round(float((df[df.scenario == "user_backchannel"].sim >= t).mean()), 3),
            "impostor_crossclip_accepted": round(float((np.asarray(imp) >= t).mean()), 3),
        }
    thr["auc_interruption_vs_bkg"] = round(auc, 4)
    # AUC of talking_other vs bkg (how separable is side-talk from background by identity)
    to = df[df.scenario == "talking_other"].sim.values
    thr["auc_talking_other_vs_bkg"] = round(float(np.mean([(p > n) + 0.5 * (p == n) for p in to for n in neg])), 4)
    thr["auc_interruption_vs_talking_other"] = round(float(np.mean([(p > n) + 0.5 * (p == n) for p in pos for n in to])), 4)
    # held-out check: tune EER threshold on even ids, evaluate on odd ids
    ev = df.id.astype(int) % 2 == 0
    p_e, n_e = df[ev & (df.scenario == "user_interruption")].sim.values, df[ev & (df.scenario == "bkg_speech")].sim.values
    t_e = grid[int(np.argmin(np.abs(np.array([(p_e < t).mean() - (n_e >= t).mean() for t in grid]))))]
    od = ~ev
    thr["heldout_eer_even->odd"] = {
        "threshold": round(float(t_e), 3),
        "interruption_accepted": round(float((df[od & (df.scenario == "user_interruption")].sim >= t_e).mean()), 3),
        "bkg_speech_accepted": round(float((df[od & (df.scenario == "bkg_speech")].sim >= t_e).mean()), 3),
        "talking_other_accepted_as_user": round(float((df[od & (df.scenario == "talking_other")].sim >= t_e).mean()), 3),
        "backchannel_accepted": round(float((df[od & (df.scenario == "user_backchannel")].sim >= t_e).mean()), 3),
    }
    (OUT / "summary.json").write_text(json.dumps(summ, indent=2))
    (OUT / "threshold.json").write_text(json.dumps(thr, indent=2))
    print(json.dumps(summ, indent=2))
    print(json.dumps(thr, indent=2))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 3.6))
        bins = np.linspace(-0.2, 1.0, 49)
        for scn, col in [("user_interruption", "#2a7"), ("user_backchannel", "#7a2"),
                         ("talking_other", "#d52"), ("bkg_speech", "#36c")]:
            ax.hist(df[df.scenario == scn].sim, bins=bins, histtype="step", lw=2, label=scn, color=col)
        ax.hist(imp, bins=bins, histtype="step", lw=1, ls="--", color="gray", label="impostor (cross-clip)")
        ax.axvline(thr["eer"]["threshold"], color="k", lw=1, ls=":")
        ax.set_xlabel("ECAPA cosine(enrollment, overlap segment)")
        ax.set_ylabel("# clips")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(OUT / "hist.png", dpi=130)
    except Exception as ex:  # noqa: BLE001
        print("plot failed", ex)


if __name__ == "__main__":
    main()
