# Pilot B: closed-loop ConFormBench (ECE 6256 topic decision)

Run on 2026-11-02, 18:15 to about 18:55 local time (about 40 minutes of wall time end to end; each LLM batch
took 1 minute or less). **This is a 10-trajectory pilot on synthetic dialogues, not a benchmark result.** Every
number below has wide uncertainty and comes from LLM-generated gold that only got a light review.

## TL;DR

- **The harness works.** The repo installs. The no_update and Direct baselines run and score end to end.
  `scripts/closed_loop.py` runs incremental, rebuild and oracle, each in clean and corrupted mode, and scores
  every turn with the repo's own evaluator. API cost for the whole pilot was about $0.70.
- **Whether error persistence shows up depends on one design knob: how much dialogue history the system sees.**
  - With **full history** (the paper's setting), Direct silently repaired an injected wrong value at the next
    turn in **9/10** trajectories. Mean persistence was 0.1 turns.
  - With a **state-only** design (history window 0: only the current assistant question and user turn), the
    injected value **survived all 3 remaining turns in 9/10** trajectories. Mean persistence was 2.7 turns and
    nothing was ever restored.
  - The model's own natural structured errors persisted 95% (incremental) and 100% (state-only) of the time.
    But rebuild re-derived the same errors 87.5% of the time, so they are systematic interpretation errors, not
    errors carried through the state.
- **Condition gaps** (full history, clean, mean over T2 to T5, 10 trajectories, paired bootstrap 95% CIs):
  - Incremental vs oracle: all-field accuracy -3.9 pp [-6.4, -1.6], structured-field accuracy -2.4 pp,
    fully-correct records -15 pp.
  - Incremental vs rebuild: +0.4 pp [-0.2, +0.9], i.e. no difference.
  - About 87% of incremental's structured errors trace back to gold ambiguity or under-annotation, or to an
    "Unknown" vs null convention. So the oracle's advantage here is mostly that it defers to the gold
    interpretation in its prior, not that it avoids propagated errors.
- **Building trajectories is the real cost.** 5 of the 9 LLM-generated trajectories needed a manual fix before
  use: 3 had invented values, 1 had a pseudo-correction, 1 had a premature count plus a year the dialogue never
  gives. Error analysis afterwards surfaced more gold under-annotations that my review missed.

## Environment

| item | value |
|---|---|
| OS | Windows 10 Home (zh-CN, GBK locale) |
| Python | Miniconda env `cfb`, Python 3.11.18 (`C:/Users/W_YI/miniconda3/envs/cfb/python.exe`); system Python untouched |
| repo | `conformbench` @ `23cbfd0` (MIT), `pip install -e .`; langchain-openai 1.7.3, openai 3.42.1 |
| data | Zenodo `conformbench-data-v1.0.0` (CC BY 4.0), `CONFORMBENCH_DATA_DIR=.../pilot_B/data_zenodo/conformbench-data-v1.0.0` |
| LLM | `deepseek-flash` via `https://api.deepseek.com` (OpenAI-compatible, repo `llm.py`, key in `conformbench/.env`, never printed or copied) |
| thinking | **disabled** for every run except `runs/direct_public_think` (see below) |
| max_tokens | 8192 for Direct (the repo default of 32000 is lowered at runtime); 6000 for the trajectory generator |
| temperature | not set (Direct does not set one), so the provider default applies |

Two local workarounds, both applied from `scripts/` with no edits to the repo:

1. **`PYTHONUTF8=1` is required.** The evaluator calls `Path.read_text()` with no encoding, and that crashes
   under the GBK locale (`UnicodeDecodeError` in `hard.py`).
2. **`scripts/llm_patch.py`** wraps `llm._build_model`. For `api.deepseek.com` it adds
   `extra_body={"thinking": {"type": $DEEPSEEK_THINKING}}`, which defaults to `disabled`. Without it,
   deepseek-flash runs in thinking mode, because the repo's llm.py drops reasoning controls for non-Groq
   endpoints.

## Exact commands

```bash
export PYTHONUTF8=1
export CONFORMBENCH_DATA_DIR=F:/OneDrive/Learn/GeorgiaTech/26Fall/ECE6256/05_final_project/pilot_B/data_zenodo/conformbench-data-v1.0.0
PY=C:/Users/W_YI/miniconda3/envs/cfb/python.exe
P=F:/OneDrive/Learn/GeorgiaTech/26Fall/ECE6256/05_final_project/pilot_B
"C:/Users/W_YI/miniconda3/Scripts/conda.exe" create -n cfb python=3.11 -y
cd $P/conformbench && $PY -m pip install -e .
$PY -m conformbench list-questionnaires && $PY -m conformbench list-public-items
# step 2: evaluator sanity check, no LLM
$PY -m conformbench run --items public --solver conformbench.systems.no_update:solve --output-dir $P/runs/no_update_public --score
$PY scripts/compute_run_metrics.py --run-dir $P/runs/no_update_public --items-dir $CONFORMBENCH_DATA_DIR/items/public --no-figures
# step 5a: Direct on the 8 public items (wrapper = repo direct + max_tokens cap + DeepSeek thinking control)
PYTHONPATH=$P/scripts DEEPSEEK_THINKING=disabled CFB_MAX_TOKENS=8192 $PY -m conformbench run --items public --solver direct_capped:solve --output-dir $P/runs/direct_public_nothink --score --workers 4
PYTHONPATH=$P/scripts DEEPSEEK_THINKING=enabled  CFB_MAX_TOKENS=16000 $PY -m conformbench run --items public --solver direct_capped:solve --output-dir $P/runs/direct_public_think --score --workers 4
cd $P/scripts && $PY summarize_public_run.py ../runs/direct_public_nothink
# step 4: trajectories
$PY check_chaining.py                                   # are public/benchmark items chainable? (no)
$PY make_trajectories.py --handmade --out ../runs/trajectories_handmade.jsonl
DEEPSEEK_THINKING=disabled $PY make_trajectories.py --plan patient_admin:5,crash_report:4 --out ../runs/trajectories_llm.jsonl --max-attempts 4
DEEPSEEK_THINKING=disabled $PY make_trajectories.py --plan crash_report:4 --out ../runs/trajectories_llm_cr.jsonl --max-attempts 5   # after a validator fix, see below
#   (merge: 5 PA from trajectories_llm + 4 CR from trajectories_llm_cr + handmade -> runs/trajectories.jsonl)
$PY fix_trajectories.py ../runs/trajectories.jsonl      # apply + log the human-review fixes, re-validate
# offline harness test (mock solver that reads gold and injects controlled noise)
$PY closed_loop.py --trajectories ../runs/trajectories_handmade.jsonl --out-dir ../runs/mock_test --solver mock_solvers:solve --mock-gold
# step 5b: closed loop, full history (main) and state-only ablation
DEEPSEEK_THINKING=disabled $PY closed_loop.py --trajectories ../runs/trajectories.jsonl --out-dir ../runs/closed_loop --solver conformbench.systems.direct:solve --workers 8 --max-tokens 8192
DEEPSEEK_THINKING=disabled $PY closed_loop.py --trajectories ../runs/trajectories.jsonl --out-dir ../runs/closed_loop_w0 --solver conformbench.systems.direct:solve --conditions incremental,oracle --history-window 0 --workers 8
$PY summarize_closed_loop.py ../runs/closed_loop ; $PY summarize_closed_loop.py ../runs/closed_loop_w0
$PY error_breakdown.py ../runs/closed_loop clean
```

## Step 1: dataset and evaluator facts

- **4 questionnaires:** crash_report, grant, patent_form, patient_admin.
- **8 public items, 2 per questionnaire** (`*_dev_01/02`). The release README calls them "API smoke tests, not
  benchmark results". Their user turns are explicit instructions, e.g. "set `pain_experience` to `true`" or
  "set `allergies[0].allergen` to ...".
- **180 benchmark items**, 45 per questionnaire, split 36 dev / 144 held-out test. These have natural utterances
  and per-field scoring policies. None were run with an LLM here.
- **Item packet (`ground_truth.json`):**
  - `prior_state`: the full record, with every schema field; repeat groups are lists of row objects.
  - `visible_history`: a list of `{role, content}`.
  - `current_utterance`: a string.
  - `gold_resulting_state`: the full post-turn record. Gold is stored as this complete record, not as a diff.
  - Public items add `expected_operations`.
  - Benchmark items add `fields` / `repeat_groups` (per-leaf strategy and evidence), `semantic_ius`,
    `gold_state_diff`, `forbidden_commits`, `difficulty_profile`, and so on.
- **Scoring routes** (`evaluator/pipeline.py::evaluate_solver_turn`):
  - Packets that have `fields` or `repeat_groups` go to the full evaluator. It does repeat-row alignment, uses
    an LLM comparator for open text and semantic IUs, and applies a preserve-miss rule.
  - Packets without per-field policies (the public items, and my synthetic turns) go to the **deterministic
    public route**. Every gold leaf is compared exactly after normalization (lowercased, whitespace collapsed,
    set-match for multiple choice).
  - On that route, an open-text mismatch counts as incorrect, and a non-empty candidate leaf that does not exist
    in gold counts as an incorrect "unexpected_field".
- **Metrics** (`evaluator/metric_views.py`):
  - **All-field accuracy** = correct leaf verdicts / evaluated leaves, summed across items (micro).
  - **Fully-correct record** = `whole_record_exact_match`, meaning every primary leaf is `correct`.
  - **Collateral edit** = a leaf whose gold value is unchanged from the prior but whose candidate value changed.

## Step 2: no_update baseline (no LLM)

| run | items | all-field acc | fully-correct | preservation | changed-field recall |
|---|---|---|---|---|---|
| no_update, public | 8 | 26.3% (99/377) | 0/8 | 167/167 kept | 0.5% (1/210) |

The CLI printed `Exact commitments: 0/8`. The metrics come from the repo's `scripts/compute_run_metrics.py`.

## Step 5a: Direct on the 8 public items

| run | all-field acc | fully-correct | input tok | output tok | reasoning tok | wall |
|---|---|---|---|---|---|---|
| Direct, thinking disabled | 100% (307/307) | 8/8 | 82,334 | 6,669 | 0 | 16 s |
| Direct, thinking enabled | 100% (307/307) | 8/8 | 82,534 | 29,976 | 22,891 | 69 s |

The public items are instruction-style smoke tests, so 100% says nothing about difficulty. Thinking mode
multiplied output tokens by 4.5 and latency by 4.3 for no accuracy change here. The realistic single-turn
baseline would be the 36-item dev split, which needs the rich evaluator with an LLM judge; that was not run (out
of brief).

## Step 4: trajectory construction

**Chaining existing items is not possible.** `check_chaining.py` found 0 pairs, among both the 8 public and the
180 benchmark items, where gold(A) equals prior(B) or where A's utterance appears in B's history. The items are
independent snapshots, so I generated trajectories with the LLM instead.

**Generator design** (`make_trajectories.py`):
- The LLM writes 5 turns, each an assistant question, a user answer and a **sparse list of updates**.
- The gold records are **built deterministically** by applying those updates to the empty record.
- Validation:
  - the repo's `validate_resulting_state`;
  - type, option and date/time checks;
  - gate consistency, and repeat count vs rows (following the repo's `_materialize_repeat_counts` convention);
  - coherence rules: an explicit correction somewhere in T3 to T5, and at least one structured fact from T1–T2
    that is never mentioned again (used as the corruption slot).
- Notes, multiline and table fields were excluded from gold by design.

| generation | requested | LLM calls | accepted | main rejection reasons |
|---|---|---|---|---|
| test run (not used) | 1 PA | 2 | 1 | no correction |
| run 1 | 5 PA + 4 CR | 19 | 5 PA + 1 CR | CR: count != rows (my validator was stricter than the repo convention), no correction, 1 unparseable JSON |
| run 2 (CR, fixed validator) | 4 CR | 6 | 4 CR | no correction (cr_gen_04 needed 3 tries) |
| final set | **9 LLM + 1 handmade** = 10 trajectories x 5 turns | | | 16 to 30 updates per trajectory |

**Human review.** I read all 9 by eye, which took about 15 to 20 minutes. **5 of 9 needed an edit.** The fixes
are applied and logged in `fix_trajectories.py` and in each trajectory's `human_review` block:
- pa_gen_01: invented `hemoptysis_any="No"`; blood was never mentioned.
- pa_gen_03: invented T1 `pain_severity="Moderate"`, which made the T4 correction "High, not Moderate"
  incoherent.
- pa_gen_05: the T3 "correction" was a no-op ("about three weeks" became "three weeks").
- cr_gen_02: invented `time_of_accident="00:20"` from "just after midnight".
- cr_gen_03: vehicle count set one turn before the second car is mentioned, and "this year" used as if it gave
  a year.

Another 5 ambiguous labels were flagged but not changed, e.g. "fairly bad" mapped to High, or "vegetarian"
mapped to Prefers.

**After the runs**, model-vs-gold disagreements exposed more gold under-annotation that the review had missed:
- cr_gen_04 T2: "at the stop sign" licenses `traffic_control="Stop Sign"`, but gold sets it only at T4.
- cr_gen_01 T2: `location_type` should already be "Intersection".
- cr_gen_02 T3: the fence damage is already stated, so `non_vehicle_property_damage` should be set.
- Gold-design artifacts: the solver legitimately fills notes fields and `injury_table`, which gold keeps empty.

**What this costs at scale:** roughly 2 minutes per trajectory for a quick read, and probably 10 or more minutes
for a contract-level check. Expect about half of the trajectories to need edits. A useful triage trick is to run
the solver once and inspect the leaves where all three conditions disagree with gold.

## Step 5b: closed-loop results (Direct, deepseek-flash, thinking disabled)

Setting: 10 trajectories (6 patient_admin, 4 crash_report), 5 turns each. History = `[a1,u1,...,a_t]`,
utterance = `u_t`. Scored with the repo's public deterministic evaluator.

**Metrics:**
- all_field_acc: strict; free-text paraphrases count as wrong.
- structured_acc: only bool, number, choice, date and time leaves.
- fully_correct: every leaf of the record is correct.

### Accuracy vs turn, full history, clean (macro mean over trajectories, %)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| all-field: incremental | 99.2 | 93.7 | 91.1 | 91.4 | 89.8 | 91.5 |
| all-field: rebuild | 99.2 | 94.0 | 91.2 | 90.0 | 89.2 | 91.1 |
| all-field: oracle | 99.2 | 94.1 | 95.7 | 95.7 | 95.9 | 95.4 |
| structured: incremental | 99.5 | 97.1 | 93.8 | 95.8 | 96.9 | 95.9 |
| structured: rebuild | 99.5 | 96.1 | 93.8 | 94.5 | 95.4 | 94.9 |
| structured: oracle | 99.5 | 97.5 | 97.3 | 98.8 | 99.6 | 98.3 |
| fully-correct: incremental | 80 | 20 | 20 | 20 | 10 | 17.5 |
| fully-correct: rebuild | 80 | 20 | 20 | 20 | 10 | 17.5 |
| fully-correct: oracle | 80 | 30 | 30 | 40 | 30 | 32.5 |

Micro all-field accuracy over T1 to T5 was incremental 93.7%, rebuild 93.2%, oracle 96.6%. By questionnaire:
crash_report scored 86.6 / 86.8 / 92.6 and patient_admin scored 97.4 / 96.7 / 98.5 (incremental / rebuild /
oracle).

### Gaps (clean, per-trajectory mean over T2 to T5, paired bootstrap 95% CI, n = 10)

| comparison | all-field (pp) | structured (pp) | fully-correct (pp) |
|---|---|---|---|
| incremental - oracle | -3.9 [-6.4, -1.6] | -2.4 [-4.0, -0.9] | -15.0 [-35, 0] |
| rebuild - oracle | -4.3 [-6.7, -2.1] | -3.4 [-5.4, -1.5] | -15.0 [-37.5, +2.5] |
| incremental - rebuild | +0.4 [-0.2, +0.9] | +0.9 [+0.1, +1.9] | 0.0 [-7.5, +7.5] |

In the state-only ablation (history window 0), incremental - oracle was -4.9 pp all-field [-8.1, -2.3],
-2.6 pp structured, and -37.5 pp fully-correct [-60, -17.5]. Clean incremental accuracy hardly changes when
history is removed: 91.4 vs 91.5 over T2 to T5.

### Injected corruption

After T2, one structured field that the system had right was overwritten with a wrong value. The user never
mentions that field again.

| history | condition | survived T3 | mean persistence (0-3 turns) | silently recovered by T5 | never recovered |
|---|---|---|---|---|---|
| full | incremental | 1/10 | 0.10 | 10/10 | 0/10 |
| full | oracle (+ carried field) | 1/10 | 0.10 | 10/10 | 0/10 |
| **state-only (w0)** | incremental | **9/10** | **2.70** | 0/10 | 10/10 |
| **state-only (w0)** | oracle (+ carried field) | **9/10** | **2.70** | 0/10 | 10/10 |

Rebuild is immune by construction, since no state is carried. Corrupted fields:
- crash_report: lighting x3 or road_surface_condition, and date_of_accident.
- patient_admin: pain_severity x2, allergy_severity, and ambulatory_aid_use x2.
- handmade: medication route.

Effect of the corruption on all-field accuracy over T3 to T5: 0.0 pp with full history; -2.6 pp (incremental)
and -2.0 pp (oracle) state-only.

### Collateral edits and natural persistence (clean, T2 to T5)

| run | condition | collateral edits / opportunities | of which non-empty gold value damaged | natural structured errors: carried / persisted / recovered |
|---|---|---|---|---|
| full | incremental | 13/1204 (1.1%) | 0 | 20 / 19 / 1 (95%) |
| full | rebuild | 22/1198 (1.8%) | 4 | 24 / 21 / 2 (87.5%, re-derived) |
| full | oracle | 28/1277 (2.2%) | 5 | 10 / 0 / 10 |
| w0 | incremental | 8/1200 (0.7%) | 0 | 22 / 22 / 0 (100%) |
| w0 | oracle | 19/1277 (1.5%) | 6 | 14 / 0 / 14 |

**Composition of errors.** Incremental, full history, clean, T1 to T5: 115 wrong leaf-turns in total. Of these,
57 were text, 23 multiline notes, 31 structured and 4 unexpected (injury_table). Of the 31 structured errors, by
my reading:
- about 21 come from gold ambiguity or under-annotation (traffic_control, location_type, pre_crash_manoeuvre,
  early contributing_factors);
- 6 are the evaluator scoring "Unknown" as wrong against a gold null;
- only about 4 are clear model errors (pa_gen_03: "moderate" copied from the shoulder pain onto the headaches).

### Example failures (from `runs/*/traces/<trajectory>/<condition>_<mode>.json`)

1. **Persisted error.**
   - *State-only, pa_gen_02, incremental:* an injected `allergies[0].allergy_severity="Severe"` (gold
     "Moderate", stated in T2) was kept unchanged at T3, T4 and T5 while the user talked about cough, falls and
     diet.
   - *Full history, cr_gen_03:* an injected `lighting="Dusk / Dawn"` (the user said "sunny and clear" in T2)
     survived T3 and was repaired only at T4.
   - *Natural error, pa_gen_03:* from T1 the model gave the headache row `pain_severity="Moderate"` (only the
     shoulder was called moderate). Incremental carried it through T4; rebuild re-derived it at all 5 turns.
2. **Silent recovery.**
   - *pa_gen_01, full history:* the prior handed in at T3 had `pain_severity="High"` (injected). The T3 utterance
     was "No, I haven't fallen. I do use a cane..." and the model returned "Moderate", the value from T1, without
     being told.
   - *Half repair, pa_handmade_01, state-only:* the injected "aspirin 81 mg, route Inhaled" was judged
     implausible and set to `route=null` instead of being restored to "Oral". With no history, the model can only
     drop an error, not fix it.
3. **Collateral edit.**
   - *w0, pa_gen_02, oracle, T2:* handed the gold prior (lower back pain, High, about a week) and an utterance
     about allergies, the model **wiped the whole pain record** (`pain_experience`, `number_of_pains` and the row
     all set to null). Direct's audit policy says "preserve a prior value only when it remains licensed by the
     visible history", and with no history the pain facts look unlicensed.
   - *Full history, pa_gen_04, rebuild, T2:* `pain_severity` flipped from High (its own T1 output) to Moderate
     with no new evidence.
   - Most other collateral edits are free-text rewrites, e.g. "driver of the first car" became "first car".

### Cost and tokens

| run | billed calls | input tok | output tok | reasoning tok |
|---|---|---|---|---|
| Direct public, no thinking | 8 | 82,334 | 6,669 | 0 |
| Direct public, thinking | 8 | 82,534 | 29,976 | 22,891 |
| trajectory generation (3 runs) | 27 | 42,248 | 24,870 | 0 |
| closed loop, full history (3 conditions x clean/corrupt) | 143 | 713,476 | 60,205 | 0 |
| closed loop, state-only ablation (2 conditions x clean/corrupt) | 130 | 637,125 | 52,896 | 0 |
| **total** | **about 316** | **about 1.56 M** | **about 0.17 M** | 22,891 |

At the coordinator's assumed rates ($0.30 per M input, $1.20 per M output) this is about **$0.68**, before any
DeepSeek cache-hit discount. A Direct call costs about 5k input and 0.4k output tokens. Calls with identical
inputs are cached, so T1 is shared across conditions, corrupt runs reuse T1–T2, and oracle turns whose input
equals incremental's input reuse that call. Billed counts per condition therefore depend on which job ran
first; the totals are exact. Retries for invalid JSON: 0. Prior-state fallbacks: 0.

Noise estimate: T1 inputs are identical across the two closed-loop runs but were sampled independently. 9/10
trajectories got the same score; one differed by one leaf.

## Signals for the decision

1. **Harness works?** Yes.
   - Install, both baselines, scoring with the repo evaluator, the 3-condition closed loop, corruption
     injection, caching, traces and summaries all run on this machine. Each closed-loop batch takes about a
     minute and about $0.25.
   - Known limitation: synthetic turns can only use the deterministic public route. Free-text fields are scored
     by exact match. Using the repo's LLM-judge route would need per-field policies in the trajectory gold.
2. **Does error persistence appear at a non-trivial rate?** Only when the system cannot audit against history.
   - Full history (the paper's setting plus Direct's audit prompt): injected errors persisted 1/10 and were
     repaired almost immediately. That is a near-null result for "state-carried error persistence".
   - State-only: 9/10 persisted for the whole remaining trajectory, with 0 recoveries.
   - Natural model errors persist about 90 to 100% of the time in every non-oracle condition, but rebuild
     re-derives them just as often. They come from systematic interpretation, not from the state channel.
   - If the topic goes ahead, **history window (or history truncation/summary) should be a main independent
     variable**, not just Incremental vs Rebuild vs Oracle.
3. **Size of the gaps:**
   - Incremental vs rebuild: about 0 (+0.4 pp all-field, CI includes 0).
   - Both vs oracle: about -4 pp all-field, -2.4 to -3.4 pp structured, about -15 pp fully-correct (-37.5 pp
     state-only).
   - Caveat: on this pilot the oracle's advantage mostly reflects deference to gold's interpretation of
     ambiguous or under-annotated leaves. The gap is real as measured, but its size is not yet trustworthy.
4. **How laborious is trajectory construction?** It is the main risk.
   - LLM generation is fast and cheap: 27 calls for 9 accepted trajectories, about 1 minute, about $0.04.
   - But 5/9 needed hand fixes (3 with invented values), and gold under-annotation slipped past a careful read.
   - A credible project needs a written annotation contract for multi-turn gold, plus double review or
     adjudication of every trajectory. Budget roughly 10 minutes per trajectory, so about 15 to 20 person-hours
     for 100 trajectories.
   - Alternatives: hand-author the dialogues, as in the handmade trajectory (about 10 minutes), or reuse the
     benchmark's annotation contract (`docs/ANNOTATION_CONTRACT_v0.9.2.md`).
5. **Blockers and caveats:**
   - (a) The GBK-locale encoding crash; worked around with `PYTHONUTF8=1`.
   - (b) deepseek-flash thinking mode is on by default and llm.py drops the control; worked around with
     `llm_patch.py`.
   - (c) llm.py defaults max_tokens to 32000; capped at runtime.
   - (d) The public scoring route marks free-text paraphrases and "Unknown" vs null as wrong, which inflates
     error counts. Report structured accuracy, or add per-field policies so the full evaluator and its LLM judge
     can be used.
   - (e) The default judge model in llm.py is `claude-sonnet-4`, which this DeepSeek endpoint cannot serve. Any
     run of the rich evaluator (the 36-item dev split) must pass `--evaluator-model`, which departs from the
     paper's judge.
   - (f) n = 10 trajectories, 2 questionnaires, 1 model, 1 system (Direct), default temperature. The CIs are
     wide and nothing here is validated on the real benchmark.

## Files

- `scripts/`:
  - `closed_loop.py` (runner), `make_trajectories.py` (generator and validator), `fix_trajectories.py` (logged
    human fixes), `cfb_common.py` (repo-evaluator scoring and schema helpers);
  - `llm_patch.py`, `direct_capped.py`, `mock_solvers.py` (offline harness test);
  - `summarize_closed_loop.py`, `summarize_public_run.py`, `error_breakdown.py`, `check_chaining.py`,
    `smoke_llm.py`.
- `runs/`:
  - `trajectories.jsonl` (final 10; `trajectories.orig.jsonl` is the pre-fix copy) and the generation logs
    `trajectories_llm*_generation_log.json`;
  - `closed_loop/closed_loop_results.csv` (main per-turn CSV), `closed_loop/closed_loop_summary.md`,
    `closed_loop/traces/`, `closed_loop/run_meta.json`;
  - `closed_loop_w0/` (state-only ablation, same layout);
  - `no_update_public/`, `direct_public_nothink/`, `direct_public_think/`, `chaining_report.json`, and
    `mock_test/` (offline harness check).
- A copy of the main CSV is at `runs/closed_loop_results.csv`.

## Round 2 (2026-11-02 evening; interrupted by an API balance of zero at 22:10, completed 23:50 after a top-up)

Purpose: test the four weaknesses of the round-1 conclusion ("closed-loop error persistence is near zero
with full history"): only one system, only one model, only one injection type (a value flatly contradicted
by the history), only 5-turn dialogues.

**How it ran.** At about 22:10 the DeepSeek account returned HTTP 402 "Insufficient Balance" on every call;
the runs that were in flight (flatagent corrupt, diff_then_verify) were scored as "no update" by the runner,
which fakes persistence, so they were discarded. After the top-up, `scripts/round2_rerun.sh` re-ran every
piece from the per-run caches (failed calls were never cached). **All 11 run directories below finished with
0 solver errors.** The combined tables are in `runs/r2_analysis.md` (5-turn sets) and
`runs/long/long_summary_k{3,6}.md` (15-turn sets).

| piece | where |
|---|---|
| Direct + deepseek-v4-pro, contradicted injection, 3 conditions | `runs/r2_direct_v4pro/` |
| flatagent (tool-based sparse updates) and diff_then_verify (sparse update + one verification call), contradicted injection, 3 conditions | `runs/r2_flatagent/`, `runs/r2_dtv/` |
| LLM-proposed "defensible alternative" values for the round-1 candidates | `runs/plausible_proposals.{jsonl,md}` |
| ambiguous-evidence injection set (10 trajectories, one hand-rewritten utterance each) x Direct flash, flatagent, diff_then_verify, Direct v4-pro | `runs/trajectories_ambiguous.jsonl`, `runs/r2_ambiguous_*/` |
| fabricated-value injection set (7 trajectories, never-mentioned ungated field) x Direct flash, flatagent, diff_then_verify | `runs/trajectories_fabricated.jsonl`, `runs/r2_fabricated_*/` |
| 15-turn trajectories (8/8 accepted, 23 LLM calls, validators only, no human review; candidates are narrow: crash date/time, patient pain severity) x full / window-3 / window-3+summary / state-only, injection after turn 3 and after turn 6 | `runs/long/README_long.md`, `runs/long/long_summary_k3.md`, `runs/long/long_summary_k6.md` |

Design note for the 15-turn stage (from the subagent's hand-back): with injection after turn 3 and a
3-exchange window, the turn-4 input under window-3 and window-3+summary is identical to full history, so the
three regimes can only diverge from turn 5 on. The rerun script therefore also runs a late-injection variant
(`--inject-after 6`), where the corrupted fact is already outside the window when it is injected; it reuses
all clean calls and summaries, so only the corrupt turns 7 to 15 are billed.

Fix needed for the agent solvers: the repo's `flatagent.solve` and `diff_then_verify.solve` call
`asyncio.run()` per turn, which under the runner's thread pool raised "RuntimeError: Event loop is closed" on
about half the calls. `scripts/async_solvers.py` runs the same coroutines on one long-lived event loop; the
solvers themselves are unchanged.

### Valid results so far

**1. Second model, same injection (Direct, deepseek-v4-pro, full history).** Same picture as deepseek-flash:
the contradicted value survived the first post-injection turn in 2/10 (flash: 1/10), was silently repaired in
9/10, and was never repaired in 1/10 (oracle condition). Incremental vs rebuild is again a wash (+0.3 pp
all-field, CI [-1.5, +2.0]). So the round-1 number is not a weak-model artifact.

**2. Sparse-update agent, clean (flatagent, deepseek-flash; failed rows excluded).** Incremental accuracy matches
Direct (92.3 vs 91.5 all-field, T2 to T5). But rebuild is now clearly *worse* than incremental (-4.2 pp
all-field, CI [+1.3, +7.4] for incremental - rebuild; -32.5 pp fully-correct vs oracle): an agent that emits
only sparse updates loses facts when it has to reconstruct the record from scratch every turn, so for this
system the state channel is doing real work. (With Direct, which rewrites the whole record anyway, carrying
state changed nothing.) The injection numbers for flatagent are not available yet.

**3. The metric the topic actually needs: errors that survive only through the carried state.** `scripts/r2_analyze.py`
splits incremental's natural structured errors at T2 to T5 into (a) inherited from its own previous output
with the same wrong value, and (b) whether rebuild also gets that leaf wrong at the same turn. Errors that
are inherited *and* that rebuild gets right are the ones that exist only because state is carried:

| system / model | incremental wrong leaf-turns | inherited | rebuild also wrong | **state-only** | distinct leaves |
|---|---|---|---|---|---|
| Direct, flash | 30 | 19 (63%) | 28 (93%) | **1** (3%) | 1 |
| flatagent, flash | 31 | 19 (61%) | 24 (77%) | **3** (10%) | 2 |
| Direct, v4-pro | 25 | 16 (64%) | 13 (52%) | **7** (28%) | 3 |

The state-only cases are all of one kind: a value the model *invented or defaulted* and then kept (v4-pro:
`time_of_accident = 00:07` from "just after midnight", carried T3 to T5; `hemoptysis_any = No` when blood was
never mentioned, carried T3 to T4; flatagent: the same `hemoptysis_any`), plus one omission (`lighting` left
null). Nothing in the history contradicts such a value, so the audit-against-history prompt never fires.
This is the mechanism Proposal B needs, and it is not zero under full history; it is just rare on 5-turn
dialogues (1 to 3 leaves per 10 trajectories) and strongest for the stronger model, which re-derives fewer
of its own errors (rebuild also wrong: 52% vs 93%). Counts this small are indicative only.

**4. Why the round-1 injection was easy.** Asked for the single most defensible alternative reading of the
user's words, deepseek-flash returned "none" (plausibility 1) for 25 of the 27 round-1 corruption candidates;
reading the evidence confirms it: the generated users speak in schema words ("I'd call it moderate",
"a mild ache", "pitch dark with no streetlights"). So round 1 tested only the contradicted-by-history case.
The two new sets target the other two cases: `trajectories_ambiguous.jsonl` rewrites one utterance per
trajectory so two readings are defensible (e.g. "I keep the walker by the bed" for `ambulatory_aid_use`,
injected "Has but does not use" against gold "Yes (uses)"); `trajectories_fabricated.jsonl` injects a
plausible value into a field the user never mentions (e.g. `traffic_control = Stop Sign`), which matches the
state-only errors found in item 3.

**5. 15-turn dialogues: persistence is a function of evidence visibility (Direct, deepseek-flash, 8 trajectories, 0 solver errors).**
Details, per-trajectory sequences and the fidelity labels: `runs/long/long_summary_k3.md`, `runs/long/long_summary_k6.md`.
Injected value = the round-1 type (contradicted by what the user said in turn 1 or 2: accident date +3 days,
pain severity one step off). "Restored" means the system's own pre-injection value is back; gold is not used
because the long gold had no human review.

| injected after | history regime | survived first post-injection turn | restored by T15 (turn) | persisted to T15 |
|---|---|---|---|---|
| turn 3 | full history | 0/8 | 7/8 (all at T4) | 0/8 |
| turn 3 | last 3 exchanges | 0/8 | 7/8 (all at T4) | 0/8 |
| turn 3 | last 3 exchanges + LLM summary of older turns | 0/8 | 7/8 (all at T4) | 0/8 |
| turn 3 | state only | 7/7 | 0/7 | 7/7 (one trajectory excluded: without history the system had already lost the date by turn 3, so there was nothing correct to corrupt) |
| **turn 6** | full history | 1/8 | 7/8 (all at T7) | 0/8 |
| **turn 6** | last 3 exchanges (fact already outside the window) | **8/8** | **0/8** | **8/8** |
| **turn 6** | last 3 exchanges + summary | 1/8 | 7/8 (all at T7) | 0/8 |

With injection after turn 3 the three evidence-bearing regimes are identical by construction (the window
still covers turns 1 to 3 at T4; same cached call), which is why the late-injection variant was added. With
injection after turn 6 the picture is unambiguous: the sliding window alone carries the wrong value for all
nine remaining turns in 8/8 trajectories, and a one-line LLM summary of the older turns is enough to bring
the repair rate back to full-history level, because 85/86 summaries (auto label; the one auto miss is a
labeler artifact, the line "The pain is moderate" lacked the anchor word "knee") state the true value. The
one trajectory that is never restored in any evidence-bearing regime (pa_long_02) ends at "Unknown", not at
the injected value. Natural structured errors persist 100% (25/25 carried) in all three evidence-bearing
regimes and 99% under state only, same as the 5-turn pilot.

Reading for the topic: the variable that decides whether a carried error survives is *whether the licensing
evidence is visible to the model*, directly or through a summary, not whether state is carried. A "history
window" treatment therefore reproduces the 2022 DST setting, and a summary treatment removes the effect
again. Cost of the 15-turn stage: 1.35 USD for 752 billed calls plus 0.06 USD generation.

**6. Other systems, contradicted injection (5 turns, full history, incremental).** Every system repairs a value
that the history contradicts: Direct flash 10/10 silently recovered (0 persisted to T5), Direct v4-pro 9/10,
flatagent 9/10 (1 never), diff_then_verify 10/10. The round-1 number is not a Direct artifact either.

**7. Fabricated injection (7 trajectories; a plausible value written into a field the user never mentions,
e.g. `traffic_control = Stop Sign`, `appetite_change = Yes`; gold null; incremental, full history).**

| system | still holds the fabricated value at T3 | cleared by T5 | holds it to T5 |
|---|---|---|---|
| Direct (whole-record rewrite), flash | 3/7 | 6/7 | **1/7** |
| flatagent (sparse tool updates) | 7/7 | 2/7 | **5/7** |
| diff_then_verify (sparse updates + verification call) | 5/7 | 2/7 | **4/7** |

The audit-against-history prompt clears an unlicensed value when the model rewrites the whole record, but
a sparse-update agent only touches fields the current turn mentions, so an invented value rides along to the
end in 5 of 7 cases, and the repo's own verification stage catches it in only 1 more case than no
verification at all. This is the mechanism behind the state-only natural errors in item 3.

**8. Ambiguous-evidence injection (10 trajectories; one utterance rewritten so two readings are defensible;
the injected value is the other reading; incremental, full history).** Only the trajectories where the system
had read the field as gold at T2 are true injections (the others already held the alternative on their own and
are reported separately):

| system | true injections | injected reading kept to T5 | repaired | system's own reading was already the alternative (kept it) |
|---|---|---|---|---|
| Direct, flash | 5 | **1/5** | 4/5 (all at T3) | 4 of 5 remaining kept, 1 went null |
| Direct, **v4-pro** | 7 | **5/7** | 2/7 (T4, T5) | 3/3 kept |
| flatagent, flash | 7 | **5/7** | 2/7 | 2 of 3 kept, 1 went null |
| diff_then_verify, flash | 4 | **2/4** | 2/4 | 6/6 kept |

Under genuinely ambiguous wording ("I keep the walker by the bed", "the sun had just about gone and the
streetlights were starting to come on", "bit of dew but nothing to speak of") the stronger model defers to
whatever the prior says in 5 of 7 cases; flash re-reads the evidence more often and flips back. Neither
behaviour is "wrong" against the evidence, which is the point: the carried state decides the committed value
whenever the evidence does not, so an early wrong reading is permanent in exactly the cases a human reviewer
would also have to adjudicate.

**9. Synthesis (incremental, full history unless stated; "persisted" = injected value still held at the last turn).**

| error type | Direct flash | Direct v4-pro | flatagent | diff_then_verify | 15-turn, window-3 (Direct flash) | 15-turn, window-3 + summary |
|---|---|---|---|---|---|---|
| contradicted by visible history | 0/10 | 0/10 | 1/10 | 0/10 | **8/8** | 0/8 |
| fabricated, nothing in history either way | 1/7 | - | 5/7 | 4/7 | - | - |
| ambiguous, two readings defensible | 1/5 | 5/7 | 5/7 | 2/4 | - | - |

So the round-1 statement "closed-loop error persistence is near zero with full history" was true only for
the easiest cell of this table. The phenomenon Proposal B wants to study exists under full history for two
realistic error types (invented values and ambiguous readings), is strongest for sparse-update agents and for
the stronger model, and the repo's verification stage does not remove it. What B's story cannot be is "errors
propagate through carried state because the model does not re-check": it does re-check, and repairs whatever
the visible evidence contradicts. A defensible reframing: *provenance*. Values that no utterance licenses
(fabricated) and values whose licensing utterance is ambiguous are the ones that persist, so a state that
carries, per field, the evidence span and an ambiguity flag, and re-verifies only unlicensed or flagged fields,
targets exactly the cells that stay red above. That is still a descendant of Correctable-DST's
"detect suspicious slots, regenerate", but the detector would be evidence-based rather than
confidence-based, and the benchmark substrate (ConFormBench's evidence-licensing contract) supports it.

Caveats that still apply: n = 7 to 10 trajectories per cell, synthetic dialogues, one trajectory family, two
DeepSeek models, no human-reviewed gold for the 15-turn set, and the ambiguous rewrites were written by the
same person who chose the injected alternative.

### Cost of round 2

5-turn runs (all `runs/r2_*`): 9.88 M input and 0.31 M output tokens, about 3.34 USD; the two aborted runs
before the top-up added about 0.45 USD. 15-turn stage: 1.35 USD plus 0.06 USD generation. Proposals about
0.02 USD. Round 2 total about 5.2 USD at list price, before DeepSeek cache discounts. Round 1 was 0.68 USD.
