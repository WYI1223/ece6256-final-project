# Round 2, part 4: 15-turn dialogues, history regimes (full / w3 / w3+summary / w0)

**Status (2026-11-02, 22:20 local): BLOCKED, no results yet.** The 8 trajectories are generated and validated.
The runner and the analysis script are written and tested offline. Then the DeepSeek account ran out of
balance at about 22:12: every call returns `HTTP 402 Insufficient Balance`. On the coordinator's instruction I
made no more API calls and did not retry. **There is no regime table, no summary-fidelity number and no trace
example yet.** Everything below is ready to resume once the balance is topped up.

## What is done

| step | state | files |
|---|---|---|
| 15-turn trajectory generator (`make_trajectories.py` design, adapted validators) | done | `scripts/long_make_trajectories.py` |
| 8 trajectories (4 patient_admin, 4 crash_report), 15 turns each | **done, 8/8 accepted** | `runs/long/trajectories_long.jsonl`, `runs/long/trajectories_long_generation_log.json`, `runs/long/generation_stdout.log` |
| runner with history regimes, a shared solver cache, a summary cache, and fail-fast on 402 | done; tested offline with `mock_solvers:solve` on all 8 trajectories (full, w3, w0) and with a simulated-402 solver | `scripts/long_closed_loop.py`, `runs/long/mock_test/` (mock output only, no LLM) |
| analysis (persistence / restoration, summary fidelity, natural persistence, cost) | done; tested on the mock output | `scripts/long_summarize.py` |
| live closed-loop runs (Direct, deepseek-flash) | **blocked by 402.** 1 Direct call succeeded and is cached (pa_long_01 T1: 5,544 in / 455 out). The first summary call failed with 402. | `runs/long/solver_cache.jsonl` (1 entry) |
| regime table, summary fidelity, trace examples | **missing** | written to `runs/long/long_summary_k3.md` etc. on resume |

Nothing that failed was written to a cache. Re-running the same command resumes and never re-bills a completed
call.

## Environment

Same setup as `README_pilot.md`:
- Windows 10 (GBK locale), conda env `cfb` (Python 3.11), repo `conformbench` editable install.
- Required env vars: `PYTHONUTF8=1`, `CONFORMBENCH_DATA_DIR=.../data_zenodo/conformbench-data-v1.0.0`,
  `DEEPSEEK_THINKING=disabled` (thinking is disabled through `scripts/llm_patch.py`, imported by `cfb_common`).
- LLM: `deepseek-flash` via api.deepseek.com, with the key in `conformbench/.env` (never opened or printed).
- Solver: `conformbench.systems.direct:solve` with `max_tokens` 8192. The generator uses `max_tokens` 12000, and
  every generator response ended with `finish_reason=stop`.
- No existing file under `scripts/` or `runs/` was modified. The new files are `scripts/long_*.py` and
  `runs/long/*`.

## Trajectory generation (done)

Command (run 22:07, 52 s):

```bash
cd $P/scripts
$PY long_make_trajectories.py --plan patient_admin:4,crash_report:4 --out ../runs/long/trajectories_long.jsonl --max-attempts 6 --workers 8
```

**Design.** The design is the same as the 5-turn generator; its helpers are imported, not copied or modified.
- The LLM writes 15 turns. Each turn is an assistant question, a user answer and a sparse list of updates.
- Gold records are built deterministically by applying the updates.
- Validators:
  - the repo's `validate_resulting_state`;
  - type, option and date/time checks;
  - gate consistency, and repeat count vs rows.
- Changes for 15 turns:
  - The user keeps adding information across the form sections up to T15.
  - 1 to 3 changes of an earlier value in T4–T15, at least one of them in T6–T15, phrased as an explicit
    correction ("actually ...", "sorry, I meant ..."). A multiple-choice superset counts as an addition, not a
    correction.
  - At most 4 text values may be non-verbatim.
  - At least 2 corruption candidates.
- **Corruption candidates:**
  - single_choice / number / date / time leaves whose final value was set in T1–T3, never touched in T4–T15,
    with gold constant afterwards;
  - the value string is not re-mentioned later;
  - gate controllers and count fields are excluded, as in the 5-turn generator;
  - for number/date/time values, the digits must appear in the user utterance that set them. This guards
    against invented values like the pilot's "just after midnight" -> 00:20.
- Candidates are sorted by the turn that set them (earliest first), so the fact leaves a 3-exchange window as
  early as possible.
- **Gold was NOT human-reviewed** (validators only).

**Yield:** 8/8 accepted, with 23 LLM calls in total.

| trajectory | attempts | updates | non-empty leaves at T15 | corrections (turn: field) | candidates (set turn) |
|---|---|---|---|---|---|
| pa_long_01 | 2 | 54 | 51 | T14 sputum_color | pain_details[0].pain_severity (t1), sputum_amount (t3) |
| pa_long_02 | 2 | 32 | 31 | T7 pain_details[0].pain_duration | pain_details[0].pain_severity (t1), pain_details[1].pain_severity (t3) |
| pa_long_03 | 2 | 40 | 39 | T10 weight_loss_amount | pain_details[0/1].pain_severity (t2) |
| pa_long_04 | 6 | 40 | 38 | T8 most_recent_fall_date_or_time | pain_details[0/1].pain_severity (t2) |
| cr_long_01 | 1 | 29 | 28 | T6 lighting | date_of_accident (t1), time_of_accident (t2) |
| cr_long_02 | 6 | 21 | 19 | T7 location_of_accident, T14 posted_speed_limit | date_of_accident (t1), time_of_accident (t2) |
| cr_long_03 | 2 | 25 | 24 | T10 vehicles[0].approx_speed_mph | date_of_accident (t1), time_of_accident (t2) |
| cr_long_04 | 2 | 23 | 22 | T12 vehicles[0].licence_plate | date_of_accident (t1), time_of_accident (t2) |

**Rejections:** 15 attempts were rejected. Reasons per attempt (an attempt can have more than one):
- 8 had no explicit correction in T6–T15;
- 8 had fewer than 2 silent candidates (the facts from T1–T3 were re-mentioned or touched later);
- 1 had 16 turns instead of 15.

There were no JSON or API errors. Generation tokens were 43,769 in and 35,867 out, about **$0.056**.

**Observations on the generated data (no review done):**
- The crash_report dialogues walk through the form in schema order (T1 date, T2 time, T3 location ...), so the
  only crash candidates are date (T1) and time (T2). The weather, lighting and surface facts all came after T3
  or were touched again later.
- All patient_admin candidates are pain severities.
- Some severity labels are interpretive. For example, in pa_long_02 "hurting pretty badly" was labelled High.
  The headline metrics below do not depend on gold being right; see Metrics.

## Runner (done, not yet run live)

`scripts/long_closed_loop.py` is a copy of `closed_loop.py` with these additions:

- **`--regimes`**, run in one process with **one shared solver cache** (`runs/long/solver_cache.jsonl`). The
  key is a hash of the solver input, history included, so only byte-identical calls are shared. The visible
  history at turn t is (u_t is always the current utterance):
  - `full`: a1,u1 ... a_t.
  - `w3`: the last 3 exchanges plus a_t (= `--history-window 3`).
  - `w3+summary`: one assistant-role message, "Summary of the earlier conversation: ...", followed by w3. The
    summary is a single deepseek-flash call (thinking disabled through the same llm / llm_patch) over turns
    1..t-4, the turns that fell out of the window.
    - The prompt asks for a faithful bullet list of all facts the user stated, in the user's own terms, with no
      inference, and only the corrected version of any corrected fact.
    - Summaries are cached per (trajectory, last covered turn) in `runs/long/summaries.jsonl`, so clean and
      corrupt runs, and every injection point, share them.
    - Every summary is also dumped to `runs/long/summaries_readable.json`.
  - `w0`: a_t only.
- **Run settings:** condition `incremental` only, modes clean and corrupt.
- **Injection:** after K = 3, the trajectory's default. `--inject-after N` overrides it.
- **Which candidate is injected:** the first one the system holds correctly at K (vs generator gold). The
  system's own turn-K value is stored as `pre_injection_value`.
- **New CSV columns:** `regime`, `inject_after`, `pre_injection_value`, `restored_pre_injection`,
  `history_messages`, `summary_upto`, `summary_chars`, and summary token columns. Traces include the visible
  history and the summary text.
- **Fail-fast:** on HTTP 402/401, or on any solver transport error (default `--abort-on-error`), the run stops
  without writing a CSV, so a no-update fallback is never scored as a model output. Completed calls stay
  cached.

### Metrics (in `long_summarize.py`)

- **Headline, gold-independent:**
  - survived at T4: the T4 output still holds the injected value;
  - persistence length (0–12): consecutive turns from T4 that hold the injected value;
  - restored by T15, and the turn of restoration: the output equals the system's **own pre-injection value**;
  - other outcomes: dropped to null, or a third value.
- Because the gold was not human-reviewed, **accuracy vs gold is not a headline**. Clean structured and
  all-field accuracy are reported only as a secondary column, labelled "vs UNREVIEWED generator gold".
- **Natural-error persistence:** as in closed_loop.py (`nat_*` columns). This one is gold-based, so it carries
  the same caveat.
- **Summary fidelity (w3+summary):**
  - For each summary that covers the turn that set the corrupted fact, check whether a bullet line contains a
    surface form of the TRUE (gold) value:
    - dates: ISO, "March 14", "14 March", "14th of March", "March 14th", "3/14";
    - times: "18:45", "6:45";
    - choices: the option word plus a short paraphrase list, e.g. High: severe / pretty bad / badly.
  - For repeat-row fields, the same line must also contain the row anchor (the last word of the row's
    `pain_part`, e.g. "knee"). Otherwise "moderate amount of phlegm" would count as the knee's "moderate".
  - Every automatic label is saved with its matched line in `summary_fidelity_<tag>.json`, so it can be checked
    by hand. This check is still to be done after the run.
- **Cost:** per run from `run_meta_<tag>.json`, which bills only non-cache-hit calls, plus a cache-wide total
  over `solver_cache.jsonl` and `summaries.jsonl`, valid across resumed invocations. Prices are $0.30 per M
  input and $1.20 per M output. DeepSeek prompt-cache discounts are ignored, so this is an upper bound.

### Design caveat to keep in mind (K = 3 with window 3)

At T4 a 3-exchange window still covers T1–T3, i.e. the whole dialogue, and w3+summary has nothing to summarize
yet. **So the T4 input under w3 and w3+summary is byte-identical to full history.** With the shared cache it is
literally the same call, so **"survived at T4" is identical for full, w3 and w3+summary by construction**. The
three regimes can only diverge from T5 on, and only for injections that survived T4.

Expect the following:
- The 5-turn pilot repaired 10/10 at the next turn with full history.
- If that repeats, the K = 3 design cannot separate window from summary.
- When the fact leaves the window:
  - crash candidates (the date, set at T1) are out of a 3-exchange window from T5;
  - pain severities set at T2 are out from T6.

A **late-injection variant, `--inject-after 6`**, puts the fact outside the window at the moment of injection.
Then w3 sees T4–T6 and the summary covers T1–T3. That is the clean test of "summary vs window only". It reuses
every clean call and every summary from the cache, so it only adds the corrupt turns T7–T15. I recommend
running it right after the K = 3 run (see the resume commands below).

## Resume commands (run these once the balance is topped up)

```bash
export PYTHONUTF8=1
export CONFORMBENCH_DATA_DIR=F:/OneDrive/Learn/GeorgiaTech/26Fall/ECE6256/05_final_project/pilot_B/data_zenodo/conformbench-data-v1.0.0
export DEEPSEEK_THINKING=disabled
PY=C:/Users/W_YI/miniconda3/envs/cfb/python.exe
cd F:/OneDrive/Learn/GeorgiaTech/26Fall/ECE6256/05_final_project/pilot_B/scripts

# 1) main run, K = 3 (spec). Append ,w0 to --regimes if the budget allows (adds ~$0.45); re-running later with
#    the extra regime is fine: the other regimes are cache hits and the k3 CSV is rewritten with all regimes.
$PY long_closed_loop.py --out-dir ../runs/long --regimes full,w3,w3+summary --workers 6 --max-tokens 8192 \
    > ../runs/long/run_k3_stdout.log 2>&1
# 2) recommended: late injection K = 6 (clean turns and summaries are cache hits; only corrupt T7-T15 is billed)
$PY long_closed_loop.py --out-dir ../runs/long --regimes full,w3,w3+summary --inject-after 6 --workers 6 --max-tokens 8192 \
    > ../runs/long/run_k6_stdout.log 2>&1
# 3) analysis (no API): writes runs/long/long_summary_<tag>.md and summary_fidelity_<tag>.json
$PY long_summarize.py ../runs/long --tag k3
$PY long_summarize.py ../runs/long --tag k6
```

If a run aborts again (402), it prints `ABORTED during ...` and writes no CSV. Rerun the identical command
after topping up; completed calls are served from `solver_cache.jsonl` and `summaries.jsonl`.

If step 1 is first run with fewer regimes and later with more, the per-run billed numbers in `run_meta_k3.json`
cover only the newer calls. The cache-wide total printed by `long_summarize.py` stays correct.

Still to do by hand after the runs (about 20 minutes):
- check the summary-fidelity labels in `summary_fidelity_k3.json`;
- pick 2–3 trace examples (persisted / restored via the summary / restored via the window) from
  `runs/long/k3_<regime>/traces/<trajectory>/incremental_corrupt.json`, which hold the visible history and the
  summary per turn;
- fill in this README's results section.

## Estimated remaining cost

- **Basis:** one measured Direct call (T1: 5.5k in / 0.46k out), and the pilot's average of about 5k in /
  0.42k out per call over 5 turns.
- **Assumed per-call input for 15 turns:** full about 6.5k, w3 about 5.8k, w3+summary about 6.2k, w0 about 5.6k.
  Output is assumed at about 0.5k per call.

| run | billed calls | est. input | est. output | est. USD |
|---|---|---|---|---|
| K=3 full (clean T1–T15 + corrupt T4–T15) | 215 | 1.40 M | 0.11 M | 0.55 |
| K=3 w3 (T1–T4 shared with full) | 176 | 1.02 M | 0.09 M | 0.41 |
| K=3 w3+summary (+88 summary calls, ~0.06 M in / 0.02 M out) | 176 + 88 | 1.15 M | 0.11 M | 0.48 |
| K=3 w0 (optional) | 208 | 1.16 M | 0.10 M | 0.47 |
| K=6 variant, full + w3 + w3+summary (corrupt T7–T15 only) | 216 | 1.34 M | 0.11 M | 0.53 |
| **total, everything** | ~1,080 | ~6.1 M | ~0.52 M | **about $2.4** |
| K=3 without w0, plus the K=6 variant | ~870 | ~4.9 M | ~0.42 M | **about $2.0** |
| K=3 without w0 only | ~650 | ~3.6 M | ~0.31 M | **about $1.45** |

Spent so far:
- trajectory generation: $0.056;
- one Direct call: $0.002;
- the failed calls were not billed (402).

Wall time is about 10–15 minutes per run at 6 workers. The 5-turn batches took about 1 minute, and 15-turn
dialogues are sequential within a trajectory.

## Caveats (apply once results exist)

- No human review of gold. Report persistence and restoration of the injected value only. Accuracy vs gold is
  secondary.
- n = 8 trajectories, 2 questionnaires, 1 model (deepseek-flash, thinking disabled, provider-default
  temperature), 1 system (Direct).
- The candidate types are narrow: crash = date or time stated at T1/T2; patient = pain severity. These are
  facts with an exact surface form in the dialogue, so summaries can easily copy them. Fidelity on
  interpretive fields would likely be lower.
- With K = 3, T4 is identical across full, w3 and w3+summary (see the design caveat above).
- One sample per input, no repeats. The 5-turn pilot showed small sampling noise (1 of 10 T1 records differed
  by one leaf).
