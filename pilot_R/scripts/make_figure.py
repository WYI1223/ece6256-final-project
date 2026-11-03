"""Main pilot figure: (left) clip-level ECAPA similarity per scenario, (right) G0 mute rates per scenario.
Usage: python -I scripts/make_figure.py  -> runs/pilot_R_main.png
"""
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RUNS  # noqa: E402

INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
S1, S2 = "#2a78d6", "#eb6834"  # categorical slots 1, 2

sims = pd.read_csv(RUNS / "similarity" / "sims.csv")
z = np.load(RUNS / "similarity" / "emb_cache.npz")
Ex = np.concatenate([z["talking_other_enr"], z["bkg_speech_enr"]])
A = (Ex @ Ex.T)[np.triu_indices(len(Ex), 1)]
order = [("user's own speech\n(same voice, other utt.)", A),
         ("user_interruption", sims[sims.scenario == "user_interruption"].sim.values),
         ("talking_other\n(same-voice side-talk)", sims[sims.scenario == "talking_other"].sim.values),
         ("user_backchannel", sims[sims.scenario == "user_backchannel"].sim.values),
         ("bkg_speech\n(different voice)", sims[sims.scenario == "bkg_speech"].sim.values)]
thr = json.loads((RUNS / "similarity" / "voice_matched.json").read_text())["accept95_of_A"]["threshold"]

g05 = json.loads((RUNS / "g0" / "win0.5_ctx0.0" / "summary.json").read_text())
g10 = json.loads((RUNS / "g0" / "win1.0_ctx0.0" / "summary.json").read_text())
scn = ["bkg_speech", "talking_other", "user_interruption", "user_backchannel"]

plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "figure.facecolor": SURF, "axes.facecolor": SURF})
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.0), gridspec_kw={"width_ratios": [1.15, 1]})

pos = np.arange(len(order))
bp = ax1.boxplot([v for _, v in order], positions=pos, orientation="horizontal", widths=0.5, whis=(10, 90), showfliers=False,
                 patch_artist=True, medianprops={"color": INK, "lw": 2},
                 boxprops={"facecolor": "#cde2fb", "edgecolor": S1, "lw": 1.2},
                 whiskerprops={"color": S1, "lw": 1.2}, capprops={"color": S1, "lw": 1.2})
for i, (_, v) in enumerate(order):
    if len(v) < 1000:
        jit = np.random.default_rng(i).uniform(-0.12, 0.12, len(v))
        ax1.scatter(v, i + jit, s=6, color=S1, alpha=0.35, lw=0)
    ax1.text(1.02, i, f"med {np.median(v):.2f}", va="center", color=INK2, fontsize=8, transform=ax1.get_yaxis_transform())
ax1.axvline(thr, color=INK2, ls=":", lw=1)
ax1.text(thr - 0.015, 0.5, f"thr {thr:.2f}: accepts 95% of user's\nown speech, 0% of bkg", fontsize=7.5,
         color=INK2, va="center", ha="right")
ax1.set_yticks(pos, [n for n, _ in order])
ax1.invert_yaxis()
ax1.set_xlabel("ECAPA cosine to the user's enrollment (box = p25-p75, whiskers = p10-p90)")
ax1.set_title("Identity cue: side-talk looks like the user, bkg does not", color=INK, fontsize=10, loc="left")
ax1.grid(axis="x", color=GRID, lw=0.8)
ax1.set_axisbelow(True)
ax1.set_xlim(-0.3, 0.9)

x = np.arange(len(scn))
w = 0.36
v05 = [g05["all"][s]["muted_overlap_frac_mean"] for s in scn]
v10 = [g10["all"][s]["muted_overlap_frac_mean"] for s in scn]
b1 = ax2.bar(x - w / 2 - 0.01, v05, w, color=S1, label=f"0.5 s windows (thr {g05['threshold']:.2f})")
b2 = ax2.bar(x + w / 2 + 0.01, v10, w, color=S2, label=f"1.0 s windows (thr {g10['threshold']:.2f})")
for bars in (b1, b2):
    for r in bars:
        ax2.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.015, f"{r.get_height():.2f}", ha="center",
                 fontsize=8, color=INK)
ax2.set_xticks(x, ["bkg\nspeech\n(should mute)", "talking\nother\n(want mute)", "user\ninterruption\n(must pass)",
                   "user\nbackchannel\n(should pass)"])
ax2.set_ylim(0, 1.05)
ax2.set_ylabel("fraction of overlap speech muted by G0")
ax2.set_title("G0 identity gate per scenario", color=INK, fontsize=10, loc="left")
ax2.grid(axis="y", color=GRID, lw=0.8)
ax2.set_axisbelow(True)
ax2.legend(frameon=False, fontsize=8, loc="upper right")
for a in (ax1, ax2):
    for sp in ("top", "right"):
        a.spines[sp].set_visible(False)
fig.tight_layout()
fig.savefig(RUNS / "pilot_R_main.png", dpi=140)
print("wrote", RUNS / "pilot_R_main.png")
