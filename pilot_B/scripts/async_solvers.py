"""Wrappers for the repo's async agent solvers (flatagent, diff_then_verify).

The repo's `solve()` calls `asyncio.run()` per turn. Under the closed-loop
runner's thread pool that raised "RuntimeError: Event loop is closed" on
roughly every second call (the async OpenAI client outlives the loop that
created it). Here all coroutines run on ONE long-lived event loop in a
daemon thread, so clients are never bound to a closed loop. Nothing else
about the solvers is changed.
"""
from __future__ import annotations

import asyncio
import sys
import threading
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cfb_common  # noqa: F401,E402  (data dir + DeepSeek thinking patch)

from conformbench.systems import diff_then_verify, flatagent  # noqa: E402

_loop = asyncio.new_event_loop()
_thread = threading.Thread(target=_loop.run_forever, name="solver-loop", daemon=True)
_thread.start()


def _run(coro):
    return asyncio.run_coroutine_threadsafe(coro, _loop).result()


def flatagent_solve(turn: Any) -> dict[str, Any]:
    return _run(flatagent._solve_async(turn))


def dtv_solve(turn: Any) -> dict[str, Any]:
    return _run(diff_then_verify._solve_async(turn))
