# Long-dialogue regime summary (k6)

solver `conformbench.systems.direct:solve`, model `deepseek-flash:thinking=disabled`, 8 trajectories, elapsed 52.4 s, solver errors 0.


## Injected value (incremental, corrupt mode)

survived = still holds the injected value at the first post-injection turn; persistence = consecutive turns holding it; restored = equals the system's own pre-injection value (not gold).

| regime | n | survived first turn | mean persistence (max) | restored by T15 | first-restore turns | persisted to T15 | other final value |
|---|---|---|---|---|---|---|---|
| full | 8 | 1/8 | 0.12 (9) | 7/8 | [7, 7, 7, 7, 7, 7, 7] | 0/8 | 1/8 |
| w3 | 8 | 8/8 | 9.00 (9) | 0/8 | [] | 8/8 | 0/8 |
| w3+summary | 8 | 1/8 | 1.00 (9) | 7/8 | [7, 7, 7, 7, 7, 7, 7] | 0/8 | 1/8 |

### Per trajectory (persist sequence from turn K+1; 1 = injected value held)

| regime | trajectory | field (set turn) | injected -> pre | persist seq | restore seq | first restored | final |
|---|---|---|---|---|---|---|---|
| full | cr_long_01 | date_of_accident (t1) | 2024-03-17 -> 2024-03-14 | 000000000 | 111111111 | 7 | restored |
| full | cr_long_02 | date_of_accident (t1) | 2024-02-06 -> 2024-02-03 | 000000000 | 111111111 | 7 | restored |
| full | cr_long_03 | date_of_accident (t1) | 2024-06-06 -> 2024-06-03 | 000000000 | 111111111 | 7 | restored |
| full | cr_long_04 | date_of_accident (t1) | 2024-03-17 -> 2024-03-14 | 000000000 | 111111111 | 7 | restored |
| full | pa_long_01 | pain_details[0].pain_severity (t1) | High -> Moderate | 000000000 | 111111111 | 7 | restored |
| full | pa_long_02 | pain_details[0].pain_severity (t1) | Mild -> High | 100000000 | 000000000 | - | other:"Unknown" |
| full | pa_long_03 | pain_details[0].pain_severity (t2) | High -> Moderate | 000000000 | 111111111 | 7 | restored |
| full | pa_long_04 | pain_details[0].pain_severity (t2) | High -> Moderate | 000000000 | 111111111 | 7 | restored |
| w3 | cr_long_01 | date_of_accident (t1) | 2024-03-17 -> 2024-03-14 | 111111111 | 000000000 | - | persisted |
| w3 | cr_long_02 | date_of_accident (t1) | 2024-02-06 -> 2024-02-03 | 111111111 | 000000000 | - | persisted |
| w3 | cr_long_03 | date_of_accident (t1) | 2024-06-06 -> 2024-06-03 | 111111111 | 000000000 | - | persisted |
| w3 | cr_long_04 | date_of_accident (t1) | 2024-03-17 -> 2024-03-14 | 111111111 | 000000000 | - | persisted |
| w3 | pa_long_01 | pain_details[0].pain_severity (t1) | High -> Moderate | 111111111 | 000000000 | - | persisted |
| w3 | pa_long_02 | pain_details[0].pain_severity (t1) | Mild -> High | 111111111 | 000000000 | - | persisted |
| w3 | pa_long_03 | pain_details[0].pain_severity (t2) | High -> Moderate | 111111111 | 000000000 | - | persisted |
| w3 | pa_long_04 | pain_details[0].pain_severity (t2) | High -> Moderate | 111111111 | 000000000 | - | persisted |
| w3+summary | cr_long_01 | date_of_accident (t1) | 2024-03-17 -> 2024-03-14 | 000000000 | 111111111 | 7 | restored |
| w3+summary | cr_long_02 | date_of_accident (t1) | 2024-02-06 -> 2024-02-03 | 000000000 | 111111111 | 7 | restored |
| w3+summary | cr_long_03 | date_of_accident (t1) | 2024-06-06 -> 2024-06-03 | 000000000 | 111111111 | 7 | restored |
| w3+summary | cr_long_04 | date_of_accident (t1) | 2024-03-17 -> 2024-03-14 | 000000000 | 111111111 | 7 | restored |
| w3+summary | pa_long_01 | pain_details[0].pain_severity (t1) | High -> Moderate | 000000000 | 111111111 | 7 | restored |
| w3+summary | pa_long_02 | pain_details[0].pain_severity (t1) | Mild -> High | 111111110 | 000000000 | - | other:"Unknown" |
| w3+summary | pa_long_03 | pain_details[0].pain_severity (t2) | High -> Moderate | 000000000 | 111111111 | 7 | restored |
| w3+summary | pa_long_04 | pain_details[0].pain_severity (t2) | High -> Moderate | 000000000 | 111111111 | 7 | restored |

## Natural structured errors and clean accuracy (vs UNREVIEWED generator gold; secondary)

| regime | nat. carried | persisted | recovered | clean structured acc, mean T4-T15 | clean all-field acc, mean T4-T15 |
|---|---|---|---|---|---|
| full | 25 | 25 (100%) | 0 | 98.3 | 90.5 |
| w3 | 25 | 25 (100%) | 0 | 98.4 | 90.5 |
| w3+summary | 25 | 25 (100%) | 0 | 98.2 | 91.0 |

## Summary fidelity (w3+summary): does the summary state the corrupted field's TRUE value?

Only summaries that cover the turn that set the fact are counted (the fact is out of the window). Auto label = bullet line containing a surface form of the gold value (and the row anchor for repeat rows); every label is listed in summary_fidelity_<tag>.json with its matched line for hand checking.

| trajectory | field | anchor | summaries covering fact | mention true value (auto) | used at turns |
|---|---|---|---|---|---|
| cr_long_01 | date_of_accident | - | 11 | 11 | 5-15 |
| cr_long_02 | date_of_accident | - | 11 | 11 | 5-15 |
| cr_long_03 | date_of_accident | - | 11 | 11 | 5-15 |
| cr_long_04 | date_of_accident | - | 11 | 11 | 5-15 |
| pa_long_01 | pain_details[0].pain_severity | knee | 11 | 10 | 5-15 |
| pa_long_02 | pain_details[0].pain_severity | back | 11 | 11 | 5-15 |
| pa_long_03 | pain_details[0].pain_severity | shoulder | 10 | 10 | 6-15 |
| pa_long_04 | pain_details[0].pain_severity | knee | 10 | 10 | 6-15 |

Overall: 85/86 summaries (99%) mention the true value.


## Tokens and cost (this tag's run; cache hits excluded)

| regime | billed solver calls | input tok | output tok | summary calls | summary in | summary out | USD |
|---|---|---|---|---|---|---|---|
| full | 9 | 45,332 | 3,291 | 0 | 0 | 0 | 0.018 |
| w3 | 72 | 353,855 | 30,739 | 0 | 0 | 0 | 0.143 |
| w3+summary | 16 | 85,361 | 6,952 | 0 | 0 | 0 | 0.034 |
| **total** | 97 | 484,548 | 40,982 | 0 | 0 | 0 | 0.195 |

All runs in this out-dir so far (solver_cache.jsonl + summaries.jsonl, 752 billed calls): 3,365,220 in / 279,949 out = $1.346.

Trajectory generation: 23 calls, 43,769 in / 35,867 out = $0.056.
