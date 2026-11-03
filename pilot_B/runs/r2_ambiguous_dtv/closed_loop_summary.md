# Closed-loop pilot summary (r2_ambiguous_dtv)

solver `async_solvers:dtv_solve`, model `na`, 10 trajectories, 5 turns, elapsed 151.5 s, solver errors 0.


## 1. Accuracy vs turn (macro mean over trajectories; percentages)

all_field_acc = correct leaf verdicts / all scored leaves (repo public evaluator, strict exact match; open-text paraphrases count as wrong). structured_acc = same restricted to bool/number/choice/date/time leaves. fully_correct = every leaf correct.

### all-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 97.9 | 91.7 | 89.4 | 89.7 | 87.7 | 89.6 |
| oracle | 97.9 | 93.8 | 95.1 | 95.7 | 94.6 | 94.8 |

### structured-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 97.8 | 92.4 | 91.3 | 93.3 | 93.7 | 92.6 |
| oracle | 97.8 | 95.4 | 95.9 | 97.9 | 97.9 | 96.8 |

### fully-correct record rate (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 40.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| oracle | 40.0 | 20.0 | 20.0 | 20.0 | 30.0 | 22.5 |

### all-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 97.9 | 91.7 | 89.2 | 89.4 | 86.4 | 89.2 |
| oracle | 97.9 | 93.8 | 93.4 | 94.8 | 93.0 | 93.7 |

### structured-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 97.8 | 92.4 | 90.0 | 92.2 | 91.5 | 91.5 |
| oracle | 97.8 | 95.4 | 92.1 | 94.5 | 94.5 | 94.1 |

### fully-correct record rate (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 40.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| oracle | 40.0 | 20.0 | 0.0 | 0.0 | 0.0 | 5.0 |

### micro all-field accuracy, clean (sum correct / sum leaves, T1-T5)

| condition | correct/total | micro acc |
|---|---|---|
| incremental | 1669/1818 | 91.8 |
| oracle | 1742/1818 | 95.8 |

## 2. Condition gaps (clean; per-trajectory mean over T2-T5; paired bootstrap 95% CI over trajectories)

| comparison | metric | mean diff (pp) | 95% CI (pp) | n traj |
|---|---|---|---|---|
| incremental - oracle | all_field_acc | -5.2 | [-7.4, -3.3] | 10 |
| incremental - oracle | structured_acc | -4.2 | [-6.5, -1.3] | 10 |
| incremental - oracle | fully_correct | -22.5 | [-37.5, -10.0] | 10 |

## 3. Injected corruption (one structured field overwritten after T2; never mentioned again)

| trajectory | condition | field | injected | gold | system had it right at T2 | persisted T3/T4/T5 | persistence length | recovered at |
|---|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `time_of_accident` | "18:30" | "18:45" | False | 1/1/1 | 3 | never |
| cr_gen_01 | oracle | `time_of_accident` | "18:30" | "18:45" | False | 1/1/1 | 3 | never |
| cr_gen_02 | incremental | `lighting` | "Dark\u2013Lit" | "Dark\u2013Unlit" | True | 0/0/0 | 0 | 3 |
| cr_gen_02 | oracle | `lighting` | "Dark\u2013Lit" | "Dark\u2013Unlit" | True | 1/1/1 | 3 | never |
| cr_gen_03 | incremental | `road_surface_condition` | "Wet" | "Dry" | True | 0/0/0 | 0 | 3 |
| cr_gen_03 | oracle | `road_surface_condition` | "Wet" | "Dry" | True | 0/0/0 | 0 | never |
| cr_gen_04 | incremental | `lighting` | "Dark\u2013Lit" | "Dusk / Dawn" | True | 1/1/1 | 3 | never |
| cr_gen_04 | oracle | `lighting` | "Dark\u2013Lit" | "Dusk / Dawn" | True | 1/1/1 | 3 | never |
| pa_gen_01 | incremental | `pain_details[0].pain_severity` | "Mild" | "Moderate" | True | 1/1/1 | 3 | never |
| pa_gen_01 | oracle | `pain_details[0].pain_severity` | "Mild" | "Moderate" | True | 1/1/1 | 3 | never |
| pa_gen_02 | incremental | `allergies[0].allergy_severity` | "Severe" | "Moderate" | False | 1/1/1 | 3 | never |
| pa_gen_02 | oracle | `allergies[0].allergy_severity` | "Severe" | "Moderate" | False | 1/1/1 | 3 | never |
| pa_gen_03 | incremental | `upper_denture` | "No" | "Yes" | False | 0/0/0 | 0 | 3 |
| pa_gen_03 | oracle | `upper_denture` | "No" | "Yes" | False | 1/1/1 | 3 | never |
| pa_gen_04 | incremental | `ambulatory_aid_use` | "Has but does not use" | "Yes (uses)" | False | 1/1/1 | 3 | never |
| pa_gen_04 | oracle | `ambulatory_aid_use` | "Has but does not use" | "Yes (uses)" | False | 1/1/1 | 3 | never |
| pa_gen_05 | incremental | `pain_details[0].pain_severity` | "Moderate" | "Mild" | False | 1/1/1 | 3 | never |
| pa_gen_05 | oracle | `pain_details[0].pain_severity` | "Moderate" | "Mild" | False | 1/1/1 | 3 | never |
| pa_handmade_01 | incremental | `sputum_amount` | "Moderate" | "Small" | False | 1/1/1 | 3 | never |
| pa_handmade_01 | oracle | `sputum_amount` | "Moderate" | "Small" | False | 1/1/1 | 3 | never |

| condition | n | wrong value survived T3 | mean persistence length (0-3 turns) | silently recovered by T5 | never recovered |
|---|---|---|---|---|---|
| incremental | 10 | 7/10 | 2.10 | 3/10 | 7/10 |
| oracle | 10 | 9/10 | 2.70 | 0/10 | 10/10 |

rebuild: not applicable (no state channel; a corrupted record is discarded each turn by construction).

### accuracy cost of the injection (corrupt - clean, all_field_acc, mean over T3-T5, pp)

| condition | clean | corrupt | diff |
|---|---|---|---|
| incremental | 88.9 | 88.3 | -0.6 |
| oracle | 95.2 | 93.7 | -1.4 |

## 4. Collateral edits and natural (non-injected) error persistence, clean mode, T2-T5

collateral: leaves correct in the previous record (incremental/oracle: the prior handed in; rebuild: its own previous output) and unchanged in gold this turn, but wrong after the turn. natural persistence: structured leaves wrong in the system's own previous output, gold unchanged this turn -> still the same wrong value.

| condition | collateral edits / opportunities | of which non-empty gold | natural: opportunities | persisted | recovered | persist rate |
|---|---|---|---|---|---|---|
| incremental | 11/1177 (0.9%) | 3 | 45 | 32 | 10 | 71.1% |
| oracle | 26/1277 (2.0%) | 7 | 22 | 1 | 21 | 4.5% |

## 5. Per questionnaire (clean, mean all_field_acc over T1-T5, %)

| questionnaire | n traj | incremental | rebuild | oracle |
|---|---|---|---|---|
| crash_report | 4 | 86.4 | - | 92.3 |
| patient_admin | 6 | 94.5 | - | 97.5 |

## 6. Tokens and cost (this run, cache hits excluded)

| condition | mode | billed calls | input tok | output tok | reasoning tok | mean in/call | mean out/call |
|---|---|---|---|---|---|---|---|
| incremental | clean | 126 | 728663 | 10989 | 0 | 5783 | 87 |
| oracle | clean | 109 | 634976 | 9563 | 0 | 5825 | 87 |
| incremental | corrupt | 69 | 398221 | 8353 | 0 | 5771 | 121 |
| oracle | corrupt | 84 | 484030 | 6928 | 0 | 5762 | 82 |

Total billed: 2245890 input + 35833 output tokens -> ~$0.717 at assumed $0.3/M in, $1.2/M out.
Turns needing a Direct retry (invalid JSON/shape): 129; prior-state fallbacks: 0.
