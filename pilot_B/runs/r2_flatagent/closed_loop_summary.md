# Closed-loop pilot summary (r2_flatagent)

solver `async_solvers:flatagent_solve`, model `na`, 10 trajectories, 5 turns, elapsed 34.1 s, solver errors 0.


## 1. Accuracy vs turn (macro mean over trajectories; percentages)

all_field_acc = correct leaf verdicts / all scored leaves (repo public evaluator, strict exact match; open-text paraphrases count as wrong). structured_acc = same restricted to bool/number/choice/date/time leaves. fully_correct = every leaf correct.

### all-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 98.7 | 94.9 | 92.4 | 92.0 | 89.3 | 92.1 |
| rebuild | 98.7 | 93.6 | 91.1 | 89.5 | 86.3 | 90.1 |
| oracle | 98.7 | 95.6 | 95.8 | 97.2 | 96.5 | 96.3 |

### structured-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.5 | 97.1 | 94.6 | 96.0 | 95.0 | 95.7 |
| rebuild | 99.5 | 96.5 | 94.3 | 93.8 | 94.7 | 94.8 |
| oracle | 99.5 | 97.5 | 97.0 | 100.0 | 99.4 | 98.5 |

### fully-correct record rate (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 70.0 | 30.0 | 20.0 | 20.0 | 10.0 | 20.0 |
| rebuild | 70.0 | 10.0 | 10.0 | 30.0 | 10.0 | 15.0 |
| oracle | 70.0 | 50.0 | 50.0 | 40.0 | 50.0 | 47.5 |

### all-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 98.7 | 94.9 | 92.2 | 91.7 | 89.4 | 92.1 |
| oracle | 98.7 | 95.6 | 96.9 | 97.2 | 96.5 | 96.5 |

### structured-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.5 | 97.1 | 94.1 | 96.1 | 95.6 | 95.7 |
| oracle | 99.5 | 97.5 | 98.5 | 100.0 | 99.4 | 98.8 |

### fully-correct record rate (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 70.0 | 30.0 | 20.0 | 20.0 | 10.0 | 20.0 |
| oracle | 70.0 | 50.0 | 50.0 | 40.0 | 50.0 | 47.5 |

### micro all-field accuracy, clean (sum correct / sum leaves, T1-T5)

| condition | correct/total | micro acc |
|---|---|---|
| incremental | 1705/1818 | 93.8 |
| rebuild | 1679/1818 | 92.4 |
| oracle | 1766/1818 | 97.1 |

## 2. Condition gaps (clean; per-trajectory mean over T2-T5; paired bootstrap 95% CI over trajectories)

| comparison | metric | mean diff (pp) | 95% CI (pp) | n traj |
|---|---|---|---|---|
| incremental - oracle | all_field_acc | -4.1 | [-6.3, -1.9] | 10 |
| rebuild - oracle | all_field_acc | -6.1 | [-10.1, -2.6] | 10 |
| incremental - rebuild | all_field_acc | +2.0 | [+0.3, +4.2] | 10 |
| incremental - oracle | structured_acc | -2.8 | [-4.3, -1.2] | 10 |
| rebuild - oracle | structured_acc | -3.6 | [-6.8, -0.8] | 10 |
| incremental - rebuild | structured_acc | +0.8 | [-1.4, +3.2] | 10 |
| incremental - oracle | fully_correct | -27.5 | [-52.5, -5.0] | 10 |
| rebuild - oracle | fully_correct | -32.5 | [-55.0, -10.0] | 10 |
| incremental - rebuild | fully_correct | +5.0 | [-5.0, +17.5] | 10 |

## 3. Injected corruption (one structured field overwritten after T2; never mentioned again)

| trajectory | condition | field | injected | gold | system had it right at T2 | persisted T3/T4/T5 | persistence length | recovered at |
|---|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `date_of_accident` | "2024-03-17" | "2024-03-14" | True | 0/0/0 | 0 | 3 |
| cr_gen_01 | oracle | `date_of_accident` | "2024-03-17" | "2024-03-14" | True | 0/0/0 | 0 | 3 |
| cr_gen_02 | incremental | `lighting` | "Daylight" | "Dark\u2013Unlit" | True | 0/0/0 | 0 | 3 |
| cr_gen_02 | oracle | `lighting` | "Daylight" | "Dark\u2013Unlit" | True | 0/0/0 | 0 | 3 |
| cr_gen_03 | incremental | `road_surface_condition` | "Wet" | "Dry" | True | 0/0/0 | 0 | 3 |
| cr_gen_03 | oracle | `road_surface_condition` | "Wet" | "Dry" | True | 0/0/0 | 0 | 3 |
| cr_gen_04 | incremental | `lighting` | "Dark\u2013Lit" | "Dusk / Dawn" | True | 1/0/0 | 1 | 4 |
| cr_gen_04 | oracle | `lighting` | "Dark\u2013Lit" | "Dusk / Dawn" | True | 0/0/0 | 0 | 3 |
| pa_gen_01 | incremental | `pain_details[0].pain_severity` | "High" | "Moderate" | True | 0/0/0 | 0 | 3 |
| pa_gen_01 | oracle | `pain_details[0].pain_severity` | "High" | "Moderate" | True | 0/0/0 | 0 | 3 |
| pa_gen_02 | incremental | `allergies[0].allergy_severity` | "Severe" | "Moderate" | True | 0/0/0 | 0 | 3 |
| pa_gen_02 | oracle | `allergies[0].allergy_severity` | "Severe" | "Moderate" | True | 0/0/0 | 0 | 3 |
| pa_gen_03 | incremental | `ambulatory_aid_use` | "Yes (uses)" | "No" | True | 0/0/0 | 0 | 3 |
| pa_gen_03 | oracle | `ambulatory_aid_use` | "Yes (uses)" | "No" | True | 0/0/0 | 0 | 3 |
| pa_gen_04 | incremental | `ambulatory_aid_use` | "Has but does not use" | "Yes (uses)" | True | 0/0/0 | 0 | 3 |
| pa_gen_04 | oracle | `ambulatory_aid_use` | "Has but does not use" | "Yes (uses)" | True | 0/0/0 | 0 | 3 |
| pa_gen_05 | incremental | `pain_details[0].pain_severity` | "Moderate" | "Mild" | True | 1/1/1 | 3 | never |
| pa_gen_05 | oracle | `pain_details[0].pain_severity` | "Moderate" | "Mild" | True | 0/0/0 | 0 | 3 |
| pa_handmade_01 | incremental | `current_medications[0].route` | "Inhaled" | "Oral" | True | 0/0/0 | 0 | 3 |
| pa_handmade_01 | oracle | `current_medications[0].route` | "Inhaled" | "Oral" | True | 0/0/0 | 0 | 3 |

| condition | n | wrong value survived T3 | mean persistence length (0-3 turns) | silently recovered by T5 | never recovered |
|---|---|---|---|---|---|
| incremental | 10 | 2/10 | 0.40 | 9/10 | 1/10 |
| oracle | 10 | 0/10 | 0.00 | 10/10 | 0/10 |

rebuild: not applicable (no state channel; a corrupted record is discarded each turn by construction).

### accuracy cost of the injection (corrupt - clean, all_field_acc, mean over T3-T5, pp)

| condition | clean | corrupt | diff |
|---|---|---|---|
| incremental | 91.2 | 91.1 | -0.1 |
| oracle | 96.5 | 96.8 | +0.4 |

## 4. Collateral edits and natural (non-injected) error persistence, clean mode, T2-T5

collateral: leaves correct in the previous record (incremental/oracle: the prior handed in; rebuild: its own previous output) and unchanged in gold this turn, but wrong after the turn. natural persistence: structured leaves wrong in the system's own previous output, gold unchanged this turn -> still the same wrong value.

| condition | collateral edits / opportunities | of which non-empty gold | natural: opportunities | persisted | recovered | persist rate |
|---|---|---|---|---|---|---|
| incremental | 7/1206 (0.6%) | 0 | 21 | 21 | 0 | 100.0% |
| rebuild | 41/1193 (3.4%) | 19 | 25 | 15 | 7 | 60.0% |
| oracle | 19/1277 (1.5%) | 2 | 7 | 3 | 4 | 42.9% |

## 5. Per questionnaire (clean, mean all_field_acc over T1-T5, %)

| questionnaire | n traj | incremental | rebuild | oracle |
|---|---|---|---|---|
| crash_report | 4 | 88.6 | 85.6 | 93.6 |
| patient_admin | 6 | 96.7 | 96.0 | 98.9 |

## 6. Tokens and cost (this run, cache hits excluded)

| condition | mode | billed calls | input tok | output tok | reasoning tok | mean in/call | mean out/call |
|---|---|---|---|---|---|---|---|
| incremental | clean | 4 | 22452 | 397 | 0 | 5613 | 99 |
| rebuild | clean | 4 | 22114 | 933 | 0 | 5528 | 233 |
| oracle | clean | 2 | 12389 | 131 | 0 | 6194 | 65 |
| incremental | corrupt | 40 | 224694 | 3869 | 0 | 5617 | 96 |
| oracle | corrupt | 16 | 89033 | 1706 | 0 | 5564 | 106 |

Total billed: 370682 input + 7036 output tokens -> ~$0.120 at assumed $0.3/M in, $1.2/M out.
Turns needing a Direct retry (invalid JSON/shape): 33; prior-state fallbacks: 0.
