"""Runtime patch for the repo's llm.py (no edit to the repo file itself).

deepseek-flash runs in THINKING mode by default. The repo's llm._build_model
drops reasoning controls for non-Groq endpoints, so here we wrap it: when the
OpenAI-compatible base URL is api.deepseek.com, add
    extra_body = {"thinking": {"type": $DEEPSEEK_THINKING}}   (default "disabled")
to the ChatOpenAI kwargs. Set DEEPSEEK_THINKING=enabled to get thinking mode.
Importing this module is idempotent.
"""
from __future__ import annotations

import os

import llm

if not getattr(llm, "_pilot_b_patched", False):
    _orig_build_model = llm._build_model

    def _build_model(backend, **kw):
        if backend == "openai":
            base = llm._first_env(llm._OPENAI_BASE_URL_ENV) or ""
            if "deepseek.com" in base.lower():
                extra = dict(kw.get("extra_body") or {})
                extra["thinking"] = {"type": thinking_mode()}
                kw["extra_body"] = extra
        return _orig_build_model(backend, **kw)

    llm._build_model = _build_model
    llm._pilot_b_patched = True


def thinking_mode() -> str:
    return os.getenv("DEEPSEEK_THINKING", "disabled")


def reasoning_tokens_from_snapshot(snap: dict) -> int:
    """Pull reasoning tokens out of a conformbench message_accounting_snapshot dict."""
    um = snap.get("usage_metadata") or {}
    r = (um.get("output_token_details") or {}).get("reasoning")
    if isinstance(r, int):
        return r
    tu = (snap.get("response_metadata") or {}).get("token_usage") or {}
    r = (tu.get("completion_tokens_details") or {}).get("reasoning_tokens")
    return r if isinstance(r, int) else 0
