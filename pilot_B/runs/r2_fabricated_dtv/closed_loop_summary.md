# Closed-loop pilot summary (r2_fabricated_dtv)

solver `async_solvers:dtv_solve`, model `na`, 7 trajectories, 5 turns, elapsed 45.3 s, solver errors 0.


## 1. Accuracy vs turn (macro mean over trajectories; percentages)

all_field_acc = correct leaf verdicts / all scored leaves (repo public evaluator, strict exact match; open-text paraphrases count as wrong). structured_acc = same restricted to bool/number/choice/date/time leaves. fully_correct = every leaf correct.

### all-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 97.7 | 94.6 | 92.3 | 90.5 | 89.6 | 91.8 |
| oracle | 97.7 | 96.4 | 94.6 | 94.7 | 98.6 | 96.1 |

### structured-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 98.2 | 96.0 | 93.8 | 93.4 | 93.5 | 94.1 |
| oracle | 98.2 | 97.7 | 96.9 | 98.4 | 99.4 | 98.1 |

### fully-correct record rate (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 42.9 | 14.3 | 14.3 | 14.3 | 0.0 | 10.7 |
| oracle | 42.9 | 42.9 | 42.9 | 42.9 | 57.1 | 46.4 |

### all-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 97.7 | 94.6 | 89.9 | 88.2 | 86.9 | 89.9 |
| oracle | 97.7 | 96.4 | 93.7 | 95.3 | 96.8 | 95.6 |

### structured-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 98.2 | 96.0 | 89.8 | 90.8 | 90.3 | 91.7 |
| oracle | 98.2 | 97.7 | 92.2 | 96.3 | 96.5 | 95.7 |

### fully-correct record rate (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 42.9 | 14.3 | 0.0 | 0.0 | 0.0 | 3.6 |
| oracle | 42.9 | 42.9 | 0.0 | 0.0 | 14.3 | 14.3 |

### micro all-field accuracy, clean (sum correct / sum leaves, T1-T5)

| condition | correct/total | micro acc |
|---|---|---|
| incremental | 1231/1311 | 93.9 |
| oracle | 1271/1311 | 96.9 |

## 2. Condition gaps (clean; per-trajectory mean over T2-T5; paired bootstrap 95% CI over trajectories)

| comparison | metric | mean diff (pp) | 95% CI (pp) | n traj |
|---|---|---|---|---|
| incremental - oracle | all_field_acc | -4.3 | [-7.2, -1.7] | 7 |
| incremental - oracle | structured_acc | -4.0 | [-6.2, -1.9] | 7 |
| incremental - oracle | fully_correct | -35.7 | [-53.6, -14.3] | 7 |

## 3. Injected corruption (one structured field overwritten after T2; never mentioned again)

| trajectory | condition | field | injected | gold | system had it right at T2 | persisted T3/T4/T5 | persistence length | recovered at |
|---|---|---|---|---|---|---|---|---|
| cr_gen_02 | incremental | `traffic_control` | "Stop Sign" | null | False | 1/0/0 | 1 | 4 |
| cr_gen_02 | oracle | `traffic_control` | "Stop Sign" | null | False | 1/0/0 | 1 | 4 |
| cr_gen_03 | incremental | `traffic_control` | "Stop Sign" | null | False | 0/0/0 | 0 | never |
| cr_gen_03 | oracle | `traffic_control` | "Stop Sign" | null | False | 1/0/0 | 1 | 4 |
| pa_gen_01 | incremental | `appetite_change` | "Yes" | null | False | 0/0/0 | 0 | 3 |
| pa_gen_01 | oracle | `appetite_change` | "Yes" | null | False | 1/1/1 | 3 | never |
| pa_gen_02 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | False | 1/1/1 | 3 | never |
| pa_gen_02 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | False | 1/1/1 | 3 | never |
| pa_gen_04 | incremental | `appetite_change` | "Yes" | null | False | 1/1/1 | 3 | never |
| pa_gen_04 | oracle | `appetite_change` | "Yes" | null | False | 1/1/1 | 3 | never |
| pa_gen_05 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | False | 1/1/1 | 3 | never |
| pa_gen_05 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | False | 1/1/1 | 3 | never |
| pa_handmade_01 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | False | 1/1/1 | 3 | never |
| pa_handmade_01 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | False | 1/1/1 | 3 | never |

| condition | n | wrong value survived T3 | mean persistence length (0-3 turns) | silently recovered by T5 | never recovered |
|---|---|---|---|---|---|
| incremental | 7 | 5/7 | 1.86 | 2/7 | 5/7 |
| oracle | 7 | 7/7 | 2.43 | 2/7 | 5/7 |

rebuild: not applicable (no state channel; a corrupted record is discarded each turn by construction).

### accuracy cost of the injection (corrupt - clean, all_field_acc, mean over T3-T5, pp)

| condition | clean | corrupt | diff |
|---|---|---|---|
| incremental | 90.8 | 88.4 | -2.5 |
| oracle | 96.0 | 95.3 | -0.7 |

## 4. Collateral edits and natural (non-injected) error persistence, clean mode, T2-T5

collateral: leaves correct in the previous record (incremental/oracle: the prior handed in; rebuild: its own previous output) and unchanged in gold this turn, but wrong after the turn. natural persistence: structured leaves wrong in the system's own previous output, gold unchanged this turn -> still the same wrong value.

| condition | collateral edits / opportunities | of which non-empty gold | natural: opportunities | persisted | recovered | persist rate |
|---|---|---|---|---|---|---|
| incremental | 9/883 (1.0%) | 0 | 22 | 20 | 2 | 90.9% |
| oracle | 15/934 (1.6%) | 0 | 9 | 0 | 9 | 0.0% |

## 5. Per questionnaire (clean, mean all_field_acc over T1-T5, %)

| questionnaire | n traj | incremental | rebuild | oracle |
|---|---|---|---|---|
| crash_report | 2 | 83.9 | - | 92.0 |
| patient_admin | 5 | 96.6 | - | 98.2 |

## 6. Tokens and cost (this run, cache hits excluded)

| condition | mode | billed calls | input tok | output tok | reasoning tok | mean in/call | mean out/call |
|---|---|---|---|---|---|---|---|
| incremental | corrupt | 57 | 338847 | 4830 | 0 | 5944 | 84 |
| oracle | corrupt | 48 | 288232 | 4420 | 0 | 6004 | 92 |

Total billed: 627079 input + 9250 output tokens -> ~$0.199 at assumed $0.3/M in, $1.2/M out.
Turns needing a Direct retry (invalid JSON/shape): 35; prior-state fallbacks: 0.
