# Closed-loop pilot summary (mock_test)

solver `mock_solvers:solve`, model `na`, 1 trajectories, 5 turns, elapsed 0.3 s, solver errors 0.


## 1. Accuracy vs turn (macro mean over trajectories; percentages)

all_field_acc = correct leaf verdicts / all scored leaves (repo public evaluator, strict exact match; open-text paraphrases count as wrong). structured_acc = same restricted to bool/number/choice/date/time leaves. fully_correct = every leaf correct.

### all-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 97.3 | 92.7 | 93.3 | 93.3 | 93.3 | 93.2 |
| rebuild | 97.3 | 92.7 | 82.2 | 82.2 | 77.8 | 83.7 |
| oracle | 97.3 | 100.0 | 100.0 | 97.8 | 100.0 | 99.4 |

### structured-field accuracy (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 95.2 | 86.4 | 87.0 | 87.0 | 87.0 | 86.8 |
| rebuild | 95.2 | 90.9 | 69.6 | 69.6 | 60.9 | 72.7 |
| oracle | 95.2 | 100.0 | 100.0 | 95.7 | 100.0 | 98.9 |

### fully-correct record rate (clean)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| rebuild | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| oracle | 0.0 | 100.0 | 100.0 | 0.0 | 100.0 | 75.0 |

### all-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 97.3 | 92.7 | 95.6 | 95.6 | 95.6 | 94.8 |
| oracle | 97.3 | 100.0 | 100.0 | 97.8 | 100.0 | 99.4 |

### structured-field accuracy (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 95.2 | 86.4 | 91.3 | 91.3 | 91.3 | 90.1 |
| oracle | 95.2 | 100.0 | 100.0 | 95.7 | 100.0 | 98.9 |

### fully-correct record rate (corrupt)

| condition | T1 | T2 | T3 | T4 | T5 | mean T2-T5 |
|---|---|---|---|---|---|---|
| incremental | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| oracle | 0.0 | 100.0 | 100.0 | 0.0 | 100.0 | 75.0 |

### micro all-field accuracy, clean (sum correct / sum leaves, T1-T5)

| condition | correct/total | micro acc |
|---|---|---|
| incremental | 200/213 | 93.9 |
| rebuild | 183/213 | 85.9 |
| oracle | 211/213 | 99.1 |

## 2. Condition gaps (clean; per-trajectory mean over T2-T5; paired bootstrap 95% CI over trajectories)

| comparison | metric | mean diff (pp) | 95% CI (pp) | n traj |
|---|---|---|---|---|
| incremental - oracle | all_field_acc | -6.3 | [-6.3, -6.3] | 1 |
| rebuild - oracle | all_field_acc | -15.7 | [-15.7, -15.7] | 1 |
| incremental - rebuild | all_field_acc | +9.4 | [+9.4, +9.4] | 1 |
| incremental - oracle | structured_acc | -12.1 | [-12.1, -12.1] | 1 |
| rebuild - oracle | structured_acc | -26.2 | [-26.2, -26.2] | 1 |
| incremental - rebuild | structured_acc | +14.1 | [+14.1, +14.1] | 1 |
| incremental - oracle | fully_correct | -75.0 | [-75.0, -75.0] | 1 |
| rebuild - oracle | fully_correct | -75.0 | [-75.0, -75.0] | 1 |
| incremental - rebuild | fully_correct | +0.0 | [+0.0, +0.0] | 1 |

## 3. Injected corruption (one structured field overwritten after T2; never mentioned again)

| trajectory | condition | field | injected | gold | system had it right at T2 | persisted T3/T4/T5 | persistence length | recovered at |
|---|---|---|---|---|---|---|---|---|
| pa_handmade_01 | incremental | `current_medications[0].route` | "Inhaled" | "Oral" | True | 0/0/0 | 0 | 3 |
| pa_handmade_01 | oracle | `current_medications[0].route` | "Inhaled" | "Oral" | True | 0/0/0 | 0 | 3 |

| condition | n | wrong value survived T3 | mean persistence length (0-3 turns) | silently recovered by T5 | never recovered |
|---|---|---|---|---|---|
| incremental | 1 | 0/1 | 0.00 | 1/1 | 0/1 |
| oracle | 1 | 0/1 | 0.00 | 1/1 | 0/1 |

rebuild: not applicable (no state channel; a corrupted record is discarded each turn by construction).

### accuracy cost of the injection (corrupt - clean, all_field_acc, mean over T3-T5, pp)

| condition | clean | corrupt | diff |
|---|---|---|---|
| incremental | 93.3 | 95.6 | +2.2 |
| oracle | 99.3 | 99.3 | +0.0 |

## 4. Collateral edits and natural (non-injected) error persistence, clean mode, T2-T5

collateral: leaves correct in the previous record (incremental/oracle: the prior handed in; rebuild: its own previous output) and unchanged in gold this turn, but wrong after the turn. natural persistence: structured leaves wrong in the system's own previous output, gold unchanged this turn -> still the same wrong value.

| condition | collateral edits / opportunities | of which non-empty gold | natural: opportunities | persisted | recovered | persist rate |
|---|---|---|---|---|---|---|
| incremental | 2/147 (1.4%) | 1 | 9 | 9 | 0 | 100.0% |
| rebuild | 10/136 (7.4%) | 9 | 17 | 15 | 2 | 88.2% |
| oracle | 1/156 (0.6%) | 1 | 2 | 0 | 2 | 0.0% |

## 5. Per questionnaire (clean, mean all_field_acc over T1-T5, %)

| questionnaire | n traj | incremental | rebuild | oracle |
|---|---|---|---|---|
| patient_admin | 1 | 94.0 | 86.4 | 99.0 |

## 6. Tokens and cost (this run, cache hits excluded)

| condition | mode | billed calls | input tok | output tok | reasoning tok | mean in/call | mean out/call |
|---|---|---|---|---|---|---|---|
| incremental | clean | 0 | 0 | 0 | 0 | 0 | 0 |
| rebuild | clean | 0 | 0 | 0 | 0 | 0 | 0 |
| oracle | clean | 0 | 0 | 0 | 0 | 0 | 0 |
| incremental | corrupt | 0 | 0 | 0 | 0 | 0 | 0 |
| oracle | corrupt | 0 | 0 | 0 | 0 | 0 | 0 |

Total billed: 0 input + 0 output tokens -> ~$0.000 at assumed $0.3/M in, $1.2/M out.
Turns needing a Direct retry (invalid JSON/shape): 0; prior-state fallbacks: 0.
