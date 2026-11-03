"""One tiny call through the repo's llm.py to confirm the endpoint/model work. Never prints secrets."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cfb_common  # noqa: F401,E402
from langchain_core.messages import HumanMessage  # noqa: E402
from llm import get_chat_model_with_config, response_text  # noqa: E402

try:
    model, cfg = get_chat_model_with_config(max_tokens=20)
    r = model.invoke([HumanMessage(content="Reply with the single word OK.")])
    print("model:", cfg.get("model"), "| reply:", response_text(r)[:40].strip(), "| usage:", getattr(r, "usage_metadata", None))
    print("response model:", (getattr(r, "response_metadata", {}) or {}).get("model_name"))
except Exception as exc:
    msg = re.sub(r"sk-[A-Za-z0-9_\-*]+", "sk-<redacted>", str(exc))
    print("ERROR", type(exc).__name__, getattr(exc, "status_code", None), msg[:400])
