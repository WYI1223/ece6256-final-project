# Closed-loop pilot summary (closed_loop)

solver `conformbench.systems.direct:solve`, model `deepseek-flash:thinking=disabled`, 10 trajectories, 5 turns, elapsed 57.7 s, solver errors 0.


## 1. Accuracy vs turn (macro mean over trajectories; percentages)

all_field_acc = correct leaf verdicts / all scored leaves (repo public evaluator, strict exact match; open-text paraphrases count as wrong). structured_acc = same restricted to bool/number/choice/date/time leaves. fully_correct = every leaf correct.

### all-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.2 | 93.7 | 91.1 | 91.4 | 89.8 | 91.5 |
| rebuild | 99.2 | 94.0 | 91.2 | 90.0 | 89.2 | 91.1 |
| oracle | 99.2 | 94.1 | 95.7 | 95.7 | 95.9 | 95.4 |

### structured-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.5 | 97.1 | 93.8 | 95.8 | 96.9 | 95.9 |
| rebuild | 99.5 | 96.1 | 93.8 | 94.5 | 95.4 | 94.9 |
| oracle | 99.5 | 97.5 | 97.3 | 98.8 | 99.6 | 98.3 |

### fully-correct record rate (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 80.0 | 20.0 | 20.0 | 20.0 | 10.0 | 17.5 |
| rebuild | 80.0 | 20.0 | 20.0 | 20.0 | 10.0 | 17.5 |
| oracle | 80.0 | 30.0 | 30.0 | 40.0 | 30.0 | 32.5 |

### all-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.2 | 93.7 | 91.7 | 90.8 | 89.8 | 91.5 |
| oracle | 99.2 | 94.1 | 94.7 | 94.1 | 95.9 | 94.7 |

### structured-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.5 | 97.1 | 94.5 | 95.8 | 96.9 | 96.1 |
| oracle | 99.5 | 97.5 | 96.2 | 98.2 | 99.6 | 97.9 |

### fully-correct record rate (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 80.0 | 20.0 | 20.0 | 20.0 | 10.0 | 17.5 |
| oracle | 80.0 | 30.0 | 40.0 | 40.0 | 30.0 | 35.0 |

### micro all-field accuracy, clean (sum correct / sum leaves, T1-T5)

| condition | correct/total | micro acc |
|---|---|---|
| incremental | 1703/1818 | 93.7 |
| rebuild | 1694/1818 | 93.2 |
| oracle | 1756/1818 | 96.6 |

## 2. Condition gaps (clean; per-trajectory mean over T2-T5; paired bootstrap 95% CI over trajectories)

| comparison | metric | mean diff (pp) | 95% CI (pp) | n traj |
|---|---|---|---|---|
| incremental - oracle | all_field_acc | -3.9 | [-6.4, -1.6] | 10 |
| rebuild - oracle | all_field_acc | -4.3 | [-6.7, -2.1] | 10 |
| incremental - rebuild | all_field_acc | +0.4 | [-0.2, +0.9] | 10 |
| incremental - oracle | structured_acc | -2.4 | [-4.0, -0.9] | 10 |
| rebuild - oracle | structured_acc | -3.4 | [-5.4, -1.5] | 10 |
| incremental - rebuild | structured_acc | +0.9 | [+0.1, +1.9] | 10 |
| incremental - oracle | fully_correct | -15.0 | [-35.0, +0.0] | 10 |
| rebuild - oracle | fully_correct | -15.0 | [-37.5, +2.5] | 10 |
| incremental - rebuild | fully_correct | +0.0 | [-7.5, +7.5] | 10 |

## 3. Injected corruption (one structured field overwritten after T2; never mentioned again)

| trajectory | condition | field | injected | gold | system had it right at T2 | persisted T3/T4/T5 | persistence length | recovered at |
|---|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `date_of_accident` | "2024-03-17" | "2024-03-14" | True | 0/0/0 | 0 | 3 |
| cr_gen_01 | oracle | `date_of_accident` | "2024-03-17" | "2024-03-14" | True | 0/0/0 | 0 | 3 |
| cr_gen_02 | incremental | `lighting` | "Daylight" | "Dark\u2013Unlit" | True | 0/0/0 | 0 | 3 |
| cr_gen_02 | oracle | `lighting` | "Daylight" | "Dark\u2013Unlit" | True | 0/0/0 | 0 | 3 |
| cr_gen_03 | incremental | `lighting` | "Dusk / Dawn" | "Daylight" | True | 1/0/0 | 1 | 4 |
| cr_gen_03 | oracle | `lighting` | "Dusk / Dawn" | "Daylight" | True | 1/0/0 | 1 | 4 |
| cr_gen_04 | incremental | `lighting` | "Dark\u2013Lit" | "Dusk / Dawn" | True | 0/0/0 | 0 | 3 |
| cr_gen_04 | oracle | `lighting` | "Dark\u2013Lit" | "Dusk / Dawn" | True | 0/0/0 | 0 | 3 |
| pa_gen_01 | incremental | `pain_details[0].pain_severity` | "High" | "Moderate" | True | 0/0/0 | 0 | 3 |
| pa_gen_01 | oracle | `pain_details[0].pain_severity` | "High" | "Moderate" | True | 0/0/0 | 0 | 3 |
| pa_gen_02 | incremental | `allergies[0].allergy_severity` | "Severe" | "Moderate" | True | 0/0/0 | 0 | 3 |
| pa_gen_02 | oracle | `allergies[0].allergy_severity` | "Severe" | "Moderate" | True | 0/0/0 | 0 | 3 |
| pa_gen_03 | incremental | `ambulatory_aid_use` | "Yes (uses)" | "No" | True | 0/0/0 | 0 | 3 |
| pa_gen_03 | oracle | `ambulatory_aid_use` | "Yes (uses)" | "No" | True | 0/0/0 | 0 | 3 |
| pa_gen_04 | incremental | `ambulatory_aid_use` | "Has but does not use" | "Yes (uses)" | True | 0/0/0 | 0 | 3 |
| pa_gen_04 | oracle | `ambulatory_aid_use` | "Has but does not use" | "Yes (uses)" | True | 0/0/0 | 0 | 3 |
| pa_gen_05 | incremental | `pain_details[0].pain_severity` | "Moderate" | "Mild" | True | 0/0/0 | 0 | 3 |
| pa_gen_05 | oracle | `pain_details[0].pain_severity` | "Moderate" | "Mild" | True | 0/0/0 | 0 | 3 |
| pa_handmade_01 | incremental | `current_medications[0].route` | "Inhaled" | "Oral" | True | 0/0/0 | 0 | 3 |
| pa_handmade_01 | oracle | `current_medications[0].route` | "Inhaled" | "Oral" | True | 0/0/0 | 0 | 3 |

| condition | n | wrong value survived T3 | mean persistence length (0-3 turns) | silently recovered by T5 | never recovered |
|---|---|---|---|---|---|
| incremental | 10 | 1/10 | 0.10 | 10/10 | 0/10 |
| oracle | 10 | 1/10 | 0.10 | 10/10 | 0/10 |

rebuild: not applicable (no state channel; a corrupted record is discarded each turn by construction).

### accuracy cost of the injection (corrupt - clean, all_field_acc, mean over T3-T5, pp)

| condition | clean | corrupt | diff |
|---|---|---|---|
| incremental | 90.8 | 90.8 | -0.0 |
| oracle | 95.8 | 94.9 | -0.9 |

## 4. Collateral edits and natural (non-injected) error persistence, clean mode, T2-T5

collateral: leaves correct in the previous record (incremental/oracle: the prior handed in; rebuild: its own previous output) and unchanged in gold this turn, but wrong after the turn. natural persistence: structured leaves wrong in the system's own previous output, gold unchanged this turn -> still the same wrong value.

| condition | collateral edits / opportunities | of which non-empty gold | natural: opportunities | persisted | recovered | persist rate |
|---|---|---|---|---|---|---|
| incremental | 13/1204 (1.1%) | 0 | 20 | 19 | 1 | 95.0% |
| rebuild | 22/1198 (1.8%) | 4 | 24 | 21 | 2 | 87.5% |
| oracle | 28/1277 (2.2%) | 5 | 10 | 0 | 10 | 0.0% |

## 5. Per questionnaire (clean, mean all_field_acc over T1-T5, %)

| questionnaire | n traj | incremental | rebuild | oracle |
|---|---|---|---|---|
| crash_report | 4 | 86.6 | 86.8 | 92.6 |
| patient_admin | 6 | 97.4 | 96.7 | 98.5 |

## 6. Tokens and cost (this run, cache hits excluded)

| condition | mode | billed calls | input tok | output tok | reasoning tok | mean in/call | mean out/call |
|---|---|---|---|---|---|---|---|
| incremental | clean | 50 | 251905 | 20371 | 0 | 5038 | 407 |
| rebuild | clean | 40 | 199096 | 17381 | 0 | 4977 | 434 |
| oracle | clean | 26 | 130721 | 11140 | 0 | 5027 | 428 |
| incremental | corrupt | 18 | 88379 | 7810 | 0 | 4909 | 433 |
| oracle | corrupt | 9 | 43375 | 3503 | 0 | 4819 | 389 |

Total billed: 713476 input + 60205 output tokens -> ~$0.286 at assumed $0.3/M in, $1.2/M out.
Turns needing a Direct retry (invalid JSON/shape): 0; prior-state fallbacks: 0.
