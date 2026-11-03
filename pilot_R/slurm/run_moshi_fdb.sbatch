#!/bin/bash
# PREPARED, NOT RUN (PACE-ICE refused logins on 2026-11-02).
# Moshi (kyutai/moshiko-pytorch-bf16, NOT gated) offline inference + FDB v1.5 scoring.
# Conditions: raw input, clean input (reference needed by the judge), and G0-gated input.
#
# Submit:   sbatch slurm/run_moshi_fdb.sbatch            (from $PILOT on PACE)
# Edit the three paths below first. moshiko bf16 needs ~17 GB VRAM for weights + KV cache;
# 48 GB (L40S) or 80 GB (H100) is comfortable.
#SBATCH -J moshi_fdb15
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:H100:1          # alternative: --gres=gpu:L40S:1  (check `pace-check-queue` / ICE docs)
#SBATCH --mem=64G
#SBATCH -t 04:00:00
#SBATCH -o logs/%x_%j.out

set -euo pipefail
PILOT=${PILOT:-$HOME/scratch/pilot_R}             # copy of this pilot folder (scripts/, data/v1_5/, fdb/)
ENV=${ENV:-$HOME/scratch/envs/moshi}               # conda env with: pip install "moshi>=0.2.6" (torch<2.10)
export HF_HOME=${HF_HOME:-$HOME/scratch/hf}        # moshiko weights (~15 GB) land here
mkdir -p "$PILOT/logs"
module load anaconda3 2>/dev/null || true
source activate "$ENV" 2>/dev/null || conda activate "$ENV"
cd "$PILOT"
nvidia-smi
DATA=$PILOT/data/v1_5
OUT=$PILOT/runs/moshi
TASKS="talking_to_other background_speech user_backchannel user_interruption"

# 1) inference: overlapped input, clean input, G0-gated input (~500 clips x ~10-20 s each per pass)
python -I scripts/run_moshi_offline.py --data_root "$DATA" --out_root "$OUT/raw" --tasks $TASKS --prefix ""
python -I scripts/run_moshi_offline.py --data_root "$DATA" --out_root "$OUT/raw" --tasks $TASKS --prefix clean_
python -I scripts/run_moshi_offline.py --data_root "$DATA" --out_root "$OUT/g0"  --tasks $TASKS --prefix "" \
       --input_override "$PILOT/runs/g0/win0.5_ctx0.0/wavs"
# the judge also needs the clean reference for the G0 condition: reuse the raw clean outputs
for t in $TASKS; do for d in "$OUT/raw/$t"/*/; do id=$(basename "$d");
  cp -n "$d/clean_output.wav" "$OUT/g0/$t/$id/" 2>/dev/null || true; done; done

# 2) time-aligned ASR (parakeet-tdt-0.6b-v2 via NeMo; needs `pip install nemo_toolkit[asr]`)
#    FDB requires output.json and clean_output.json (input.json / clean_input.json ship with the data)
cd "$PILOT/fdb/v1_v1.5/get_transcript"
for cond in raw g0; do for t in $TASKS; do
  python asr.py --root_dir "$OUT/$cond/$t" --task default --audio_name output.wav
  python asr.py --root_dir "$OUT/$cond/$t" --task default --audio_name clean_output.wav
done; done

# 3) FDB v1.5 scoring.  Behavior (C_RESPOND / C_RESUME / C_UNCERTAIN_HANDLING / C_UNKNOWN) is judged by
#    OpenAI gpt-4o-2024-08-06 -> needs OPENAI_API_KEY in $PILOT/fdb/v1_v1.5/.env (paid API call, ~1k requests).
#    Must run from evaluation/ because eval_behavior.py reads ./instruction/behavior.txt.
cd "$PILOT/fdb/v1_v1.5/evaluation"
for cond in raw g0; do for t in $TASKS; do
  python evaluate.py --task behavior --root_dir "$OUT/$cond/$t"          # -> ${t}_behavior.log in cwd
  mv "${t}_behavior.log" "$OUT/$cond/${t}_behavior.log" || true
  python get_timing.py --root_dir "$OUT/$cond/$t"                         # stop / response latency (silero VAD)
done; done
# optional (UTMOSv2 + pitch/intensity before/after): python evaluate.py --task general_before_after --root_dir ...
echo DONE
