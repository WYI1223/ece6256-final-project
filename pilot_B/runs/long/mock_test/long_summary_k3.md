# Long-dialogue regime summary (k3)

solver `mock_solvers:solve`, model `na`, 8 trajectories, elapsed 7.3 s, solver errors 0.


## Injected value (incremental, corrupt mode)

survived = still holds the injected value at the first post-injection turn; persistence = consecutive turns holding it; restored = equals the system's own pre-injection value (not gold).

| regime | n | survived first turn | mean persistence (max) | restored by T15 | first-restore turns | persisted to T15 | other final value |
|---|---|---|---|---|---|---|---|
| full | 8 | 3/8 | 3.75 (12) | 7/8 | [4, 4, 4, 4, 4, 13, 13] | 1/8 | 0/8 |
| w3 | 8 | 3/8 | 3.75 (12) | 7/8 | [4, 4, 4, 4, 4, 13, 13] | 1/8 | 0/8 |
| w0 | 8 | 3/8 | 3.75 (12) | 7/8 | [4, 4, 4, 4, 4, 13, 13] | 1/8 | 0/8 |

### Per trajectory (persist sequence from turn K+1; 1 = injected value held)

| regime | trajectory | field (set turn) | injected -> pre | persist seq | restore seq | first restored | final |
|---|---|---|---|---|---|---|---|
| full | cr_long_01 | date_of_accident (t1) | 2024-03-17 -> 2024-03-14 | 111111111000 | 000000000111 | 13 | restored |
| full | cr_long_02 | date_of_accident (t1) | 2024-02-06 -> 2024-02-03 | 111111111111 | 000000000000 | - | persisted |
| full | cr_long_03 | time_of_accident (t2) | 18:20 -> 16:20 | 000000000000 | 111111111111 | 4 | restored |
| full | cr_long_04 | date_of_accident (t1) | 2024-03-17 -> 2024-03-14 | 111111111000 | 000000000111 | 13 | restored |
| full | pa_long_01 | pain_details[0].pain_severity (t1) | High -> Moderate | 000000000000 | 111111111111 | 4 | restored |
| full | pa_long_02 | pain_details[0].pain_severity (t1) | Mild -> High | 000000000000 | 111111111111 | 4 | restored |
| full | pa_long_03 | pain_details[0].pain_severity (t2) | High -> Moderate | 000000000000 | 111111111111 | 4 | restored |
| full | pa_long_04 | pain_details[0].pain_severity (t2) | High -> Moderate | 000000000000 | 111111111111 | 4 | restored |
| w3 | cr_long_01 | date_of_accident (t1) | 2024-03-17 -> 2024-03-14 | 111111111000 | 000000000111 | 13 | restored |
| w3 | cr_long_02 | date_of_accident (t1) | 2024-02-06 -> 2024-02-03 | 111111111111 | 000000000000 | - | persisted |
| w3 | cr_long_03 | time_of_accident (t2) | 18:20 -> 16:20 | 000000000000 | 111111111111 | 4 | restored |
| w3 | cr_long_04 | date_of_accident (t1) | 2024-03-17 -> 2024-03-14 | 111111111000 | 000000000111 | 13 | restored |
| w3 | pa_long_01 | pain_details[0].pain_severity (t1) | High -> Moderate | 000000000000 | 111111111111 | 4 | restored |
| w3 | pa_long_02 | pain_details[0].pain_severity (t1) | Mild -> High | 000000000000 | 111111111111 | 4 | restored |
| w3 | pa_long_03 | pain_details[0].pain_severity (t2) | High -> Moderate | 000000000000 | 111111111111 | 4 | restored |
| w3 | pa_long_04 | pain_details[0].pain_severity (t2) | High -> Moderate | 000000000000 | 111111111111 | 4 | restored |
| w0 | cr_long_01 | date_of_accident (t1) | 2024-03-17 -> 2024-03-14 | 111111111000 | 000000000111 | 13 | restored |
| w0 | cr_long_02 | date_of_accident (t1) | 2024-02-06 -> 2024-02-03 | 111111111111 | 000000000000 | - | persisted |
| w0 | cr_long_03 | time_of_accident (t2) | 18:20 -> 16:20 | 000000000000 | 111111111111 | 4 | restored |
| w0 | cr_long_04 | date_of_accident (t1) | 2024-03-17 -> 2024-03-14 | 111111111000 | 000000000111 | 13 | restored |
| w0 | pa_long_01 | pain_details[0].pain_severity (t1) | High -> Moderate | 000000000000 | 111111111111 | 4 | restored |
| w0 | pa_long_02 | pain_details[0].pain_severity (t1) | Mild -> High | 000000000000 | 111111111111 | 4 | restored |
| w0 | pa_long_03 | pain_details[0].pain_severity (t2) | High -> Moderate | 000000000000 | 111111111111 | 4 | restored |
| w0 | pa_long_04 | pain_details[0].pain_severity (t2) | High -> Moderate | 000000000000 | 111111111111 | 4 | restored |

## Natural structured errors and clean accuracy (vs UNREVIEWED generator gold; secondary)

| regime | nat. carried | persisted | recovered | clean structured acc, mean T4-T15 | clean all-field acc, mean T4-T15 |
|---|---|---|---|---|---|
| full | 153 | 130 (85%) | 21 | 91.5 | 95.1 |
| w3 | 153 | 130 (85%) | 21 | 91.5 | 95.1 |
| w0 | 153 | 130 (85%) | 21 | 91.5 | 95.1 |

## Tokens and cost (this tag's run; cache hits excluded)

| regime | billed solver calls | input tok | output tok | summary calls | summary in | summary out | USD |
|---|---|---|---|---|---|---|---|
| full | 0 | 0 | 0 | 0 | 0 | 0 | 0.000 |
| w3 | 0 | 0 | 0 | 0 | 0 | 0 | 0.000 |
| w0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.000 |
| **total** | 0 | 0 | 0 | 0 | 0 | 0 | 0.000 |

All runs in this out-dir so far (solver_cache.jsonl + summaries.jsonl, 513 billed calls): 0 in / 0 out = $0.000.
