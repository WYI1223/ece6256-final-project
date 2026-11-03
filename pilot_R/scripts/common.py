"""Shared helpers for Pilot R (FDB v1.5 overlap scenarios)."""
import json
import os
from pathlib import Path

import numpy as np
import soundfile as sf

PILOT = Path("F:/OneDrive/Learn/GeorgiaTech/26Fall/ECE6256/05_final_project/pilot_R")
DATA = PILOT / "data" / "v1_5"
RUNS = PILOT / "runs"

# scenario name used in this pilot -> (folder, overlap-only wav, metadata text key)
SCENARIOS = {
    "talking_other": ("talking_to_other", "current_turn.wav", "current_turn_text"),
    "bkg_speech": ("background_speech", "background.wav", "background_text"),
    "user_backchannel": ("user_backchannel", "backchannel.wav", "backchannel_text"),
    "user_interruption": ("user_interruption", "interrupt.wav", "current_turn_text"),
}


def list_ids(scn):
    folder = DATA / SCENARIOS[scn][0]
    ids = [d for d in os.listdir(folder) if (folder / d).is_dir() and not d.startswith(".")]
    return sorted(ids, key=lambda s: int(s) if s.isdigit() else s)


def load_clip(scn, cid):
    folder, ov_name, key = SCENARIOS[scn]
    d = DATA / folder / cid
    meta = json.loads((d / "metadata.json").read_text(encoding="utf-8"))
    out = {"dir": d, "meta": meta, "overlap_text": meta.get(key, ""),
           "context_text": meta.get("context_text", "")}
    for name in ["input.wav", "clean_input.wav", "context.wav", ov_name]:
        p = d / name
        if p.exists():
            x, sr = sf.read(p, dtype="float32", always_2d=True)
            out[name] = (x, sr)
    return out


def mono(x):
    return x.mean(axis=1) if x.ndim == 2 else x


def rms_db(x, eps=1e-10):
    x = np.asarray(x, dtype=np.float64)
    return 10 * np.log10(np.mean(x ** 2) + eps)


def active_rms_db(x, sr, frame=0.02, rel_db=-35.0):
    """RMS over 'active' frames only (frames within rel_db of the loudest frame)."""
    n = int(frame * sr)
    if len(x) < n:
        return rms_db(x)
    fr = x[: len(x) // n * n].reshape(-1, n)
    e = 10 * np.log10((fr.astype(np.float64) ** 2).mean(axis=1) + 1e-12)
    act = fr[e > e.max() + rel_db]
    return rms_db(act)


def ensure_16k(x, sr):
    if sr == 16000:
        return x
    import torch
    import torchaudio.functional as AF
    y = AF.resample(torch.from_numpy(np.ascontiguousarray(x)).float()[None], sr, 16000)[0].numpy()
    return y
