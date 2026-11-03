# Closed-loop pilot summary (r2_ambiguous_direct)

solver `conformbench.systems.direct:solve`, model `deepseek-flash:thinking=disabled`, 10 trajectories, 5 turns, elapsed 80.9 s, solver errors 0.


## 1. Accuracy vs turn (macro mean over trajectories; percentages)

all_field_acc = correct leaf verdicts / all scored leaves (repo public evaluator, strict exact match; open-text paraphrases count as wrong). structured_acc = same restricted to bool/number/choice/date/time leaves. fully_correct = every leaf correct.

### all-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 98.4 | 91.8 | 87.3 | 89.4 | 87.8 | 89.1 |
| oracle | 98.4 | 92.8 | 93.4 | 95.6 | 95.2 | 94.3 |

### structured-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.1 | 94.4 | 89.5 | 94.7 | 95.4 | 93.5 |
| oracle | 99.1 | 95.4 | 95.2 | 99.5 | 99.2 | 97.3 |

### fully-correct record rate (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 60.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| oracle | 60.0 | 10.0 | 30.0 | 40.0 | 40.0 | 30.0 |

### all-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 98.4 | 91.8 | 88.7 | 88.2 | 86.7 | 88.8 |
| oracle | 98.4 | 92.8 | 92.7 | 93.4 | 94.4 | 93.3 |

### structured-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.1 | 94.4 | 92.1 | 93.7 | 94.5 | 93.7 |
| oracle | 99.1 | 95.4 | 91.9 | 95.4 | 97.3 | 95.0 |

### fully-correct record rate (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 60.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| oracle | 60.0 | 10.0 | 10.0 | 10.0 | 20.0 | 12.5 |

### micro all-field accuracy, clean (sum correct / sum leaves, T1-T5)

| condition | correct/total | micro acc |
|---|---|---|
| incremental | 1660/1818 | 91.3 |
| oracle | 1738/1818 | 95.6 |

## 2. Condition gaps (clean; per-trajectory mean over T2-T5; paired bootstrap 95% CI over trajectories)

| comparison | metric | mean diff (pp) | 95% CI (pp) | n traj |
|---|---|---|---|---|
| incremental - oracle | all_field_acc | -5.2 | [-7.3, -3.2] | 10 |
| incremental - oracle | structured_acc | -3.8 | [-6.1, -1.8] | 10 |
| incremental - oracle | fully_correct | -30.0 | [-55.0, -10.0] | 10 |

## 3. Injected corruption (one structured field overwritten after T2; never mentioned again)

| trajectory | condition | field | injected | gold | system had it right at T2 | persisted T3/T4/T5 | persistence length | recovered at |
|---|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `time_of_accident` | "18:30" | "18:45" | False | 0/0/0 | 0 | never |
| cr_gen_01 | oracle | `time_of_accident` | "18:30" | "18:45" | False | 1/1/1 | 3 | never |
| cr_gen_02 | incremental | `lighting` | "Dark\u2013Lit" | "Dark\u2013Unlit" | True | 0/0/0 | 0 | 3 |
| cr_gen_02 | oracle | `lighting` | "Dark\u2013Lit" | "Dark\u2013Unlit" | True | 1/0/0 | 1 | 4 |
| cr_gen_03 | incremental | `road_surface_condition` | "Wet" | "Dry" | True | 0/0/0 | 0 | 3 |
| cr_gen_03 | oracle | `road_surface_condition` | "Wet" | "Dry" | True | 0/0/0 | 0 | 3 |
| cr_gen_04 | incremental | `lighting` | "Dark\u2013Lit" | "Dusk / Dawn" | True | 0/0/0 | 0 | 3 |
| cr_gen_04 | oracle | `lighting` | "Dark\u2013Lit" | "Dusk / Dawn" | True | 1/0/0 | 1 | 4 |
| pa_gen_01 | incremental | `pain_details[0].pain_severity` | "Mild" | "Moderate" | True | 1/1/1 | 3 | never |
| pa_gen_01 | oracle | `pain_details[0].pain_severity` | "Mild" | "Moderate" | True | 1/1/1 | 3 | never |
| pa_gen_02 | incremental | `allergies[0].allergy_severity` | "Severe" | "Moderate" | False | 1/1/1 | 3 | never |
| pa_gen_02 | oracle | `allergies[0].allergy_severity` | "Severe" | "Moderate" | False | 1/1/0 | 2 | never |
| pa_gen_03 | incremental | `upper_denture` | "No" | "Yes" | True | 0/0/0 | 0 | 3 |
| pa_gen_03 | oracle | `upper_denture` | "No" | "Yes" | True | 0/0/0 | 0 | 3 |
| pa_gen_04 | incremental | `ambulatory_aid_use` | "Has but does not use" | "Yes (uses)" | False | 1/1/1 | 3 | never |
| pa_gen_04 | oracle | `ambulatory_aid_use` | "Has but does not use" | "Yes (uses)" | False | 1/1/1 | 3 | never |
| pa_gen_05 | incremental | `pain_details[0].pain_severity` | "Moderate" | "Mild" | False | 1/1/1 | 3 | never |
| pa_gen_05 | oracle | `pain_details[0].pain_severity` | "Moderate" | "Mild" | False | 1/1/1 | 3 | never |
| pa_handmade_01 | incremental | `sputum_amount` | "Moderate" | "Small" | False | 1/1/1 | 3 | never |
| pa_handmade_01 | oracle | `sputum_amount` | "Moderate" | "Small" | False | 1/1/1 | 3 | never |

| condition | n | wrong value survived T3 | mean persistence length (0-3 turns) | silently recovered by T5 | never recovered |
|---|---|---|---|---|---|
| incremental | 10 | 5/10 | 1.50 | 4/10 | 6/10 |
| oracle | 10 | 8/10 | 1.90 | 4/10 | 6/10 |

rebuild: not applicable (no state channel; a corrupted record is discarded each turn by construction).

### accuracy cost of the injection (corrupt - clean, all_field_acc, mean over T3-T5, pp)

| condition | clean | corrupt | diff |
|---|---|---|---|
| incremental | 88.2 | 87.9 | -0.3 |
| oracle | 94.7 | 93.5 | -1.2 |

## 4. Collateral edits and natural (non-injected) error persistence, clean mode, T2-T5

collateral: leaves correct in the previous record (incremental/oracle: the prior handed in; rebuild: its own previous output) and unchanged in gold this turn, but wrong after the turn. natural persistence: structured leaves wrong in the system's own previous output, gold unchanged this turn -> still the same wrong value.

| condition | collateral edits / opportunities | of which non-empty gold | natural: opportunities | persisted | recovered | persist rate |
|---|---|---|---|---|---|---|
| incremental | 13/1171 (1.1%) | 0 | 36 | 32 | 4 | 88.9% |
| oracle | 43/1277 (3.4%) | 9 | 17 | 3 | 14 | 17.6% |

## 5. Per questionnaire (clean, mean all_field_acc over T1-T5, %)

| questionnaire | n traj | incremental | rebuild | oracle |
|---|---|---|---|---|
| crash_report | 4 | 85.4 | - | 91.3 |
| patient_admin | 6 | 94.6 | - | 97.6 |

## 6. Tokens and cost (this run, cache hits excluded)

| condition | mode | billed calls | input tok | output tok | reasoning tok | mean in/call | mean out/call |
|---|---|---|---|---|---|---|---|
| incremental | clean | 42 | 214343 | 17702 | 0 | 5103 | 421 |
| oracle | clean | 34 | 176221 | 15281 | 0 | 5182 | 449 |
| incremental | corrupt | 23 | 117207 | 10185 | 0 | 5095 | 442 |
| oracle | corrupt | 21 | 107826 | 9390 | 0 | 5134 | 447 |

Total billed: 615597 input + 52558 output tokens -> ~$0.248 at assumed $0.3/M in, $1.2/M out.
Turns needing a Direct retry (invalid JSON/shape): 0; prior-state fallbacks: 0.
