# Closed-loop pilot summary (r2_ambiguous_v4pro)

solver `conformbench.systems.direct:solve`, model `deepseek-v4-pro:thinking=disabled`, 10 trajectories, 5 turns, elapsed 166.5 s, solver errors 0.


## 1. Accuracy vs turn (macro mean over trajectories; percentages)

all_field_acc = correct leaf verdicts / all scored leaves (repo public evaluator, strict exact match; open-text paraphrases count as wrong). structured_acc = same restricted to bool/number/choice/date/time leaves. fully_correct = every leaf correct.

### all-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 97.4 | 91.8 | 89.4 | 90.0 | 88.5 | 89.9 |
| oracle | 97.4 | 94.1 | 95.7 | 96.8 | 97.1 | 95.9 |

### structured-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 97.5 | 94.2 | 92.8 | 95.0 | 95.0 | 94.2 |
| oracle | 97.5 | 95.8 | 97.3 | 99.5 | 100.0 | 98.1 |

### fully-correct record rate (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 40.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| oracle | 40.0 | 30.0 | 60.0 | 50.0 | 50.0 | 47.5 |

### all-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 97.4 | 91.8 | 87.9 | 89.0 | 87.5 | 89.0 |
| oracle | 97.4 | 94.1 | 94.0 | 95.6 | 94.0 | 94.4 |

### structured-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 97.5 | 94.2 | 89.2 | 92.2 | 92.3 | 92.0 |
| oracle | 97.5 | 95.8 | 93.2 | 95.6 | 95.2 | 95.0 |

### fully-correct record rate (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 40.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| oracle | 40.0 | 30.0 | 0.0 | 10.0 | 0.0 | 10.0 |

### micro all-field accuracy, clean (sum correct / sum leaves, T1-T5)

| condition | correct/total | micro acc |
|---|---|---|
| incremental | 1674/1818 | 92.1 |
| oracle | 1759/1818 | 96.8 |

## 2. Condition gaps (clean; per-trajectory mean over T2-T5; paired bootstrap 95% CI over trajectories)

| comparison | metric | mean diff (pp) | 95% CI (pp) | n traj |
|---|---|---|---|---|
| incremental - oracle | all_field_acc | -6.0 | [-8.1, -4.1] | 10 |
| incremental - oracle | structured_acc | -3.9 | [-5.1, -2.6] | 10 |
| incremental - oracle | fully_correct | -47.5 | [-70.0, -25.0] | 10 |

## 3. Injected corruption (one structured field overwritten after T2; never mentioned again)

| trajectory | condition | field | injected | gold | system had it right at T2 | persisted T3/T4/T5 | persistence length | recovered at |
|---|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `time_of_accident` | "18:30" | "18:45" | False | 1/1/1 | 3 | never |
| cr_gen_01 | oracle | `time_of_accident` | "18:30" | "18:45" | False | 1/1/1 | 3 | never |
| cr_gen_02 | incremental | `lighting` | "Dark\u2013Lit" | "Dark\u2013Unlit" | True | 1/0/0 | 1 | 4 |
| cr_gen_02 | oracle | `lighting` | "Dark\u2013Lit" | "Dark\u2013Unlit" | True | 1/1/1 | 3 | never |
| cr_gen_03 | incremental | `road_surface_condition` | "Wet" | "Dry" | True | 1/1/1 | 3 | never |
| cr_gen_03 | oracle | `road_surface_condition` | "Wet" | "Dry" | True | 1/1/1 | 3 | never |
| cr_gen_04 | incremental | `lighting` | "Dark\u2013Lit" | "Dusk / Dawn" | True | 1/1/1 | 3 | never |
| cr_gen_04 | oracle | `lighting` | "Dark\u2013Lit" | "Dusk / Dawn" | True | 1/0/0 | 1 | 4 |
| pa_gen_01 | incremental | `pain_details[0].pain_severity` | "Mild" | "Moderate" | True | 1/1/1 | 3 | never |
| pa_gen_01 | oracle | `pain_details[0].pain_severity` | "Mild" | "Moderate" | True | 1/1/1 | 3 | never |
| pa_gen_02 | incremental | `allergies[0].allergy_severity` | "Severe" | "Moderate" | False | 1/1/1 | 3 | never |
| pa_gen_02 | oracle | `allergies[0].allergy_severity` | "Severe" | "Moderate" | False | 1/1/1 | 3 | never |
| pa_gen_03 | incremental | `upper_denture` | "No" | "Yes" | True | 1/1/0 | 2 | 5 |
| pa_gen_03 | oracle | `upper_denture` | "No" | "Yes" | True | 1/1/1 | 3 | never |
| pa_gen_04 | incremental | `ambulatory_aid_use` | "Has but does not use" | "Yes (uses)" | True | 1/1/1 | 3 | never |
| pa_gen_04 | oracle | `ambulatory_aid_use` | "Has but does not use" | "Yes (uses)" | True | 1/1/1 | 3 | never |
| pa_gen_05 | incremental | `pain_details[0].pain_severity` | "Moderate" | "Mild" | True | 1/1/1 | 3 | never |
| pa_gen_05 | oracle | `pain_details[0].pain_severity` | "Moderate" | "Mild" | True | 1/1/1 | 3 | never |
| pa_handmade_01 | incremental | `sputum_amount` | "Moderate" | "Small" | False | 1/1/1 | 3 | never |
| pa_handmade_01 | oracle | `sputum_amount` | "Moderate" | "Small" | False | 1/1/1 | 3 | never |

| condition | n | wrong value survived T3 | mean persistence length (0-3 turns) | silently recovered by T5 | never recovered |
|---|---|---|---|---|---|
| incremental | 10 | 10/10 | 2.70 | 2/10 | 8/10 |
| oracle | 10 | 10/10 | 2.80 | 1/10 | 9/10 |

rebuild: not applicable (no state channel; a corrupted record is discarded each turn by construction).

### accuracy cost of the injection (corrupt - clean, all_field_acc, mean over T3-T5, pp)

| condition | clean | corrupt | diff |
|---|---|---|---|
| incremental | 89.3 | 88.1 | -1.2 |
| oracle | 96.6 | 94.6 | -2.0 |

## 4. Collateral edits and natural (non-injected) error persistence, clean mode, T2-T5

collateral: leaves correct in the previous record (incremental/oracle: the prior handed in; rebuild: its own previous output) and unchanged in gold this turn, but wrong after the turn. natural persistence: structured leaves wrong in the system's own previous output, gold unchanged this turn -> still the same wrong value.

| condition | collateral edits / opportunities | of which non-empty gold | natural: opportunities | persisted | recovered | persist rate |
|---|---|---|---|---|---|---|
| incremental | 9/1184 (0.8%) | 0 | 31 | 31 | 0 | 100.0% |
| oracle | 21/1277 (1.6%) | 1 | 15 | 0 | 15 | 0.0% |

## 5. Per questionnaire (clean, mean all_field_acc over T1-T5, %)

| questionnaire | n traj | incremental | rebuild | oracle |
|---|---|---|---|---|
| crash_report | 4 | 86.0 | - | 93.0 |
| patient_admin | 6 | 95.0 | - | 98.4 |

## 6. Tokens and cost (this run, cache hits excluded)

| condition | mode | billed calls | input tok | output tok | reasoning tok | mean in/call | mean out/call |
|---|---|---|---|---|---|---|---|
| incremental | clean | 50 | 251899 | 20389 | 0 | 5037 | 407 |
| oracle | clean | 37 | 189770 | 15986 | 0 | 5128 | 432 |
| incremental | corrupt | 29 | 148375 | 12951 | 0 | 5116 | 446 |
| oracle | corrupt | 27 | 138122 | 11819 | 0 | 5115 | 437 |

Total billed: 728166 input + 61145 output tokens -> ~$0.292 at assumed $0.3/M in, $1.2/M out.
Turns needing a Direct retry (invalid JSON/shape): 1; prior-state fallbacks: 0.
