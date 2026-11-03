# Closed-loop pilot summary (r2_ambiguous_flatagent)

solver `async_solvers:flatagent_solve`, model `na`, 10 trajectories, 5 turns, elapsed 105.0 s, solver errors 0.


## 1. Accuracy vs turn (macro mean over trajectories; percentages)

all_field_acc = correct leaf verdicts / all scored leaves (repo public evaluator, strict exact match; open-text paraphrases count as wrong). structured_acc = same restricted to bool/number/choice/date/time leaves. fully_correct = every leaf correct.

### all-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 98.5 | 93.0 | 90.3 | 89.2 | 87.2 | 89.9 |
| oracle | 98.5 | 93.1 | 95.6 | 97.0 | 96.7 | 95.6 |

### structured-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.5 | 95.4 | 93.3 | 94.2 | 94.3 | 94.3 |
| oracle | 99.5 | 95.4 | 96.3 | 98.9 | 100.0 | 97.6 |

### fully-correct record rate (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 60.0 | 10.0 | 0.0 | 0.0 | 0.0 | 2.5 |
| oracle | 60.0 | 20.0 | 50.0 | 70.0 | 50.0 | 47.5 |

### all-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 98.5 | 93.0 | 89.0 | 88.7 | 86.3 | 89.2 |
| oracle | 98.5 | 93.1 | 94.2 | 93.9 | 94.0 | 93.8 |

### structured-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.5 | 95.4 | 90.3 | 92.6 | 92.9 | 92.8 |
| oracle | 99.5 | 95.4 | 92.5 | 95.0 | 97.1 | 95.0 |

### fully-correct record rate (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 60.0 | 10.0 | 0.0 | 0.0 | 0.0 | 2.5 |
| oracle | 60.0 | 20.0 | 10.0 | 10.0 | 20.0 | 15.0 |

### micro all-field accuracy, clean (sum correct / sum leaves, T1-T5)

| condition | correct/total | micro acc |
|---|---|---|
| incremental | 1673/1818 | 92.0 |
| oracle | 1758/1818 | 96.7 |

## 2. Condition gaps (clean; per-trajectory mean over T2-T5; paired bootstrap 95% CI over trajectories)

| comparison | metric | mean diff (pp) | 95% CI (pp) | n traj |
|---|---|---|---|---|
| incremental - oracle | all_field_acc | -5.7 | [-8.4, -3.4] | 10 |
| incremental - oracle | structured_acc | -3.3 | [-5.2, -1.7] | 10 |
| incremental - oracle | fully_correct | -45.0 | [-65.0, -25.0] | 10 |

## 3. Injected corruption (one structured field overwritten after T2; never mentioned again)

| trajectory | condition | field | injected | gold | system had it right at T2 | persisted T3/T4/T5 | persistence length | recovered at |
|---|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `time_of_accident` | "18:30" | "18:45" | False | 1/1/1 | 3 | never |
| cr_gen_01 | oracle | `time_of_accident` | "18:30" | "18:45" | False | 1/1/0 | 2 | never |
| cr_gen_02 | incremental | `lighting` | "Dark\u2013Lit" | "Dark\u2013Unlit" | True | 1/1/0 | 2 | 5 |
| cr_gen_02 | oracle | `lighting` | "Dark\u2013Lit" | "Dark\u2013Unlit" | True | 1/1/1 | 3 | never |
| cr_gen_03 | incremental | `road_surface_condition` | "Wet" | "Dry" | True | 0/0/0 | 0 | 3 |
| cr_gen_03 | oracle | `road_surface_condition` | "Wet" | "Dry" | True | 0/1/0 | 0 | 5 |
| cr_gen_04 | incremental | `lighting` | "Dark\u2013Lit" | "Dusk / Dawn" | True | 1/1/1 | 3 | never |
| cr_gen_04 | oracle | `lighting` | "Dark\u2013Lit" | "Dusk / Dawn" | True | 0/0/0 | 0 | 3 |
| pa_gen_01 | incremental | `pain_details[0].pain_severity` | "Mild" | "Moderate" | True | 1/1/1 | 3 | never |
| pa_gen_01 | oracle | `pain_details[0].pain_severity` | "Mild" | "Moderate" | True | 0/0/0 | 0 | 3 |
| pa_gen_02 | incremental | `allergies[0].allergy_severity` | "Severe" | "Moderate" | False | 1/1/1 | 3 | never |
| pa_gen_02 | oracle | `allergies[0].allergy_severity` | "Severe" | "Moderate" | False | 1/1/1 | 3 | never |
| pa_gen_03 | incremental | `upper_denture` | "No" | "Yes" | True | 1/1/1 | 3 | never |
| pa_gen_03 | oracle | `upper_denture` | "No" | "Yes" | True | 1/1/0 | 2 | 5 |
| pa_gen_04 | incremental | `ambulatory_aid_use` | "Has but does not use" | "Yes (uses)" | True | 1/1/1 | 3 | never |
| pa_gen_04 | oracle | `ambulatory_aid_use` | "Has but does not use" | "Yes (uses)" | True | 0/0/0 | 0 | never |
| pa_gen_05 | incremental | `pain_details[0].pain_severity` | "Moderate" | "Mild" | True | 1/1/1 | 3 | never |
| pa_gen_05 | oracle | `pain_details[0].pain_severity` | "Moderate" | "Mild" | True | 1/1/1 | 3 | never |
| pa_handmade_01 | incremental | `sputum_amount` | "Moderate" | "Small" | False | 1/0/0 | 1 | never |
| pa_handmade_01 | oracle | `sputum_amount` | "Moderate" | "Small" | False | 1/1/1 | 3 | never |

| condition | n | wrong value survived T3 | mean persistence length (0-3 turns) | silently recovered by T5 | never recovered |
|---|---|---|---|---|---|
| incremental | 10 | 9/10 | 2.40 | 2/10 | 8/10 |
| oracle | 10 | 6/10 | 1.60 | 4/10 | 6/10 |

rebuild: not applicable (no state channel; a corrupted record is discarded each turn by construction).

### accuracy cost of the injection (corrupt - clean, all_field_acc, mean over T3-T5, pp)

| condition | clean | corrupt | diff |
|---|---|---|---|
| incremental | 88.9 | 88.0 | -0.9 |
| oracle | 96.4 | 94.0 | -2.4 |

## 4. Collateral edits and natural (non-injected) error persistence, clean mode, T2-T5

collateral: leaves correct in the previous record (incremental/oracle: the prior handed in; rebuild: its own previous output) and unchanged in gold this turn, but wrong after the turn. natural persistence: structured leaves wrong in the system's own previous output, gold unchanged this turn -> still the same wrong value.

| condition | collateral edits / opportunities | of which non-empty gold | natural: opportunities | persisted | recovered | persist rate |
|---|---|---|---|---|---|---|
| incremental | 9/1182 (0.8%) | 2 | 29 | 28 | 1 | 96.6% |
| oracle | 20/1277 (1.6%) | 5 | 16 | 1 | 14 | 6.2% |

## 5. Per questionnaire (clean, mean all_field_acc over T1-T5, %)

| questionnaire | n traj | incremental | rebuild | oracle |
|---|---|---|---|---|
| crash_report | 4 | 85.9 | - | 92.9 |
| patient_admin | 6 | 95.5 | - | 98.3 |

## 6. Tokens and cost (this run, cache hits excluded)

| condition | mode | billed calls | input tok | output tok | reasoning tok | mean in/call | mean out/call |
|---|---|---|---|---|---|---|---|
| incremental | clean | 82 | 460205 | 7299 | 0 | 5612 | 89 |
| oracle | clean | 71 | 403074 | 5582 | 0 | 5677 | 78 |
| incremental | corrupt | 53 | 303578 | 4688 | 0 | 5727 | 88 |
| oracle | corrupt | 51 | 289866 | 5176 | 0 | 5683 | 101 |

Total billed: 1456723 input + 22745 output tokens -> ~$0.464 at assumed $0.3/M in, $1.2/M out.
Turns needing a Direct retry (invalid JSON/shape): 127; prior-state fallbacks: 0.
