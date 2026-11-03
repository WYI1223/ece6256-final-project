#!/usr/bin/env python3
"""Offline (server-free) Moshi inference over Full-Duplex-Bench v1.5 folders.  PREPARED, NOT RUN.

Why this file instead of the FDB client or `moshi.run_inference`:
  * FDB's own Moshi path (fdb/v1_v1.5/model_inference/moshi/inference.py) is a websocket client that
    streams the wav in REAL TIME to `python -m moshi.server` (Opus-encoded, asyncio.sleep per 80 ms
    frame) -> ~1x real-time per clip, fragile on a batch node, and it has a bug: `root_dir_path` is a
    str but is used with `/` (Path join) in _input_files().
  * kyutai's `python -m moshi.run_inference in.wav out.wav` reloads the 7B model per file and does
    not replicate the server's "skip first frame" convention.
  * PersonaPlex's `python -m moshi.offline` lives in NVIDIA's FORK of the moshi package (different
    LMGen API: voice/text prompts, step_system_prompts) and defaults to the gated
    nvidia/personaplex-7b-v1 repo -> not usable for moshiko and requires accepting gated terms.
  So this runner loads kyutai/moshiko-pytorch-bf16 ONCE via the pip `moshi` package (kyutai) and,
  per file, replicates exactly the frame loop of kyutai `moshi/server.py::recv_loop` (reset
  streaming, encode 1920-sample frames at 24 kHz, drop the first encoded frame by resetting mimi,
  LMGen.step, mimi.decode) and the FDB client's output alignment (1 frame of leading zeros, then
  generated PCM, trimmed/padded to the input length).  Output: mono 24 kHz wav, time-aligned with
  the input -> what FDB evaluation expects.  Faster than real time on an H100/L40S.

Layout written (mirrors what FDB evaluation reads):
  OUT/<task>/<id>/output.wav            (from input.wav, or from a gated wav with --input_override)
  OUT/<task>/<id>/clean_output.wav      (from clean_input.wav, when --prefix clean_)
  OUT/<task>/<id>/{input.json,clean_input.json,metadata.json,input.wav,clean_input.wav}  (copied)
  OUT/<task>/<id>/output_text.json      (Moshi's inner-monologue text tokens, for debugging)

Example:
  python -I scripts/run_moshi_offline.py --data_root DATA/v1_5 --out_root OUT/moshi_raw \
      --tasks talking_to_other background_speech user_backchannel user_interruption --prefix ""
  python -I scripts/run_moshi_offline.py ... --prefix clean_
  # G0 condition: feed identity-gated user channel instead of input.wav
  python -I scripts/run_moshi_offline.py ... --out_root OUT/moshi_g0 \
      --input_override runs/g0/win0.5_ctx0.0/wavs  # expects <override>/<scenario_alias>/<id>.wav
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import time
from pathlib import Path

import numpy as np
import torch

ALIAS = {"talking_to_other": "talking_other", "background_speech": "bkg_speech",
         "user_backchannel": "user_backchannel", "user_interruption": "user_interruption"}


def seed_all(seed: int):
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    random.seed(seed)
    np.random.seed(seed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_root", required=True, help="dir containing talking_to_other/, background_speech/, ...")
    ap.add_argument("--out_root", required=True)
    ap.add_argument("--tasks", nargs="+", default=list(ALIAS))
    ap.add_argument("--prefix", default="", choices=["", "clean_"], help='"" -> input.wav, "clean_" -> clean_input.wav')
    ap.add_argument("--input_override", default=None, help="dir with <scenario_alias>/<id>.wav replacing input.wav")
    ap.add_argument("--hf_repo", default="kyutai/moshiko-pytorch-bf16")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--seed", type=int, default=4242)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="max clips per task (0 = all)")
    args = ap.parse_args()

    import sphn
    from moshi.models import LMGen, loaders

    t_load = time.time()
    ckpt = loaders.CheckpointInfo.from_hf_repo(args.hf_repo)
    mimi = ckpt.get_mimi(device=args.device)
    tok = ckpt.get_text_tokenizer()
    lm = ckpt.get_moshi(device=args.device, dtype=torch.bfloat16)
    lm_gen = LMGen(lm, **ckpt.lm_gen_config)  # moshiko defaults: temp .8 / temp_text .7 / top_k 250 / 25
    sr = mimi.sample_rate                       # 24000
    frame = int(sr / mimi.frame_rate)           # 1920 samples = 80 ms
    mimi.streaming_forever(1)
    lm_gen.streaming_forever(1)
    with torch.no_grad():                       # warmup (as in server.py)
        for _ in range(4):
            codes = mimi.encode(torch.zeros(1, 1, frame, device=args.device))
            for c in range(codes.shape[-1]):
                tk = lm_gen.step(codes[:, :, c:c + 1])
                if tk is not None:
                    mimi.decode(tk[:, 1:])
    torch.cuda.synchronize()
    print(f"[load] {args.hf_repo} in {time.time() - t_load:.1f}s", flush=True)

    out_name = f"{args.prefix}output.wav"
    for task in args.tasks:
        ids = sorted([p.name for p in (Path(args.data_root) / task).iterdir() if p.is_dir()],
                     key=lambda s: int(s) if s.isdigit() else s)
        if args.limit:
            ids = ids[: args.limit]
        for cid in ids:
            src = Path(args.data_root) / task / cid
            dst = Path(args.out_root) / task / cid
            dst.mkdir(parents=True, exist_ok=True)
            for f in ["input.json", "clean_input.json", "metadata.json", "input.wav", "clean_input.wav"]:
                if (src / f).exists() and not (dst / f).exists():
                    shutil.copy2(src / f, dst / f)
            if (dst / out_name).exists() and not args.overwrite:
                continue
            inp = src / f"{args.prefix}input.wav"
            if args.input_override and args.prefix == "":
                inp = Path(args.input_override) / ALIAS[task] / f"{cid}.wav"
            pcm, _ = sphn.read(str(inp), sample_rate=sr)          # (C, T) float32 @ 24 kHz
            pcm = pcm[:1]                                          # mono user channel
            n_target = pcm.shape[-1]
            seed_all(args.seed)
            t0 = time.time()
            outs, texts = [], []
            with torch.no_grad():
                mimi.reset_streaming()
                lm_gen.reset_streaming()
                x = torch.from_numpy(pcm).to(args.device)[None]   # [1, 1, T]
                n_full = x.shape[-1] // frame
                skip = 1
                for i in range(n_full):
                    codes = mimi.encode(x[:, :, i * frame:(i + 1) * frame])
                    if skip:                                       # server.py convention
                        mimi.reset_streaming()
                        skip -= 1
                    for c in range(codes.shape[-1]):
                        tk = lm_gen.step(codes[:, :, c:c + 1])
                        if tk is None:
                            continue
                        outs.append(mimi.decode(tk[:, 1:]).float().cpu().numpy()[0, 0])
                        t_id = int(tk[0, 0, 0].item())
                        texts.append(tok.id_to_piece(t_id).replace("▁", " ") if t_id not in (0, 3) else "")
            y = np.concatenate([np.zeros(frame, np.float32)] + outs) if outs else np.zeros(n_target, np.float32)
            y = y[:n_target] if len(y) >= n_target else np.pad(y, (0, n_target - len(y)))
            sphn.write_wav(str(dst / out_name), y.astype(np.float32), sr)
            (dst / f"{args.prefix}output_text.json").write_text(json.dumps(texts))
            print(f"[{task}/{cid}] {n_target / sr:.1f}s audio in {time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
