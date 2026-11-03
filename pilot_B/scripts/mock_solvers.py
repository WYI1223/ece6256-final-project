"""Offline MOCK solver used only to test the closed-loop harness without an API.

It cheats (reads gold from turn.metadata, which closed_loop.py only supplies
with --mock-gold) and then injects controlled noise so that every metric path
(persistence, silent recovery, collateral edits, missed updates) is exercised:

- top-level scalar fields that gold leaves unchanged this turn: copy the prior
  value with p=0.85 (so a wrong prior persists), otherwise use gold (recovery);
- fields gold changes this turn: keep the prior value with p=0.10 (missed update);
- with p=0.25 per turn, overwrite one unchanged single_choice/bool field with a
  wrong value (collateral edit).
Numbers it produces are meaningless; it exists to validate the bookkeeping.
"""

from __future__ import annotations

import hashlib
import json
import random
from copy import deepcopy
from typing import Any


def _rng(turn) -> random.Random:
    seed = (turn.metadata.get("_mock_seed", "") + json.dumps(turn.prior_state, sort_keys=True))
    return random.Random(int(hashlib.sha256(seed.encode()).hexdigest()[:12], 16))


def solve(turn: Any) -> dict[str, Any]:
    md = turn.metadata
    gold = md.get("_mock_gold")
    if gold is None:
        raise RuntimeError("mock solver needs --mock-gold")
    gold_prev = md.get("_mock_gold_prev") or {}
    prior = turn.prior_state or {}
    rng = _rng(turn)
    out = deepcopy(gold)
    choice_fields = []
    for node_id, info in _scalar_fields(turn.schema).items():
        if node_id not in out or isinstance(out.get(node_id), list):
            continue
        unchanged = gold.get(node_id) == gold_prev.get(node_id)
        if unchanged:
            if rng.random() < 0.85:
                out[node_id] = deepcopy(prior.get(node_id))
            if info["type"] in ("single_choice", "bool"):
                choice_fields.append((node_id, info))
        else:
            if rng.random() < 0.10:
                out[node_id] = deepcopy(prior.get(node_id))
    if choice_fields and rng.random() < 0.25:
        fid, info = rng.choice(choice_fields)
        if info["type"] == "bool":
            out[fid] = not bool(out.get(fid))
        else:
            opts = [o for o in info["options"] if o != out.get(fid)]
            if opts:
                out[fid] = rng.choice(opts)
    return {"resulting_state": out, "agent_response": {"model_calls": [], "attempts": 1}}


def _scalar_fields(schema) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}

    def walk(nodes, in_repeat=False):
        for n in nodes or []:
            st = n.get("structure_type", "regular")
            if st == "regular":
                if not in_repeat and n.get("type") != "table":
                    found[n["id"]] = {"type": n.get("type"), "options": n.get("options") or []}
            elif st == "repeat_group":
                walk(n.get("fields"), True)
            elif st in ("group", "gate"):
                walk(n.get("fields"), in_repeat)

    walk(schema.get("questions"))
    return found
