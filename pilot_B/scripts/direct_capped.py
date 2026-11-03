"""The paper's Direct JSON baseline with a capped max_tokens (pilot budget).

Identical to conformbench.systems.direct:solve except llm.MAX_TOKENS is lowered
(default 8192, env CFB_MAX_TOKENS) because llm.py defaults to 32000, which
exceeds DeepSeek's output limit. Also sets direct_invalid_output_policy=prior_state
(the paper's documented fallback) so a 3x-invalid response scores as no-update
instead of crashing the run. Use with:
  python -m conformbench run --items public --solver direct_capped:solve ...   (PYTHONPATH=scripts)
"""
from __future__ import annotations

import os

import llm
import llm_patch  # noqa: F401  (DeepSeek thinking disabled unless DEEPSEEK_THINKING=enabled)

llm.MAX_TOKENS = int(os.environ.get("CFB_MAX_TOKENS", "8192"))

from conformbench.systems import direct as _direct  # noqa: E402


def solve(turn):
    md = dict(getattr(turn, "metadata", {}) or {})
    md.setdefault("direct_invalid_output_policy", "prior_state")
    turn.metadata = md
    return _direct.solve(turn)
