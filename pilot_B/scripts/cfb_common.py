"""Shared helpers for the Pilot-B closed-loop ConFormBench scripts.

Everything here reuses the ConFormBench repo (runner shape check, public
deterministic evaluator) so the pilot follows the paper's own semantics.
Import this module BEFORE importing anything from `conformbench` so the data
directory and UTF-8 mode are set correctly.
"""

from __future__ import annotations

import json
import os
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

PILOT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PILOT_ROOT / "conformbench"
DATA_DIR = PILOT_ROOT / "data_zenodo" / "conformbench-data-v1.0.0"
RUNS_DIR = PILOT_ROOT / "runs"

os.environ.setdefault("CONFORMBENCH_DATA_DIR", str(DATA_DIR))
os.environ.setdefault("PYTHONUTF8", "1")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# The evaluator reads questionnaire JSON with Path.read_text() and no encoding;
# on a GBK-locale Windows box that fails unless Python runs in UTF-8 mode.
if not sys.flags.utf8_mode:
    raise SystemExit(
        "Run with PYTHONUTF8=1 (or `python -X utf8`): the ConFormBench evaluator "
        "reads schemas with the locale encoding."
    )

from conformbench.benchmark import (  # noqa: E402
    _build_turn_result,
    _questionnaire_path,
    validate_resulting_state,
)
from conformbench.evaluator.pipeline import evaluate_solver_turn  # noqa: E402
from conformbench.items import normalize_item  # noqa: E402
from conformbench.questionnaires import load_questionnaire  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import llm_patch  # noqa: E402,F401  (DeepSeek thinking-mode control)

STRUCTURED_TYPES = {"bool", "number", "integer", "single_choice", "multiple_choice", "date", "time"}
TEXT_TYPES = {"text", "multiline_text", "string"}
_REPEAT_PATH_RE = re.compile(r"^(?P<group>\w+)\[(?P<idx>\d+)\]\.(?P<field>\w+)$")


# --------------------------------------------------------------------------
# Schema helpers
# --------------------------------------------------------------------------

def schema_index(schema: dict[str, Any]) -> dict[str, Any]:
    """Walk a questionnaire schema and index fields, repeat groups, gates."""

    fields: dict[str, dict[str, Any]] = {}  # field_id -> {type, options, group, gate}
    repeat_groups: dict[str, dict[str, Any]] = {}  # group_id -> {fields, count_field}
    gates: dict[str, dict[str, Any]] = {}  # gate_id -> {gate_on, when_values, children}
    top_level: list[str] = []

    def walk(nodes, repeat_stack=(), gate_stack=()):
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            st = node.get("structure_type", "regular")
            if st == "regular":
                fid = node.get("id")
                if not fid:
                    continue
                group = repeat_stack[-1] if repeat_stack else None
                fields[fid] = {
                    "type": node.get("type"),
                    "options": node.get("options") or [],
                    "group": group,
                    "gates": list(gate_stack),
                    "question": node.get("question_text") or "",
                    "columns": [c.get("id") for c in node.get("columns") or [] if isinstance(c, dict)],
                }
                if group:
                    repeat_groups[group]["fields"].append(fid)
                else:
                    top_level.append(fid)
                for g in gate_stack:
                    gates[g]["children"].append(fid)
            elif st == "repeat_group":
                gid = node.get("id")
                repeat = node.get("repeat") or {}
                repeat_groups[gid] = {
                    "fields": [],
                    "count_field": repeat.get("from_slot") if repeat.get("mode") == "from_slot" else None,
                    "gates": list(gate_stack),
                }
                top_level.append(gid)
                for g in gate_stack:
                    gates[g]["children"].append(gid)
                walk(node.get("fields"), (*repeat_stack, gid), gate_stack)
            elif st == "gate":
                gate = node.get("gate") or {}
                gid = node.get("id")
                gates[gid] = {
                    "gate_on": gate.get("gate_on"),
                    "when_values": gate.get("when_values") or [],
                    "children": [],
                }
                walk(node.get("fields"), repeat_stack, (*gate_stack, gid))
            elif st == "group":
                walk(node.get("fields"), repeat_stack, gate_stack)
            elif st == "branch":
                branch = node.get("branch") or {}
                for route in branch.get("routes") or []:
                    walk(route.get("children"), repeat_stack, gate_stack)
                walk(branch.get("default_children"), repeat_stack, gate_stack)

    walk(schema.get("questions"))
    gate_controllers = {g["gate_on"] for g in gates.values() if g.get("gate_on")}
    count_fields = {rg["count_field"] for rg in repeat_groups.values() if rg.get("count_field")}
    return {
        "fields": fields,
        "repeat_groups": repeat_groups,
        "gates": gates,
        "top_level": top_level,
        "gate_controllers": gate_controllers,
        "count_fields": count_fields,
    }


def empty_record(schema: dict[str, Any]) -> dict[str, Any]:
    """Initial record: every scalar null, every repeat group an empty list.

    Mirrors the benchmark's S1 (empty) prior states, e.g. FM-CR-01.
    """

    idx = schema_index(schema)
    state: dict[str, Any] = {}
    for key in idx["top_level"]:
        state[key] = [] if key in idx["repeat_groups"] else None
    return state


def leaf_field_id(leaf: str) -> str:
    m = _REPEAT_PATH_RE.match(leaf)
    if m:
        return m.group("field")
    return leaf.split(".")[0].split("[")[0]


def leaf_type(leaf: str, idx: dict[str, Any]) -> str | None:
    info = idx["fields"].get(leaf_field_id(leaf))
    return info.get("type") if info else None


def is_structured_leaf(leaf: str, idx: dict[str, Any]) -> bool:
    return leaf_type(leaf, idx) in STRUCTURED_TYPES


# --------------------------------------------------------------------------
# State helpers (same flattening convention as the repo's public evaluator)
# --------------------------------------------------------------------------

def flatten_state(state: Any, prefix: str = "") -> dict[str, Any]:
    if not prefix:
        if not isinstance(state, dict):
            return {}
        out: dict[str, Any] = {}
        for key in sorted(state):
            out.update(flatten_state(state[key], str(key)))
        return out
    if isinstance(state, dict):
        out = {}
        for key in sorted(state):
            out.update(flatten_state(state[key], f"{prefix}.{key}"))
        return out
    if isinstance(state, list) and all(isinstance(item, dict) for item in state):
        out = {}
        for i, row in enumerate(state):
            out.update(flatten_state(row, f"{prefix}[{i}]"))
        return out
    return {prefix: state}


def get_path(state: dict[str, Any], path: str) -> Any:
    m = _REPEAT_PATH_RE.match(path)
    if m:
        rows = state.get(m.group("group"))
        i = int(m.group("idx"))
        if not isinstance(rows, list) or i >= len(rows) or not isinstance(rows[i], dict):
            return None
        return rows[i].get(m.group("field"))
    return state.get(path)


def set_path(state: dict[str, Any], path: str, value: Any, idx: dict[str, Any]) -> None:
    """Set a top-level field or group[i].field; appends one empty row when i == len."""

    m = _REPEAT_PATH_RE.match(path)
    if m:
        group, i, field = m.group("group"), int(m.group("idx")), m.group("field")
        if group not in idx["repeat_groups"]:
            raise KeyError(f"unknown repeat group {group!r}")
        if field not in idx["repeat_groups"][group]["fields"]:
            raise KeyError(f"unknown field {field!r} in group {group!r}")
        rows = state.get(group)
        if not isinstance(rows, list):
            rows = []
            state[group] = rows
        if i > len(rows):
            raise IndexError(f"{path}: row index {i} skips rows (have {len(rows)})")
        if i == len(rows):
            rows.append({f: None for f in sorted(idx["repeat_groups"][group]["fields"])})
        rows[i][field] = deepcopy(value)
        return
    if path not in idx["top_level"] or path in idx["repeat_groups"]:
        raise KeyError(f"unknown top-level scalar field {path!r}")
    state[path] = deepcopy(value)


# --------------------------------------------------------------------------
# Scoring with the repo's own public deterministic evaluator
# --------------------------------------------------------------------------

def score_state(
    *,
    item_id: str,
    questionnaire_id: str,
    prior_state: dict[str, Any],
    visible_history: list[dict[str, Any]],
    current_utterance: str,
    gold_state: dict[str, Any],
    candidate_state: dict[str, Any],
) -> dict[str, Any]:
    """Score candidate vs gold with conformbench.evaluator.pipeline.evaluate_solver_turn.

    The packet has no per-field policies, so the repo routes it to
    `evaluate_public_turn_result`: deterministic field-level scoring (exact
    after normalization; set-match for multiple choice; open-text mismatches
    count as incorrect; non-empty candidate fields absent from gold count as
    incorrect "unexpected_field" verdicts). No LLM calls.
    """

    packet = {
        "item_id": item_id,
        "questionnaire_id": questionnaire_id,
        "prior_state": prior_state,
        "visible_history": visible_history,
        "current_utterance": current_utterance,
        "gold_resulting_state": gold_state,
    }
    item = normalize_item(packet)
    turn_result = _build_turn_result(item, {"candidate_state": candidate_state, "operations": []})
    evaluation = evaluate_solver_turn(
        turn_result,
        packet,
        questionnaire_path=_questionnaire_path(questionnaire_id),
    )
    verdicts = {qid: v.correctness for qid, v in evaluation.field_results.items()}
    return {"summary": dict(evaluation.summary), "verdicts": verdicts}


def load_schema(questionnaire_id: str) -> dict[str, Any]:
    return load_questionnaire(questionnaire_id)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def env_key_present() -> bool:
    """True if repo .env (or process env) has a non-empty OPENAI_API_KEY. Never prints it."""

    if os.environ.get("OPENAI_API_KEY"):
        return True
    env = REPO_ROOT / ".env"
    if not env.exists():
        return False
    for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("OPENAI_API_KEY") and "=" in line:
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            if value and not value.startswith("#"):
                return True
    return False
