"""Break down wrong leaves in closed-loop traces by condition and field type; list examples."""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cfb_common as C  # noqa: E402

run = Path(sys.argv[1]) if len(sys.argv) > 1 else C.RUNS_DIR / "closed_loop"
mode = sys.argv[2] if len(sys.argv) > 2 else "clean"
idx = {q: C.schema_index(C.load_schema(q)) for q in ["patient_admin", "crash_report"]}
cnt = collections.Counter()
ex = collections.defaultdict(list)
for p in sorted((run / "traces").glob(f"*/*_{mode}.json")):
    tid, cond = p.parent.name, p.name.split("_")[0]
    q = "crash_report" if tid.startswith("cr") else "patient_admin"
    for tr in json.loads(p.read_text(encoding="utf-8")):
        for leaf, w in tr["wrong_leaves"].items():
            ty = C.leaf_type(leaf, idx[q]) or "?"
            if w.get("gold") is None and leaf not in C.flatten_state(tr["gold_state"]):
                ty = "unexpected_field"
            cnt[(cond, ty)] += 1
            ex[(tid, leaf, cond)].append((tr["turn"], w["cand"], w["gold"]))
print(f"wrong leaves by condition x field type ({mode}, T1-T5):")
for c in ["incremental", "rebuild", "oracle"]:
    print(" ", c, dict(sorted({t: n for (cc, t), n in cnt.items() if cc == c}.items())))
print("\nper (trajectory, leaf): turns wrong per condition  [incremental examples: (turn, cand, gold)]")
keys = sorted({(t, l) for (t, l, c) in ex})
for tid, leaf in keys:
    per = {c: [x[0] for x in ex.get((tid, leaf, c), [])] for c in ["incremental", "rebuild", "oracle"]}
    sample = (ex.get((tid, leaf, "incremental")) or ex.get((tid, leaf, "rebuild")) or ex.get((tid, leaf, "oracle")))[0]
    print(f"  {tid:14s} {leaf:40s} inc{per['incremental']} reb{per['rebuild']} ora{per['oracle']}  e.g. {json.dumps(sample, ensure_ascii=False)[:150]}")
