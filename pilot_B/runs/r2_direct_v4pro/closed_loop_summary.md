# Closed-loop pilot summary (r2_direct_v4pro)

solver `conformbench.systems.direct:solve`, model `deepseek-v4-pro:thinking=disabled`, 10 trajectories, 5 turns, elapsed 166.5 s, solver errors 0.


## 1. Accuracy vs turn (macro mean over trajectories; percentages)

all_field_acc = correct leaf verdicts / all scored leaves (repo public evaluator, strict exact match; open-text paraphrases count as wrong). structured_acc = same restricted to bool/number/choice/date/time leaves. fully_correct = every leaf correct.

### all-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.2 | 94.2 | 92.4 | 92.8 | 90.9 | 92.6 |
| rebuild | 99.2 | 94.6 | 93.3 | 92.2 | 88.8 | 92.2 |
| oracle | 99.2 | 94.9 | 95.7 | 97.0 | 96.5 | 96.0 |

### structured-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 100.0 | 96.9 | 95.6 | 97.0 | 97.1 | 96.7 |
| rebuild | 100.0 | 97.7 | 96.9 | 96.5 | 97.5 | 97.2 |
| oracle | 100.0 | 96.9 | 96.1 | 100.0 | 100.0 | 98.3 |

### fully-correct record rate (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 80.0 | 20.0 | 20.0 | 20.0 | 10.0 | 17.5 |
| rebuild | 80.0 | 30.0 | 20.0 | 30.0 | 10.0 | 22.5 |
| oracle | 80.0 | 40.0 | 60.0 | 40.0 | 50.0 | 47.5 |

### all-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.2 | 94.2 | 90.2 | 91.6 | 90.6 | 91.7 |
| oracle | 99.2 | 94.9 | 95.2 | 96.7 | 96.5 | 95.8 |

### structured-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 100.0 | 96.9 | 92.5 | 95.6 | 96.1 | 95.3 |
| oracle | 100.0 | 96.9 | 96.2 | 99.4 | 99.4 | 98.0 |

### fully-correct record rate (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 80.0 | 20.0 | 10.0 | 20.0 | 10.0 | 15.0 |
| oracle | 80.0 | 40.0 | 40.0 | 40.0 | 50.0 | 42.5 |

### micro all-field accuracy, clean (sum correct / sum leaves, T1-T5)

| condition | correct/total | micro acc |
|---|---|---|
| incremental | 1714/1818 | 94.3 |
| rebuild | 1711/1818 | 94.1 |
| oracle | 1766/1818 | 97.1 |

## 2. Condition gaps (clean; per-trajectory mean over T2-T5; paired bootstrap 95% CI over trajectories)

| comparison | metric | mean diff (pp) | 95% CI (pp) | n traj |
|---|---|---|---|---|
| incremental - oracle | all_field_acc | -3.5 | [-5.9, -1.6] | 10 |
| rebuild - oracle | all_field_acc | -3.8 | [-6.0, -1.9] | 10 |
| incremental - rebuild | all_field_acc | +0.3 | [-1.5, +2.0] | 10 |
| incremental - oracle | structured_acc | -1.6 | [-3.1, -0.3] | 10 |
| rebuild - oracle | structured_acc | -1.1 | [-2.1, -0.1] | 10 |
| incremental - rebuild | structured_acc | -0.5 | [-1.9, +1.0] | 10 |
| incremental - oracle | fully_correct | -30.0 | [-55.0, -7.5] | 10 |
| rebuild - oracle | fully_correct | -25.0 | [-47.5, -5.0] | 10 |
| incremental - rebuild | fully_correct | -5.0 | [-22.5, +10.0] | 10 |

## 3. Injected corruption (one structured field overwritten after T2; never mentioned again)

| trajectory | condition | field | injected | gold | system had it right at T2 | persisted T3/T4/T5 | persistence length | recovered at |
|---|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `date_of_accident` | "2024-03-17" | "2024-03-14" | True | 0/0/0 | 0 | 3 |
| cr_gen_01 | oracle | `date_of_accident` | "2024-03-17" | "2024-03-14" | True | 0/0/0 | 0 | 3 |
| cr_gen_02 | incremental | `lighting` | "Daylight" | "Dark\u2013Unlit" | True | 0/0/0 | 0 | 3 |
| cr_gen_02 | oracle | `lighting` | "Daylight" | "Dark\u2013Unlit" | True | 0/0/0 | 0 | 3 |
| cr_gen_03 | incremental | `lighting` | "Dusk / Dawn" | "Daylight" | True | 1/0/0 | 1 | never |
| cr_gen_03 | oracle | `lighting` | "Dusk / Dawn" | "Daylight" | True | 1/1/1 | 3 | never |
| cr_gen_04 | incremental | `lighting` | "Dark\u2013Lit" | "Dusk / Dawn" | True | 0/0/0 | 0 | 3 |
| cr_gen_04 | oracle | `lighting` | "Dark\u2013Lit" | "Dusk / Dawn" | True | 0/0/0 | 0 | 3 |
| pa_gen_01 | incremental | `pain_details[0].pain_severity` | "High" | "Moderate" | True | 0/0/0 | 0 | 3 |
| pa_gen_01 | oracle | `pain_details[0].pain_severity` | "High" | "Moderate" | True | 0/0/0 | 0 | 3 |
| pa_gen_02 | incremental | `allergies[0].allergy_severity` | "Severe" | "Moderate" | True | 0/0/0 | 0 | 3 |
| pa_gen_02 | oracle | `allergies[0].allergy_severity` | "Severe" | "Moderate" | True | 0/0/0 | 0 | 3 |
| pa_gen_03 | incremental | `ambulatory_aid_use` | "Yes (uses)" | "No" | True | 0/0/0 | 0 | 3 |
| pa_gen_03 | oracle | `ambulatory_aid_use` | "Yes (uses)" | "No" | True | 0/0/0 | 0 | 3 |
| pa_gen_04 | incremental | `ambulatory_aid_use` | "Has but does not use" | "Yes (uses)" | True | 1/0/0 | 1 | 4 |
| pa_gen_04 | oracle | `ambulatory_aid_use` | "Has but does not use" | "Yes (uses)" | True | 1/0/0 | 1 | 4 |
| pa_gen_05 | incremental | `pain_details[0].pain_severity` | "Moderate" | "Mild" | True | 0/0/0 | 0 | 3 |
| pa_gen_05 | oracle | `pain_details[0].pain_severity` | "Moderate" | "Mild" | True | 0/0/0 | 0 | 3 |
| pa_handmade_01 | incremental | `current_medications[0].route` | "Inhaled" | "Oral" | True | 0/0/0 | 0 | 3 |
| pa_handmade_01 | oracle | `current_medications[0].route` | "Inhaled" | "Oral" | True | 0/0/0 | 0 | 3 |

| condition | n | wrong value survived T3 | mean persistence length (0-3 turns) | silently recovered by T5 | never recovered |
|---|---|---|---|---|---|
| incremental | 10 | 2/10 | 0.20 | 9/10 | 1/10 |
| oracle | 10 | 2/10 | 0.40 | 9/10 | 1/10 |

rebuild: not applicable (no state channel; a corrupted record is discarded each turn by construction).

### accuracy cost of the injection (corrupt - clean, all_field_acc, mean over T3-T5, pp)

| condition | clean | corrupt | diff |
|---|---|---|---|
| incremental | 92.0 | 90.8 | -1.2 |
| oracle | 96.4 | 96.1 | -0.3 |

## 4. Collateral edits and natural (non-injected) error persistence, clean mode, T2-T5

collateral: leaves correct in the previous record (incremental/oracle: the prior handed in; rebuild: its own previous output) and unchanged in gold this turn, but wrong after the turn. natural persistence: structured leaves wrong in the system's own previous output, gold unchanged this turn -> still the same wrong value.

| condition | collateral edits / opportunities | of which non-empty gold | natural: opportunities | persisted | recovered | persist rate |
|---|---|---|---|---|---|---|
| incremental | 9/1212 (0.7%) | 0 | 16 | 16 | 0 | 100.0% |
| rebuild | 26/1217 (2.1%) | 9 | 11 | 5 | 4 | 45.5% |
| oracle | 21/1277 (1.6%) | 2 | 9 | 1 | 8 | 11.1% |

## 5. Per questionnaire (clean, mean all_field_acc over T1-T5, %)

| questionnaire | n traj | incremental | rebuild | oracle |
|---|---|---|---|---|
| crash_report | 4 | 88.7 | 88.2 | 93.0 |
| patient_admin | 6 | 97.4 | 97.3 | 99.1 |

## 6. Tokens and cost (this run, cache hits excluded)

| condition | mode | billed calls | input tok | output tok | reasoning tok | mean in/call | mean out/call |
|---|---|---|---|---|---|---|---|
| incremental | clean | 48 | 240642 | 19675 | 0 | 5013 | 409 |
| rebuild | clean | 40 | 199056 | 17060 | 0 | 4976 | 426 |
| oracle | clean | 28 | 141693 | 12029 | 0 | 5060 | 429 |
| incremental | corrupt | 17 | 85013 | 7266 | 0 | 5000 | 427 |
| oracle | corrupt | 10 | 47740 | 3952 | 0 | 4774 | 395 |

Total billed: 714144 input + 59982 output tokens -> ~$0.286 at assumed $0.3/M in, $1.2/M out.
Turns needing a Direct retry (invalid JSON/shape): 0; prior-state fallbacks: 0.
