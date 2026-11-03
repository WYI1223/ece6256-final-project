#!/usr/bin/env bash
# Round 2 of Pilot B: (re)run everything that the DeepSeek 402 "Insufficient Balance"
# interrupted on 2026-11-02. Idempotent: each out-dir keeps a solver cache of the calls
# that succeeded, failed calls were never cached, so only missing turns are re-billed.
#
#   bash round2_rerun.sh            # everything below
#   bash round2_rerun.sh r1 new v4  # pick stages
#
# Estimated remaining cost (deepseek-flash, before cache discounts): about 1.5 USD for
# stages r1+new, about 0.4 USD for the v4-pro stage, about 2.4 USD for the 15-turn stage
# (K=3 with four regimes plus the K=6 variant). Total about 4.5 USD upper bound.
set -u
cd "$(dirname "$0")"
export PYTHONUTF8=1
export CONFORMBENCH_DATA_DIR=F:/OneDrive/Learn/GeorgiaTech/26Fall/ECE6256/05_final_project/pilot_B/data_zenodo/conformbench-data-v1.0.0
export DEEPSEEK_THINKING=disabled
export PYTHONPATH=F:/OneDrive/Learn/GeorgiaTech/26Fall/ECE6256/05_final_project/pilot_B/scripts
PY=C:/Users/W_YI/miniconda3/envs/cfb/python.exe
R=../runs
STAGES="${*:-r1 new v4 long}"   # stages: r1 new v4 long

run () {  # out-dir, trajectories, solver, conditions
  local out=$1 traj=$2 solver=$3 conds=$4
  "$PY" closed_loop.py --trajectories "$traj" --out-dir "$out" --solver "$solver" \
      --conditions "$conds" --modes clean,corrupt --workers 4 --max-tokens 8192 > "$out.log" 2>&1
  local rc=$?
  "$PY" summarize_closed_loop.py "$out" > /dev/null 2>&1
  printf '%-28s exit %s | %s\n' "$(basename "$out")" "$rc" "$(grep -m1 -oE 'solver errors [0-9]+' "$out/closed_loop_summary.md")"
}
seed () {  # new out-dir, source out-dir: reuse the source's successful calls (same solver + model)
  [ -f "$1/solver_cache.jsonl" ] && return
  mkdir -p "$1"; [ -f "$2/solver_cache.jsonl" ] && cp "$2/solver_cache.jsonl" "$1/solver_cache.jsonl"
}

# sanity: is the endpoint paying again?
"$PY" smoke_llm.py | grep -q "reply: OK" || { echo "API still failing (see smoke_llm.py). Aborting."; exit 2; }

case " $STAGES " in *" r1 "*)
  echo "== stage r1: round-1 (contradicted) injection, other systems =="
  run $R/r2_flatagent $R/trajectories.jsonl async_solvers:flatagent_solve incremental,rebuild,oracle
  run $R/r2_dtv       $R/trajectories.jsonl async_solvers:dtv_solve       incremental,rebuild,oracle
;; esac

case " $STAGES " in *" new "*)
  echo "== stage new: fabricated + ambiguous injection sets x 3 systems =="
  for set in fabricated ambiguous; do
    seed $R/r2_${set}_direct    $R/closed_loop;   run $R/r2_${set}_direct    $R/trajectories_${set}.jsonl conformbench.systems.direct:solve incremental,oracle
    seed $R/r2_${set}_flatagent $R/r2_flatagent;  run $R/r2_${set}_flatagent $R/trajectories_${set}.jsonl async_solvers:flatagent_solve     incremental,oracle
    seed $R/r2_${set}_dtv       $R/r2_dtv;        run $R/r2_${set}_dtv       $R/trajectories_${set}.jsonl async_solvers:dtv_solve           incremental,oracle
  done
;; esac

case " $STAGES " in *" v4 "*)
  echo "== stage v4: second model (deepseek-v4-pro) on the ambiguous set, Direct =="
  OPENAI_MODEL=deepseek-v4-pro run $R/r2_ambiguous_v4pro $R/trajectories_ambiguous.jsonl conformbench.systems.direct:solve incremental,oracle
;; esac

case " $STAGES " in *" long "*)
  echo "== stage long: 15-turn dialogues, history regimes (Direct, deepseek-flash) =="
  # K=3 (inject after turn 3): at T4 the 3-exchange window still covers T1..T3, so full / w3 / w3+summary
  # share the T4 call; they can only differ from T5 on. K=6 injects once the fact is outside the window.
  "$PY" long_closed_loop.py --out-dir $R/long --regimes full,w3,w3+summary,w0 --workers 6 --max-tokens 8192 > $R/long/run_k3.log 2>&1; echo "long k3 exit $?"
  "$PY" long_closed_loop.py --out-dir $R/long --regimes full,w3,w3+summary --inject-after 6 --workers 6 --max-tokens 8192 > $R/long/run_k6.log 2>&1; echo "long k6 exit $?"
  "$PY" long_summarize.py $R/long --tag k3 > /dev/null 2>&1; "$PY" long_summarize.py $R/long --tag k6 > /dev/null 2>&1
  ls $R/long/*summary* 2>/dev/null
;; esac

echo "== analysis =="
"$PY" r2_analyze.py $R/closed_loop $R/r2_direct_v4pro $R/r2_flatagent $R/r2_dtv \
    $R/r2_fabricated_direct $R/r2_fabricated_flatagent $R/r2_fabricated_dtv \
    $R/r2_ambiguous_direct $R/r2_ambiguous_flatagent $R/r2_ambiguous_dtv $R/r2_ambiguous_v4pro \
    > $R/r2_analysis.md 2>&1
echo "wrote $R/r2_analysis.md"
