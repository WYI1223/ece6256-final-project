# Closed-loop pilot summary (r2_fabricated_direct)

solver `conformbench.systems.direct:solve`, model `deepseek-flash:thinking=disabled`, 7 trajectories, 5 turns, elapsed 22.5 s, solver errors 0.


## 1. Accuracy vs turn (macro mean over trajectories; percentages)

all_field_acc = correct leaf verdicts / all scored leaves (repo public evaluator, strict exact match; open-text paraphrases count as wrong). structured_acc = same restricted to bool/number/choice/date/time leaves. fully_correct = every leaf correct.

### all-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.6 | 95.5 | 92.2 | 91.6 | 91.0 | 92.5 |
| oracle | 99.6 | 95.5 | 95.4 | 95.9 | 96.9 | 95.9 |

### structured-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 100.0 | 99.0 | 95.1 | 96.1 | 97.1 | 96.8 |
| oracle | 100.0 | 99.0 | 96.9 | 99.0 | 99.4 | 98.6 |

### fully-correct record rate (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 85.7 | 28.6 | 28.6 | 28.6 | 14.3 | 25.0 |
| oracle | 85.7 | 28.6 | 28.6 | 42.9 | 28.6 | 32.1 |

### all-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 99.6 | 95.5 | 91.8 | 90.0 | 90.8 | 92.0 |
| oracle | 99.6 | 95.5 | 92.4 | 93.3 | 95.4 | 94.1 |

### structured-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 100.0 | 99.0 | 94.9 | 94.9 | 96.7 | 96.4 |
| oracle | 100.0 | 99.0 | 92.9 | 96.7 | 97.6 | 96.6 |

### fully-correct record rate (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 85.7 | 28.6 | 14.3 | 14.3 | 0.0 | 14.3 |
| oracle | 85.7 | 28.6 | 28.6 | 42.9 | 28.6 | 32.1 |

### micro all-field accuracy, clean (sum correct / sum leaves, T1-T5)

| condition | correct/total | micro acc |
|---|---|---|
| incremental | 1244/1311 | 94.9 |
| oracle | 1274/1311 | 97.2 |

## 2. Condition gaps (clean; per-trajectory mean over T2-T5; paired bootstrap 95% CI over trajectories)

| comparison | metric | mean diff (pp) | 95% CI (pp) | n traj |
|---|---|---|---|---|
| incremental - oracle | all_field_acc | -3.4 | [-6.6, -0.7] | 7 |
| incremental - oracle | structured_acc | -1.8 | [-3.6, -0.2] | 7 |
| incremental - oracle | fully_correct | -7.1 | [-21.4, +0.0] | 7 |

## 3. Injected corruption (one structured field overwritten after T2; never mentioned again)

| trajectory | condition | field | injected | gold | system had it right at T2 | persisted T3/T4/T5 | persistence length | recovered at |
|---|---|---|---|---|---|---|---|---|
| cr_gen_02 | incremental | `traffic_control` | "Stop Sign" | null | False | 1/0/0 | 1 | 4 |
| cr_gen_02 | oracle | `traffic_control` | "Stop Sign" | null | False | 0/0/0 | 0 | never |
| cr_gen_03 | incremental | `traffic_control` | "Stop Sign" | null | False | 0/0/0 | 0 | 3 |
| cr_gen_03 | oracle | `traffic_control` | "Stop Sign" | null | False | 0/0/0 | 0 | never |
| pa_gen_01 | incremental | `appetite_change` | "Yes" | null | False | 1/0/0 | 1 | 4 |
| pa_gen_01 | oracle | `appetite_change` | "Yes" | null | False | 0/0/0 | 0 | 3 |
| pa_gen_02 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | False | 0/0/0 | 0 | 3 |
| pa_gen_02 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | False | 0/0/0 | 0 | 3 |
| pa_gen_04 | incremental | `appetite_change` | "Yes" | null | False | 0/0/0 | 0 | 3 |
| pa_gen_04 | oracle | `appetite_change` | "Yes" | null | False | 0/0/0 | 0 | 3 |
| pa_gen_05 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | False | 1/1/1 | 3 | never |
| pa_gen_05 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | False | 1/1/0 | 2 | 5 |
| pa_handmade_01 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | False | 0/0/0 | 0 | 3 |
| pa_handmade_01 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | False | 0/0/0 | 0 | 3 |

| condition | n | wrong value survived T3 | mean persistence length (0-3 turns) | silently recovered by T5 | never recovered |
|---|---|---|---|---|---|
| incremental | 7 | 3/7 | 0.71 | 6/7 | 1/7 |
| oracle | 7 | 1/7 | 0.29 | 5/7 | 2/7 |

rebuild: not applicable (no state channel; a corrupted record is discarded each turn by construction).

### accuracy cost of the injection (corrupt - clean, all_field_acc, mean over T3-T5, pp)

| condition | clean | corrupt | diff |
|---|---|---|---|
| incremental | 91.6 | 90.9 | -0.7 |
| oracle | 96.1 | 93.7 | -2.4 |

## 4. Collateral edits and natural (non-injected) error persistence, clean mode, T2-T5

collateral: leaves correct in the previous record (incremental/oracle: the prior handed in; rebuild: its own previous output) and unchanged in gold this turn, but wrong after the turn. natural persistence: structured leaves wrong in the system's own previous output, gold unchanged this turn -> still the same wrong value.

| condition | collateral edits / opportunities | of which non-empty gold | natural: opportunities | persisted | recovered | persist rate |
|---|---|---|---|---|---|---|
| incremental | 9/891 (1.0%) | 0 | 10 | 10 | 0 | 100.0% |
| oracle | 19/934 (2.0%) | 0 | 4 | 0 | 4 | 0.0% |

## 5. Per questionnaire (clean, mean all_field_acc over T1-T5, %)

| questionnaire | n traj | incremental | rebuild | oracle |
|---|---|---|---|---|
| crash_report | 2 | 84.7 | - | 92.3 |
| patient_admin | 5 | 97.7 | - | 98.4 |

## 6. Tokens and cost (this run, cache hits excluded)

| condition | mode | billed calls | input tok | output tok | reasoning tok | mean in/call | mean out/call |
|---|---|---|---|---|---|---|---|
| incremental | corrupt | 16 | 82595 | 7121 | 0 | 5162 | 445 |
| oracle | corrupt | 11 | 54077 | 4616 | 0 | 4916 | 419 |

Total billed: 136672 input + 11737 output tokens -> ~$0.055 at assumed $0.3/M in, $1.2/M out.
Turns needing a Direct retry (invalid JSON/shape): 0; prior-state fallbacks: 0.
