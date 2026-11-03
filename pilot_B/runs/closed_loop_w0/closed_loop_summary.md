# Closed-loop pilot summary (closed_loop_w0)

solver `conformbench.systems.direct:solve`, model `deepseek-flash:thinking=disabled`, 10 trajectories, 5 turns, elapsed 53.5 s, solver errors 0.


## 1. Accuracy vs turn (macro mean over trajectories; percentages)

all_field_acc = correct leaf verdicts / all scored leaves (repo public evaluator, strict exact match; open-text paraphrases count as wrong). structured_acc = same restricted to bool/number/choice/date/time leaves. fully_correct = every leaf correct.

### all-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.0 | 93.7 | 91.9 | 91.1 | 89.1 | 91.4 |
| oracle | 99.0 | 93.4 | 96.6 | 97.5 | 98.0 | 96.4 |

### structured-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.5 | 96.4 | 94.5 | 95.9 | 95.9 | 95.7 |
| oracle | 99.5 | 95.5 | 97.9 | 99.5 | 100.0 | 98.2 |

### fully-correct record rate (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 80.0 | 20.0 | 20.0 | 20.0 | 10.0 | 17.5 |
| oracle | 80.0 | 30.0 | 60.0 | 60.0 | 70.0 | 55.0 |

### all-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.0 | 93.7 | 89.0 | 88.5 | 86.9 | 89.5 |
| oracle | 99.0 | 93.4 | 94.9 | 95.5 | 95.6 | 94.9 |

### structured-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.5 | 96.4 | 89.3 | 90.9 | 91.0 | 91.9 |
| oracle | 99.5 | 95.5 | 92.7 | 94.5 | 94.7 | 94.4 |

### fully-correct record rate (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 80.0 | 20.0 | 0.0 | 0.0 | 0.0 | 5.0 |
| oracle | 80.0 | 30.0 | 0.0 | 0.0 | 0.0 | 7.5 |

### micro all-field accuracy, clean (sum correct / sum leaves, T1-T5)

| condition | correct/total | micro acc |
|---|---|---|
| incremental | 1697/1818 | 93.3 |
| oracle | 1767/1818 | 97.2 |

## 2. Condition gaps (clean; per-trajectory mean over T2-T5; paired bootstrap 95% CI over trajectories)

| comparison | metric | mean diff (pp) | 95% CI (pp) | n traj |
|---|---|---|---|---|
| incremental - oracle | all_field_acc | -4.9 | [-8.1, -2.3] | 10 |
| incremental - oracle | structured_acc | -2.6 | [-4.7, -0.5] | 10 |
| incremental - oracle | fully_correct | -37.5 | [-60.0, -17.5] | 10 |

## 3. Injected corruption (one structured field overwritten after T2; never mentioned again)

| trajectory | condition | field | injected | gold | system had it right at T2 | persisted T3/T4/T5 | persistence length | recovered at |
|---|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `date_of_accident` | "2024-03-17" | "2024-03-14" | True | 1/1/1 | 3 | never |
| cr_gen_01 | oracle | `date_of_accident` | "2024-03-17" | "2024-03-14" | True | 1/1/1 | 3 | never |
| cr_gen_02 | incremental | `lighting` | "Daylight" | "Dark\u2013Unlit" | True | 1/1/1 | 3 | never |
| cr_gen_02 | oracle | `lighting` | "Daylight" | "Dark\u2013Unlit" | True | 1/1/1 | 3 | never |
| cr_gen_03 | incremental | `road_surface_condition` | "Wet" | "Dry" | True | 1/1/1 | 3 | never |
| cr_gen_03 | oracle | `road_surface_condition` | "Wet" | "Dry" | True | 1/1/1 | 3 | never |
| cr_gen_04 | incremental | `lighting` | "Dark\u2013Lit" | "Dusk / Dawn" | True | 1/1/1 | 3 | never |
| cr_gen_04 | oracle | `lighting` | "Dark\u2013Lit" | "Dusk / Dawn" | True | 1/1/1 | 3 | never |
| pa_gen_01 | incremental | `pain_details[0].pain_severity` | "High" | "Moderate" | True | 1/1/1 | 3 | never |
| pa_gen_01 | oracle | `pain_details[0].pain_severity` | "High" | "Moderate" | True | 1/1/1 | 3 | never |
| pa_gen_02 | incremental | `allergies[0].allergy_severity` | "Severe" | "Moderate" | True | 1/1/1 | 3 | never |
| pa_gen_02 | oracle | `allergies[0].allergy_severity` | "Severe" | "Moderate" | True | 1/1/1 | 3 | never |
| pa_gen_03 | incremental | `ambulatory_aid_use` | "Yes (uses)" | "No" | True | 1/1/1 | 3 | never |
| pa_gen_03 | oracle | `ambulatory_aid_use` | "Yes (uses)" | "No" | True | 1/1/1 | 3 | never |
| pa_gen_04 | incremental | `ambulatory_aid_use` | "Has but does not use" | "Yes (uses)" | True | 1/1/1 | 3 | never |
| pa_gen_04 | oracle | `ambulatory_aid_use` | "Has but does not use" | "Yes (uses)" | True | 1/1/1 | 3 | never |
| pa_gen_05 | incremental | `pain_details[0].pain_severity` | "Moderate" | "Mild" | True | 1/1/1 | 3 | never |
| pa_gen_05 | oracle | `pain_details[0].pain_severity` | "Moderate" | "Mild" | True | 1/1/1 | 3 | never |
| pa_handmade_01 | incremental | `current_medications[0].route` | "Inhaled" | "Oral" | True | 0/0/0 | 0 | never |
| pa_handmade_01 | oracle | `current_medications[0].route` | "Inhaled" | "Oral" | True | 0/0/0 | 0 | never |

| condition | n | wrong value survived T3 | mean persistence length (0-3 turns) | silently recovered by T5 | never recovered |
|---|---|---|---|---|---|
| incremental | 10 | 9/10 | 2.70 | 0/10 | 10/10 |
| oracle | 10 | 9/10 | 2.70 | 0/10 | 10/10 |

rebuild: not applicable (no state channel; a corrupted record is discarded each turn by construction).

### accuracy cost of the injection (corrupt - clean, all_field_acc, mean over T3-T5, pp)

| condition | clean | corrupt | diff |
|---|---|---|---|
| incremental | 90.7 | 88.1 | -2.6 |
| oracle | 97.3 | 95.3 | -2.0 |

## 4. Collateral edits and natural (non-injected) error persistence, clean mode, T2-T5

collateral: leaves correct in the previous record (incremental/oracle: the prior handed in; rebuild: its own previous output) and unchanged in gold this turn, but wrong after the turn. natural persistence: structured leaves wrong in the system's own previous output, gold unchanged this turn -> still the same wrong value.

| condition | collateral edits / opportunities | of which non-empty gold | natural: opportunities | persisted | recovered | persist rate |
|---|---|---|---|---|---|---|
| incremental | 8/1200 (0.7%) | 0 | 22 | 22 | 0 | 100.0% |
| oracle | 19/1277 (1.5%) | 6 | 14 | 0 | 14 | 0.0% |

## 5. Per questionnaire (clean, mean all_field_acc over T1-T5, %)

| questionnaire | n traj | incremental | rebuild | oracle |
|---|---|---|---|---|
| crash_report | 4 | 86.9 | - | 94.3 |
| patient_admin | 6 | 97.0 | - | 98.6 |

## 6. Tokens and cost (this run, cache hits excluded)

| condition | mode | billed calls | input tok | output tok | reasoning tok | mean in/call | mean out/call |
|---|---|---|---|---|---|---|---|
| incremental | clean | 49 | 240734 | 19403 | 0 | 4912 | 395 |
| oracle | clean | 27 | 131936 | 11022 | 0 | 4886 | 408 |
| incremental | corrupt | 29 | 143470 | 12489 | 0 | 4947 | 430 |
| oracle | corrupt | 25 | 120985 | 9982 | 0 | 4839 | 399 |

Total billed: 637125 input + 52896 output tokens -> ~$0.255 at assumed $0.3/M in, $1.2/M out.
Turns needing a Direct retry (invalid JSON/shape): 0; prior-state fallbacks: 0.
