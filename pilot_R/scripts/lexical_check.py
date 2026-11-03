"""Step 2d: lexical-shortcut check. Can a trivial text rule separate side-talk from interruptions in FDB v1.5?
Rule: utterance starts with a vocative = a comma within the first 3 words AND first word is not a discourse marker.
Usage: python -I scripts/lexical_check.py   -> runs/similarity/lexical_check.json
"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RUNS, SCENARIOS, list_ids, load_clip  # noqa: E402
MARKERS = {"actually", "oh", "wait", "hold", "by", "sorry", "so", "well", "hey", "okay", "ok", "um", "uh", "and", "but",
           "also", "anyway", "never", "quick", "one", "before", "speaking", "on", "just", "let's", "can", "could"}
def vocative(t):
    w = t.strip().split()
    head = " ".join(w[:3])
    return ("," in head) and re.sub(r"[^a-z']", "", w[0].lower()) not in MARKERS
res, ex = {}, {}
for scn in SCENARIOS:
    txt = [load_clip(scn, c)["overlap_text"] for c in list_ids(scn)]
    res[scn] = round(sum(map(vocative, txt)) / len(txt), 3)
    ex[scn] = [t for t in txt if vocative(t) != (scn == "talking_other")][:5]
out = {"frac_flagged_as_vocative_side_talk": res, "rule_errors_examples": ex}
(RUNS / "similarity" / "lexical_check.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
sys.stdout.reconfigure(encoding="utf-8"); print(json.dumps(out, indent=2, ensure_ascii=False))
