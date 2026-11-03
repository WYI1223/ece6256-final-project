# Closed-loop pilot summary (r2_fabricated_flatagent)

solver `async_solvers:flatagent_solve`, model `na`, 7 trajectories, 5 turns, elapsed 34.2 s, solver errors 0.


## 1. Accuracy vs turn (macro mean over trajectories; percentages)

all_field_acc = correct leaf verdicts / all scored leaves (repo public evaluator, strict exact match; open-text paraphrases count as wrong). structured_acc = same restricted to bool/number/choice/date/time leaves. fully_correct = every leaf correct.

### all-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.2 | 97.2 | 94.4 | 92.7 | 90.8 | 93.8 |
| oracle | 99.2 | 97.2 | 97.0 | 97.2 | 97.7 | 97.3 |

### structured-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 100.0 | 99.0 | 96.3 | 96.4 | 94.9 | 96.7 |
| oracle | 100.0 | 99.0 | 99.0 | 100.0 | 100.0 | 99.5 |

### fully-correct record rate (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 71.4 | 42.9 | 28.6 | 28.6 | 14.3 | 28.6 |
| oracle | 71.4 | 57.1 | 57.1 | 42.9 | 57.1 | 53.6 |

### all-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.2 | 97.2 | 91.5 | 91.6 | 90.1 | 92.6 |
| oracle | 99.2 | 97.2 | 93.8 | 95.2 | 95.8 | 95.5 |

### structured-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 100.0 | 99.0 | 91.1 | 93.2 | 92.3 | 93.9 |
| oracle | 100.0 | 99.0 | 92.5 | 94.8 | 95.8 | 95.5 |

### fully-correct record rate (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 71.4 | 42.9 | 0.0 | 0.0 | 0.0 | 10.7 |
| oracle | 71.4 | 57.1 | 0.0 | 0.0 | 14.3 | 17.9 |

### micro all-field accuracy, clean (sum correct / sum leaves, T1-T5)

| condition | correct/total | micro acc |
|---|---|---|
| incremental | 1251/1311 | 95.4 |
| oracle | 1285/1311 | 98.0 |

## 2. Condition gaps (clean; per-trajectory mean over T2-T5; paired bootstrap 95% CI over trajectories)

| comparison | metric | mean diff (pp) | 95% CI (pp) | n traj |
|---|---|---|---|---|
| incremental - oracle | all_field_acc | -3.5 | [-5.8, -1.3] | 7 |
| incremental - oracle | structured_acc | -2.8 | [-4.6, -1.2] | 7 |
| incremental - oracle | fully_correct | -25.0 | [-53.6, -3.6] | 7 |

## 3. Injected corruption (one structured field overwritten after T2; never mentioned again)

| trajectory | condition | field | injected | gold | system had it right at T2 | persisted T3/T4/T5 | persistence length | recovered at |
|---|---|---|---|---|---|---|---|---|
| cr_gen_02 | incremental | `traffic_control` | "Stop Sign" | null | False | 1/0/0 | 1 | 4 |
| cr_gen_02 | oracle | `traffic_control` | "Stop Sign" | null | False | 1/0/0 | 1 | never |
| cr_gen_03 | incremental | `traffic_control` | "Stop Sign" | null | False | 1/1/1 | 3 | never |
| cr_gen_03 | oracle | `traffic_control` | "Stop Sign" | null | False | 1/1/1 | 3 | never |
| pa_gen_01 | incremental | `appetite_change` | "Yes" | null | False | 1/1/1 | 3 | never |
| pa_gen_01 | oracle | `appetite_change` | "Yes" | null | False | 1/1/1 | 3 | never |
| pa_gen_02 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | False | 1/1/0 | 2 | 5 |
| pa_gen_02 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | False | 1/1/1 | 3 | never |
| pa_gen_04 | incremental | `appetite_change` | "Yes" | null | False | 1/1/1 | 3 | never |
| pa_gen_04 | oracle | `appetite_change` | "Yes" | null | False | 1/1/1 | 3 | never |
| pa_gen_05 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | False | 1/1/1 | 3 | never |
| pa_gen_05 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | False | 0/0/0 | 0 | 3 |
| pa_handmade_01 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | False | 1/1/1 | 3 | never |
| pa_handmade_01 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | False | 1/1/1 | 3 | never |

| condition | n | wrong value survived T3 | mean persistence length (0-3 turns) | silently recovered by T5 | never recovered |
|---|---|---|---|---|---|
| incremental | 7 | 7/7 | 2.57 | 2/7 | 5/7 |
| oracle | 7 | 6/7 | 2.29 | 1/7 | 6/7 |

rebuild: not applicable (no state channel; a corrupted record is discarded each turn by construction).

### accuracy cost of the injection (corrupt - clean, all_field_acc, mean over T3-T5, pp)

| condition | clean | corrupt | diff |
|---|---|---|---|
| incremental | 92.6 | 91.0 | -1.6 |
| oracle | 97.3 | 94.9 | -2.4 |

## 4. Collateral edits and natural (non-injected) error persistence, clean mode, T2-T5

collateral: leaves correct in the previous record (incremental/oracle: the prior handed in; rebuild: its own previous output) and unchanged in gold this turn, but wrong after the turn. natural persistence: structured leaves wrong in the system's own previous output, gold unchanged this turn -> still the same wrong value.

| condition | collateral edits / opportunities | of which non-empty gold | natural: opportunities | persisted | recovered | persist rate |
|---|---|---|---|---|---|---|
| incremental | 3/896 (0.3%) | 0 | 11 | 11 | 0 | 100.0% |
| oracle | 9/934 (1.0%) | 0 | 2 | 0 | 2 | 0.0% |

## 5. Per questionnaire (clean, mean all_field_acc over T1-T5, %)

| questionnaire | n traj | incremental | rebuild | oracle |
|---|---|---|---|---|
| crash_report | 2 | 88.4 | - | 94.5 |
| patient_admin | 5 | 97.5 | - | 98.9 |

## 6. Tokens and cost (this run, cache hits excluded)

| condition | mode | billed calls | input tok | output tok | reasoning tok | mean in/call | mean out/call |
|---|---|---|---|---|---|---|---|
| incremental | corrupt | 42 | 242409 | 3435 | 0 | 5771 | 81 |
| oracle | corrupt | 30 | 170967 | 2623 | 0 | 5698 | 87 |

Total billed: 413376 input + 6058 output tokens -> ~$0.131 at assumed $0.3/M in, $1.2/M out.
Turns needing a Direct retry (invalid JSON/shape): 36; prior-state fallbacks: 0.
