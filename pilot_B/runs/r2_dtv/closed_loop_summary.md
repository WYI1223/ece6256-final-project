# Closed-loop pilot summary (r2_dtv)

solver `async_solvers:dtv_solve`, model `na`, 10 trajectories, 5 turns, elapsed 189.8 s, solver errors 0.


## 1. Accuracy vs turn (macro mean over trajectories; percentages)

all_field_acc = correct leaf verdicts / all scored leaves (repo public evaluator, strict exact match; open-text paraphrases count as wrong). structured_acc = same restricted to bool/number/choice/date/time leaves. fully_correct = every leaf correct.

### all-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 98.1 | 93.0 | 90.7 | 90.1 | 88.1 | 90.5 |
| rebuild | 98.1 | 94.0 | 91.1 | 92.5 | 88.7 | 91.5 |
| oracle | 98.1 | 94.6 | 94.3 | 95.7 | 97.1 | 95.4 |

### structured-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 98.3 | 94.4 | 92.6 | 94.4 | 94.5 | 94.0 |
| rebuild | 98.3 | 95.8 | 93.9 | 96.4 | 97.0 | 95.8 |
| oracle | 98.3 | 96.1 | 96.0 | 98.4 | 99.6 | 97.5 |

### fully-correct record rate (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 50.0 | 10.0 | 10.0 | 10.0 | 0.0 | 7.5 |
| rebuild | 50.0 | 30.0 | 10.0 | 30.0 | 10.0 | 20.0 |
| oracle | 50.0 | 40.0 | 40.0 | 40.0 | 50.0 | 42.5 |

### all-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 98.1 | 93.0 | 91.1 | 89.2 | 87.3 | 90.1 |
| oracle | 98.1 | 94.6 | 94.7 | 95.7 | 97.1 | 95.5 |

### structured-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 98.3 | 94.4 | 94.2 | 94.5 | 94.6 | 94.4 |
| oracle | 98.3 | 96.1 | 97.1 | 98.4 | 99.6 | 97.8 |

### fully-correct record rate (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 50.0 | 10.0 | 10.0 | 10.0 | 0.0 | 7.5 |
| oracle | 50.0 | 40.0 | 50.0 | 40.0 | 50.0 | 45.0 |

### micro all-field accuracy, clean (sum correct / sum leaves, T1-T5)

| condition | correct/total | micro acc |
|---|---|---|
| incremental | 1685/1818 | 92.7 |
| rebuild | 1698/1818 | 93.4 |
| oracle | 1754/1818 | 96.5 |

## 2. Condition gaps (clean; per-trajectory mean over T2-T5; paired bootstrap 95% CI over trajectories)

| comparison | metric | mean diff (pp) | 95% CI (pp) | n traj |
|---|---|---|---|---|
| incremental - oracle | all_field_acc | -4.9 | [-8.3, -2.2] | 10 |
| rebuild - oracle | all_field_acc | -3.9 | [-6.3, -1.6] | 10 |
| incremental - rebuild | all_field_acc | -1.0 | [-2.7, +0.4] | 10 |
| incremental - oracle | structured_acc | -3.5 | [-5.2, -2.0] | 10 |
| rebuild - oracle | structured_acc | -1.7 | [-3.0, -0.4] | 10 |
| incremental - rebuild | structured_acc | -1.8 | [-3.0, -0.7] | 10 |
| incremental - oracle | fully_correct | -35.0 | [-57.5, -15.0] | 10 |
| rebuild - oracle | fully_correct | -22.5 | [-47.5, +0.0] | 10 |
| incremental - rebuild | fully_correct | -12.5 | [-27.5, +0.0] | 10 |

## 3. Injected corruption (one structured field overwritten after T2; never mentioned again)

| trajectory | condition | field | injected | gold | system had it right at T2 | persisted T3/T4/T5 | persistence length | recovered at |
|---|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `date_of_accident` | "2024-03-17" | "2024-03-14" | True | 0/0/0 | 0 | 3 |
| cr_gen_01 | oracle | `date_of_accident` | "2024-03-17" | "2024-03-14" | True | 0/0/0 | 0 | 3 |
| cr_gen_02 | incremental | `lighting` | "Daylight" | "Dark\u2013Unlit" | True | 0/0/0 | 0 | 3 |
| cr_gen_02 | oracle | `lighting` | "Daylight" | "Dark\u2013Unlit" | True | 0/0/0 | 0 | 3 |
| cr_gen_03 | incremental | `road_surface_condition` | "Wet" | "Dry" | True | 0/0/0 | 0 | 3 |
| cr_gen_03 | oracle | `road_surface_condition` | "Wet" | "Dry" | True | 0/0/0 | 0 | 3 |
| cr_gen_04 | incremental | `road_surface_condition` | "Wet" | "Dry" | True | 0/0/0 | 0 | 3 |
| cr_gen_04 | oracle | `road_surface_condition` | "Wet" | "Dry" | True | 0/0/0 | 0 | 3 |
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
| incremental | 10 | 0/10 | 0.00 | 10/10 | 0/10 |
| oracle | 10 | 0/10 | 0.00 | 10/10 | 0/10 |

rebuild: not applicable (no state channel; a corrupted record is discarded each turn by construction).

### accuracy cost of the injection (corrupt - clean, all_field_acc, mean over T3-T5, pp)

| condition | clean | corrupt | diff |
|---|---|---|---|
| incremental | 89.6 | 89.2 | -0.5 |
| oracle | 95.7 | 95.8 | +0.1 |

## 4. Collateral edits and natural (non-injected) error persistence, clean mode, T2-T5

collateral: leaves correct in the previous record (incremental/oracle: the prior handed in; rebuild: its own previous output) and unchanged in gold this turn, but wrong after the turn. natural persistence: structured leaves wrong in the system's own previous output, gold unchanged this turn -> still the same wrong value.

| condition | collateral edits / opportunities | of which non-empty gold | natural: opportunities | persisted | recovered | persist rate |
|---|---|---|---|---|---|---|
| incremental | 13/1194 (1.1%) | 0 | 32 | 27 | 4 | 84.4% |
| rebuild | 34/1205 (2.8%) | 10 | 23 | 13 | 9 | 56.5% |
| oracle | 25/1277 (2.0%) | 3 | 15 | 3 | 12 | 20.0% |

## 5. Per questionnaire (clean, mean all_field_acc over T1-T5, %)

| questionnaire | n traj | incremental | rebuild | oracle |
|---|---|---|---|---|
| crash_report | 4 | 84.9 | 87.0 | 92.3 |
| patient_admin | 6 | 96.8 | 96.7 | 98.4 |

## 6. Tokens and cost (this run, cache hits excluded)

| condition | mode | billed calls | input tok | output tok | reasoning tok | mean in/call | mean out/call |
|---|---|---|---|---|---|---|---|
| incremental | clean | 149 | 849491 | 11993 | 0 | 5701 | 80 |
| rebuild | clean | 121 | 690160 | 18726 | 0 | 5703 | 154 |
| oracle | clean | 101 | 584818 | 9041 | 0 | 5790 | 89 |
| incremental | corrupt | 51 | 285917 | 4947 | 0 | 5606 | 97 |
| oracle | corrupt | 28 | 158619 | 2579 | 0 | 5664 | 92 |

Total billed: 2569005 input + 47286 output tokens -> ~$0.827 at assumed $0.3/M in, $1.2/M out.
Turns needing a Direct retry (invalid JSON/shape): 149; prior-state fallbacks: 0.
