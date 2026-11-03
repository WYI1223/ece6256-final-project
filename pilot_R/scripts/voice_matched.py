"""Step 2c: voice-matched identity-threshold analysis (removes the voice-pool confound).

talking_other, bkg_speech and user_backchannel all use ONE shared user voice ("voice X"); user_interruption
uses many voices.  So instead of tuning on interruption-vs-bkg, tune on voice X itself:
  A  same voice, clean, different utterance : enrollment_i vs enrollment_j  (i != j, both voice X; talking_other+bkg clips)
  B  different voice (background talker)    : enrollment_i vs bkg overlap_i (as heard in input.wav)
  C  same voice, side-talk as rendered      : enrollment_i vs talking_other overlap_i (input.wav, processed)
  D  same voice, side-talk unprocessed      : enrollment_i vs current_turn.wav_i (raw TTS file)
Thresholds: EER(A,B) and 95%-acceptance-of-A.  Report acceptance of C and D, AUC(A vs C), AUC(D vs C).

Usage: python -I scripts/voice_matched.py   -> runs/similarity/voice_matched.json, emb_cache.npz
"""
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RUNS, SCENARIOS, ensure_16k, list_ids, load_clip, mono  # noqa: E402
from spk_similarity import drop_silence, embed, load_ecapa  # noqa: E402

OUT = RUNS / "similarity"


def auc(pos, neg):
    pos, neg = np.asarray(pos), np.asarray(neg)
    return float(((pos[:, None] > neg[None]) + 0.5 * (pos[:, None] == neg[None])).mean())


def main():
    cache = OUT / "emb_cache.npz"
    if cache.exists():
        z = dict(np.load(cache, allow_pickle=True))
    else:
        model = load_ecapa()
        z = {}
        for scn in ["talking_other", "bkg_speech"]:
            ov_name = SCENARIOS[scn][1]
            E, O, R = [], [], []
            for cid in list_ids(scn):
                c = load_clip(scn, cid)
                x, sr = c["input.wav"]
                x = mono(x)
                t0, t1 = c["meta"]["timestamps"][:2]
                E.append(embed(model, ensure_16k(drop_silence(x[: int(t0 * sr)], sr), sr)))
                O.append(embed(model, ensure_16k(drop_silence(x[int(t0 * sr): int(t1 * sr)], sr), sr)))
                r, srr = c[ov_name]
                R.append(embed(model, ensure_16k(drop_silence(mono(r), srr), srr)))
            z[f"{scn}_enr"], z[f"{scn}_ovl"], z[f"{scn}_raw"] = np.stack(E), np.stack(O), np.stack(R)
            print(scn, "embedded", flush=True)
        np.savez(cache, **z)

    Ex = np.concatenate([z["talking_other_enr"], z["bkg_speech_enr"]])           # voice X enrollments
    S = Ex @ Ex.T
    A = S[np.triu_indices(len(Ex), 1)]
    B = (z["bkg_speech_enr"] * z["bkg_speech_ovl"]).sum(1)
    C = (z["talking_other_enr"] * z["talking_other_ovl"]).sum(1)
    D = (z["talking_other_enr"] * z["talking_other_raw"]).sum(1)
    grid = np.linspace(-0.3, 1.0, 1301)
    acc = lambda s, t: float((s >= t).mean())  # noqa: E731
    t_eer = float(grid[np.argmin([abs((1 - acc(A, t)) - acc(B, t)) for t in grid])])
    t_95 = float(np.quantile(A, 0.05))
    t_90 = float(np.quantile(A, 0.10))
    q = lambda s: {"median": round(float(np.median(s)), 3), "p10": round(float(np.quantile(s, .1)), 3),  # noqa: E731
                   "p90": round(float(np.quantile(s, .9)), 3), "n": int(len(s))}
    res = {
        "distributions": {"A_same_voice_clean_cross_utt": q(A), "B_bkg_voice": q(B),
                          "C_talking_other_processed": q(C), "D_talking_other_raw": q(D)},
        "AUC_A_vs_B(identity separates bkg)": round(auc(A, B), 4),
        "AUC_A_vs_C(identity separates processed side-talk from clean user speech)": round(auc(A, C), 4),
        "AUC_D_vs_C(effect of far-field processing alone)": round(auc(D, C), 4),
        "AUC_C_vs_B(side-talk vs bkg)": round(auc(C, B), 4),
    }
    for name, t in [("eer_A_vs_B", t_eer), ("accept95_of_A", t_95), ("accept90_of_A", t_90)]:
        res[name] = {"threshold": round(t, 3), "A_accepted": round(acc(A, t), 3), "B_bkg_accepted": round(acc(B, t), 3),
                     "C_talking_other_accepted_as_user": round(acc(C, t), 3),
                     "D_raw_side_talk_accepted": round(acc(D, t), 3)}
    (OUT / "voice_matched.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    with torch.no_grad():
        main()
