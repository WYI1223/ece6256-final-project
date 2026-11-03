"""Step 5 (optional): zero-shot voice-cloned same-voice side-talk with Chatterbox on the RTX 3070.

Reference voice = FDB "voice X" (the single user voice shared by talking_to_other / background_speech /
user_backchannel), built by concatenating context.wav of talking_to_other clips 1..5 (~10 s).
Writes runs/tts_demo/{ref_voiceX.wav, side_talk_{1,2,3}.wav, timing.json}.

Usage (TTS env):  F:/AI/conda_envs/fdb_tts/python.exe -I scripts/tts_demo.py
"""
import json
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

PILOT = Path("F:/OneDrive/Learn/GeorgiaTech/26Fall/ECE6256/05_final_project/pilot_R")
OUT = PILOT / "runs" / "tts_demo"
OUT.mkdir(parents=True, exist_ok=True)
SRC = PILOT / "data" / "v1_5" / "talking_to_other"

TEXTS = [
    "Hey Tom, can you grab the door?",
    "Sorry Maria, give me one second, I'm on a call.",
    "Tom, did you remember to feed the dog this morning?",
]


def main():
    parts = []
    for cid in ["1", "2", "3", "4", "5"]:
        x, sr = sf.read(SRC / cid / "context.wav", dtype="float32")
        parts += [x, np.zeros(int(0.3 * sr), np.float32)]
    ref = np.concatenate(parts)
    sf.write(OUT / "ref_voiceX.wav", ref, sr)

    from chatterbox.tts import ChatterboxTTS
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    t = time.time()
    model = ChatterboxTTS.from_pretrained(device=dev)
    t_load = time.time() - t
    timing = {"device": dev, "gpu": torch.cuda.get_device_name(0) if dev == "cuda" else None,
              "ref_sec": round(len(ref) / sr, 2), "load_sec": round(t_load, 1), "utts": []}
    model.generate("Warm up.", audio_prompt_path=str(OUT / "ref_voiceX.wav"))  # warm-up (not timed)
    for i, text in enumerate(TEXTS, 1):
        if dev == "cuda":
            torch.cuda.synchronize()
        t = time.time()
        wav = model.generate(text, audio_prompt_path=str(OUT / "ref_voiceX.wav"))
        if dev == "cuda":
            torch.cuda.synchronize()
        dt = time.time() - t
        y = wav.squeeze().cpu().numpy()
        sf.write(OUT / f"side_talk_{i}.wav", y, model.sr)
        timing["utts"].append({"text": text, "gen_sec": round(dt, 2), "audio_sec": round(len(y) / model.sr, 2),
                               "rtf": round(dt / (len(y) / model.sr), 2)})
        print(timing["utts"][-1], flush=True)
    if dev == "cuda":
        timing["peak_vram_gb"] = round(torch.cuda.max_memory_allocated() / 1e9, 2)
    (OUT / "timing.json").write_text(json.dumps(timing, indent=2))
    print(json.dumps(timing, indent=2))


if __name__ == "__main__":
    main()
