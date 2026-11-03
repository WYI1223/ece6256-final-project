
## closed_loop

solver `conformbench.systems.direct:solve` model `deepseek-flash:thinking=disabled` trajectories 10 solver_errors 0 billed in/out 713476/60205

### 1. Clean accuracy by turn (macro over trajectories; failed-call rows excluded)

| condition | metric | T1 | T2 | T3 | T4 | T5 | mean T2+ | excluded rows |
|---|---|---|---|---|---|---|---|---|
| incremental | all_field_acc | 99.2 | 93.7 | 91.1 | 91.4 | 89.8 | 91.5 | 0 |
| incremental | structured_acc | 99.5 | 97.1 | 93.8 | 95.8 | 96.9 | 95.9 | 0 |
| rebuild | all_field_acc | 99.2 | 94.0 | 91.2 | 90.0 | 89.2 | 91.1 | 0 |
| rebuild | structured_acc | 99.5 | 96.1 | 93.8 | 94.5 | 95.4 | 94.9 | 0 |
| oracle | all_field_acc | 99.2 | 94.1 | 95.7 | 95.7 | 95.9 | 95.4 | 0 |
| oracle | structured_acc | 99.5 | 97.5 | 97.3 | 98.8 | 99.6 | 98.3 | 0 |

### 2. Injected corruption per trajectory (incremental / oracle)

| trajectory | condition | field | injected | gold | persisted by turn | recovered at | valid |
|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `date_of_accident` | "2024-03-17" | "2024-03-14" | 0/0/0 | 3 | yes |
| cr_gen_01 | oracle | `date_of_accident` | "2024-03-17" | "2024-03-14" | 0/0/0 | 3 | yes |
| cr_gen_02 | incremental | `lighting` | "Daylight" | null | 0/0/0 | 3 | yes |
| cr_gen_02 | oracle | `lighting` | "Daylight" | null | 0/0/0 | 3 | yes |
| cr_gen_03 | incremental | `lighting` | "Dusk / Dawn" | null | 1/0/0 | 4 | yes |
| cr_gen_03 | oracle | `lighting` | "Dusk / Dawn" | null | 1/0/0 | 4 | yes |
| cr_gen_04 | incremental | `lighting` | "Dark\u2013Lit" | null | 0/0/0 | 3 | yes |
| cr_gen_04 | oracle | `lighting` | "Dark\u2013Lit" | null | 0/0/0 | 3 | yes |
| pa_gen_01 | incremental | `pain_details[0].pain_severity` | "High" | "Moderate" | 0/0/0 | 3 | yes |
| pa_gen_01 | oracle | `pain_details[0].pain_severity` | "High" | "Moderate" | 0/0/0 | 3 | yes |
| pa_gen_02 | incremental | `allergies[0].allergy_severity` | "Severe" | null | 0/0/0 | 3 | yes |
| pa_gen_02 | oracle | `allergies[0].allergy_severity` | "Severe" | null | 0/0/0 | 3 | yes |
| pa_gen_03 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | 0/0/0 | 3 | yes |
| pa_gen_03 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | 0/0/0 | 3 | yes |
| pa_gen_04 | incremental | `ambulatory_aid_use` | "Has but does not use" | null | 0/0/0 | 3 | yes |
| pa_gen_04 | oracle | `ambulatory_aid_use` | "Has but does not use" | null | 0/0/0 | 3 | yes |
| pa_gen_05 | incremental | `pain_details[0].pain_severity` | "Moderate" | "Mild" | 0/0/0 | 3 | yes |
| pa_gen_05 | oracle | `pain_details[0].pain_severity` | "Moderate" | "Mild" | 0/0/0 | 3 | yes |
| pa_handmade_01 | incremental | `current_medications[0].route` | "Inhaled" | null | 0/0/0 | 3 | yes |
| pa_handmade_01 | oracle | `current_medications[0].route` | "Inhaled" | null | 0/0/0 | 3 | yes |

| condition | valid trajectories | survived first post-injection turn | silently recovered | never recovered |
|---|---|---|---|---|
| incremental | 10 | 1/10 | 10/10 | 0/10 |
| oracle | 10 | 1/10 | 10/10 | 0/10 |

### 3. Natural structured errors: inherited vs re-derived (clean, turns 2+)

- incremental wrong structured leaf-turns (T2+): **30**
- inherited from its own previous output (same wrong value): 19 (63%)
- rebuild also wrong on the same leaf-turn: 28 (93%), with the same wrong value: 25
- inherited AND rebuild also wrong (error is systematic, state channel not needed): 18
- inherited but rebuild gets it right (error survives ONLY through the carried state): **1** (3% of incremental's errors)

## r2_direct_v4pro

solver `conformbench.systems.direct:solve` model `deepseek-v4-pro:thinking=disabled` trajectories 10 solver_errors 0 billed in/out 714144/59982

### 1. Clean accuracy by turn (macro over trajectories; failed-call rows excluded)

| condition | metric | T1 | T2 | T3 | T4 | T5 | mean T2+ | excluded rows |
|---|---|---|---|---|---|---|---|---|
| incremental | all_field_acc | 99.2 | 94.2 | 92.4 | 92.8 | 90.9 | 92.6 | 0 |
| incremental | structured_acc | 100.0 | 96.9 | 95.6 | 97.0 | 97.1 | 96.7 | 0 |
| rebuild | all_field_acc | 99.2 | 94.6 | 93.3 | 92.2 | 88.8 | 92.2 | 0 |
| rebuild | structured_acc | 100.0 | 97.7 | 96.9 | 96.5 | 97.5 | 97.2 | 0 |
| oracle | all_field_acc | 99.2 | 94.9 | 95.7 | 97.0 | 96.5 | 96.0 | 0 |
| oracle | structured_acc | 100.0 | 96.9 | 96.1 | 100.0 | 100.0 | 98.3 | 0 |

### 2. Injected corruption per trajectory (incremental / oracle)

| trajectory | condition | field | injected | gold | persisted by turn | recovered at | valid |
|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `date_of_accident` | "2024-03-17" | "2024-03-14" | 0/0/0 | 3 | yes |
| cr_gen_01 | oracle | `date_of_accident` | "2024-03-17" | "2024-03-14" | 0/0/0 | 3 | yes |
| cr_gen_02 | incremental | `lighting` | "Daylight" | null | 0/0/0 | 3 | yes |
| cr_gen_02 | oracle | `lighting` | "Daylight" | null | 0/0/0 | 3 | yes |
| cr_gen_03 | incremental | `lighting` | "Dusk / Dawn" | null | 1/0/0 | - | yes |
| cr_gen_03 | oracle | `lighting` | "Dusk / Dawn" | null | 1/1/1 | never | yes |
| cr_gen_04 | incremental | `lighting` | "Dark\u2013Lit" | null | 0/0/0 | 3 | yes |
| cr_gen_04 | oracle | `lighting` | "Dark\u2013Lit" | null | 0/0/0 | 3 | yes |
| pa_gen_01 | incremental | `pain_details[0].pain_severity` | "High" | "Moderate" | 0/0/0 | 3 | yes |
| pa_gen_01 | oracle | `pain_details[0].pain_severity` | "High" | "Moderate" | 0/0/0 | 3 | yes |
| pa_gen_02 | incremental | `allergies[0].allergy_severity` | "Severe" | null | 0/0/0 | 3 | yes |
| pa_gen_02 | oracle | `allergies[0].allergy_severity` | "Severe" | null | 0/0/0 | 3 | yes |
| pa_gen_03 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | 0/0/0 | 3 | yes |
| pa_gen_03 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | 0/0/0 | 3 | yes |
| pa_gen_04 | incremental | `ambulatory_aid_use` | "Has but does not use" | null | 1/0/0 | 4 | yes |
| pa_gen_04 | oracle | `ambulatory_aid_use` | "Has but does not use" | null | 1/0/0 | 4 | yes |
| pa_gen_05 | incremental | `pain_details[0].pain_severity` | "Moderate" | "Mild" | 0/0/0 | 3 | yes |
| pa_gen_05 | oracle | `pain_details[0].pain_severity` | "Moderate" | "Mild" | 0/0/0 | 3 | yes |
| pa_handmade_01 | incremental | `current_medications[0].route` | "Inhaled" | null | 0/0/0 | 3 | yes |
| pa_handmade_01 | oracle | `current_medications[0].route` | "Inhaled" | null | 0/0/0 | 3 | yes |

| condition | valid trajectories | survived first post-injection turn | silently recovered | never recovered |
|---|---|---|---|---|
| incremental | 10 | 2/10 | 9/10 | 0/10 |
| oracle | 10 | 2/10 | 9/10 | 1/10 |

### 3. Natural structured errors: inherited vs re-derived (clean, turns 2+)

- incremental wrong structured leaf-turns (T2+): **25**
- inherited from its own previous output (same wrong value): 16 (64%)
- rebuild also wrong on the same leaf-turn: 13 (52%), with the same wrong value: 9
- inherited AND rebuild also wrong (error is systematic, state channel not needed): 9
- inherited but rebuild gets it right (error survives ONLY through the carried state): **7** (28% of incremental's errors)

## r2_flatagent

solver `async_solvers:flatagent_solve` model `na` trajectories 10 solver_errors 0 billed in/out 370682/7036

### 1. Clean accuracy by turn (macro over trajectories; failed-call rows excluded)

| condition | metric | T1 | T2 | T3 | T4 | T5 | mean T2+ | excluded rows |
|---|---|---|---|---|---|---|---|---|
| incremental | all_field_acc | 98.7 | 94.9 | 92.4 | 92.0 | 89.3 | 92.1 | 0 |
| incremental | structured_acc | 99.5 | 97.1 | 94.6 | 96.0 | 95.0 | 95.7 | 0 |
| rebuild | all_field_acc | 98.7 | 93.6 | 91.1 | 89.5 | 86.3 | 90.1 | 0 |
| rebuild | structured_acc | 99.5 | 96.5 | 94.3 | 93.8 | 94.7 | 94.8 | 0 |
| oracle | all_field_acc | 98.7 | 95.6 | 95.8 | 97.2 | 96.5 | 96.3 | 0 |
| oracle | structured_acc | 99.5 | 97.5 | 97.0 | 100.0 | 99.4 | 98.5 | 0 |

### 2. Injected corruption per trajectory (incremental / oracle)

| trajectory | condition | field | injected | gold | persisted by turn | recovered at | valid |
|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `date_of_accident` | "2024-03-17" | "2024-03-14" | 0/0/0 | 3 | yes |
| cr_gen_01 | oracle | `date_of_accident` | "2024-03-17" | "2024-03-14" | 0/0/0 | 3 | yes |
| cr_gen_02 | incremental | `lighting` | "Daylight" | null | 0/0/0 | 3 | yes |
| cr_gen_02 | oracle | `lighting` | "Daylight" | null | 0/0/0 | 3 | yes |
| cr_gen_03 | incremental | `road_surface_condition` | "Wet" | null | 0/0/0 | 3 | yes |
| cr_gen_03 | oracle | `road_surface_condition` | "Wet" | null | 0/0/0 | 3 | yes |
| cr_gen_04 | incremental | `lighting` | "Dark\u2013Lit" | null | 1/0/0 | 4 | yes |
| cr_gen_04 | oracle | `lighting` | "Dark\u2013Lit" | null | 0/0/0 | 3 | yes |
| pa_gen_01 | incremental | `pain_details[0].pain_severity` | "High" | "Moderate" | 0/0/0 | 3 | yes |
| pa_gen_01 | oracle | `pain_details[0].pain_severity` | "High" | "Moderate" | 0/0/0 | 3 | yes |
| pa_gen_02 | incremental | `allergies[0].allergy_severity` | "Severe" | null | 0/0/0 | 3 | yes |
| pa_gen_02 | oracle | `allergies[0].allergy_severity` | "Severe" | null | 0/0/0 | 3 | yes |
| pa_gen_03 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | 0/0/0 | 3 | yes |
| pa_gen_03 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | 0/0/0 | 3 | yes |
| pa_gen_04 | incremental | `ambulatory_aid_use` | "Has but does not use" | null | 0/0/0 | 3 | yes |
| pa_gen_04 | oracle | `ambulatory_aid_use` | "Has but does not use" | null | 0/0/0 | 3 | yes |
| pa_gen_05 | incremental | `pain_details[0].pain_severity` | "Moderate" | "Mild" | 1/1/1 | never | yes |
| pa_gen_05 | oracle | `pain_details[0].pain_severity` | "Moderate" | "Mild" | 0/0/0 | 3 | yes |
| pa_handmade_01 | incremental | `current_medications[0].route` | "Inhaled" | null | 0/0/0 | 3 | yes |
| pa_handmade_01 | oracle | `current_medications[0].route` | "Inhaled" | null | 0/0/0 | 3 | yes |

| condition | valid trajectories | survived first post-injection turn | silently recovered | never recovered |
|---|---|---|---|---|
| incremental | 10 | 2/10 | 9/10 | 1/10 |
| oracle | 10 | 0/10 | 10/10 | 0/10 |

### 3. Natural structured errors: inherited vs re-derived (clean, turns 2+)

- incremental wrong structured leaf-turns (T2+): **33**
- inherited from its own previous output (same wrong value): 21 (64%)
- rebuild also wrong on the same leaf-turn: 25 (76%), with the same wrong value: 21
- inherited AND rebuild also wrong (error is systematic, state channel not needed): 17
- inherited but rebuild gets it right (error survives ONLY through the carried state): **4** (12% of incremental's errors)

## r2_dtv

solver `async_solvers:dtv_solve` model `na` trajectories 10 solver_errors 0 billed in/out 2569005/47286

### 1. Clean accuracy by turn (macro over trajectories; failed-call rows excluded)

| condition | metric | T1 | T2 | T3 | T4 | T5 | mean T2+ | excluded rows |
|---|---|---|---|---|---|---|---|---|
| incremental | all_field_acc | 98.1 | 93.0 | 90.7 | 90.1 | 88.1 | 90.5 | 0 |
| incremental | structured_acc | 98.3 | 94.4 | 92.6 | 94.4 | 94.5 | 94.0 | 0 |
| rebuild | all_field_acc | 98.1 | 94.0 | 91.1 | 92.5 | 88.7 | 91.5 | 0 |
| rebuild | structured_acc | 98.3 | 95.8 | 93.9 | 96.4 | 97.0 | 95.8 | 0 |
| oracle | all_field_acc | 98.1 | 94.6 | 94.3 | 95.7 | 97.1 | 95.4 | 0 |
| oracle | structured_acc | 98.3 | 96.1 | 96.0 | 98.4 | 99.6 | 97.5 | 0 |

### 2. Injected corruption per trajectory (incremental / oracle)

| trajectory | condition | field | injected | gold | persisted by turn | recovered at | valid |
|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `date_of_accident` | "2024-03-17" | "2024-03-14" | 0/0/0 | 3 | yes |
| cr_gen_01 | oracle | `date_of_accident` | "2024-03-17" | "2024-03-14" | 0/0/0 | 3 | yes |
| cr_gen_02 | incremental | `lighting` | "Daylight" | null | 0/0/0 | 3 | yes |
| cr_gen_02 | oracle | `lighting` | "Daylight" | null | 0/0/0 | 3 | yes |
| cr_gen_03 | incremental | `road_surface_condition` | "Wet" | null | 0/0/0 | 3 | yes |
| cr_gen_03 | oracle | `road_surface_condition` | "Wet" | null | 0/0/0 | 3 | yes |
| cr_gen_04 | incremental | `road_surface_condition` | "Wet" | null | 0/0/0 | 3 | yes |
| cr_gen_04 | oracle | `road_surface_condition` | "Wet" | null | 0/0/0 | 3 | yes |
| pa_gen_01 | incremental | `pain_details[0].pain_severity` | "High" | "Moderate" | 0/0/0 | 3 | yes |
| pa_gen_01 | oracle | `pain_details[0].pain_severity` | "High" | "Moderate" | 0/0/0 | 3 | yes |
| pa_gen_02 | incremental | `allergies[0].allergy_severity` | "Severe" | null | 0/0/0 | 3 | yes |
| pa_gen_02 | oracle | `allergies[0].allergy_severity` | "Severe" | null | 0/0/0 | 3 | yes |
| pa_gen_03 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | 0/0/0 | 3 | yes |
| pa_gen_03 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | 0/0/0 | 3 | yes |
| pa_gen_04 | incremental | `ambulatory_aid_use` | "Has but does not use" | null | 0/0/0 | 3 | yes |
| pa_gen_04 | oracle | `ambulatory_aid_use` | "Has but does not use" | null | 0/0/0 | 3 | yes |
| pa_gen_05 | incremental | `pain_details[0].pain_severity` | "Moderate" | "Mild" | 0/0/0 | 3 | yes |
| pa_gen_05 | oracle | `pain_details[0].pain_severity` | "Moderate" | "Mild" | 0/0/0 | 3 | yes |
| pa_handmade_01 | incremental | `current_medications[0].route` | "Inhaled" | null | 0/0/0 | 3 | yes |
| pa_handmade_01 | oracle | `current_medications[0].route` | "Inhaled" | null | 0/0/0 | 3 | yes |

| condition | valid trajectories | survived first post-injection turn | silently recovered | never recovered |
|---|---|---|---|---|
| incremental | 10 | 0/10 | 10/10 | 0/10 |
| oracle | 10 | 0/10 | 10/10 | 0/10 |

### 3. Natural structured errors: inherited vs re-derived (clean, turns 2+)

- incremental wrong structured leaf-turns (T2+): **45**
- inherited from its own previous output (same wrong value): 27 (60%)
- rebuild also wrong on the same leaf-turn: 25 (56%), with the same wrong value: 22
- inherited AND rebuild also wrong (error is systematic, state channel not needed): 14
- inherited but rebuild gets it right (error survives ONLY through the carried state): **13** (29% of incremental's errors)

## r2_fabricated_direct

solver `conformbench.systems.direct:solve` model `deepseek-flash:thinking=disabled` trajectories 7 solver_errors 0 billed in/out 136672/11737

### 1. Clean accuracy by turn (macro over trajectories; failed-call rows excluded)

| condition | metric | T1 | T2 | T3 | T4 | T5 | mean T2+ | excluded rows |
|---|---|---|---|---|---|---|---|---|
| incremental | all_field_acc | 99.6 | 95.5 | 92.2 | 91.6 | 91.0 | 92.5 | 0 |
| incremental | structured_acc | 100.0 | 99.0 | 95.1 | 96.1 | 97.1 | 96.8 | 0 |
| oracle | all_field_acc | 99.6 | 95.5 | 95.4 | 95.9 | 96.9 | 95.9 | 0 |
| oracle | structured_acc | 100.0 | 99.0 | 96.9 | 99.0 | 99.4 | 98.6 | 0 |

### 2. Injected corruption per trajectory (incremental / oracle)

| trajectory | condition | field | injected | gold | persisted by turn | recovered at | valid |
|---|---|---|---|---|---|---|---|
| cr_gen_02 | incremental | `traffic_control` | "Stop Sign" | null | 1/0/0 | 4 | yes |
| cr_gen_02 | oracle | `traffic_control` | "Stop Sign" | null | 0/0/0 | - | yes |
| cr_gen_03 | incremental | `traffic_control` | "Stop Sign" | null | 0/0/0 | 3 | yes |
| cr_gen_03 | oracle | `traffic_control` | "Stop Sign" | null | 0/0/0 | - | yes |
| pa_gen_01 | incremental | `appetite_change` | "Yes" | null | 1/0/0 | 4 | yes |
| pa_gen_01 | oracle | `appetite_change` | "Yes" | null | 0/0/0 | 3 | yes |
| pa_gen_02 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | 0/0/0 | 3 | yes |
| pa_gen_02 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | 0/0/0 | 3 | yes |
| pa_gen_04 | incremental | `appetite_change` | "Yes" | null | 0/0/0 | 3 | yes |
| pa_gen_04 | oracle | `appetite_change` | "Yes" | null | 0/0/0 | 3 | yes |
| pa_gen_05 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | 1/1/1 | never | yes |
| pa_gen_05 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | 1/1/0 | 5 | yes |
| pa_handmade_01 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | 0/0/0 | 3 | yes |
| pa_handmade_01 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | 0/0/0 | 3 | yes |

| condition | valid trajectories | survived first post-injection turn | silently recovered | never recovered |
|---|---|---|---|---|
| incremental | 7 | 3/7 | 6/7 | 1/7 |
| oracle | 7 | 1/7 | 5/7 | 0/7 |

### 3. Natural structured errors: inherited vs re-derived (clean, turns 2+)

- incremental wrong structured leaf-turns (T2+): **16**, inherited from its own previous output: 10 (62%)
- (rebuild condition not run in this out-dir, so the inherited-vs-re-derived split is not available)

## r2_fabricated_flatagent

solver `async_solvers:flatagent_solve` model `na` trajectories 7 solver_errors 0 billed in/out 413376/6058

### 1. Clean accuracy by turn (macro over trajectories; failed-call rows excluded)

| condition | metric | T1 | T2 | T3 | T4 | T5 | mean T2+ | excluded rows |
|---|---|---|---|---|---|---|---|---|
| incremental | all_field_acc | 99.2 | 97.2 | 94.4 | 92.7 | 90.8 | 93.8 | 0 |
| incremental | structured_acc | 100.0 | 99.0 | 96.3 | 96.4 | 94.9 | 96.7 | 0 |
| oracle | all_field_acc | 99.2 | 97.2 | 97.0 | 97.2 | 97.7 | 97.3 | 0 |
| oracle | structured_acc | 100.0 | 99.0 | 99.0 | 100.0 | 100.0 | 99.5 | 0 |

### 2. Injected corruption per trajectory (incremental / oracle)

| trajectory | condition | field | injected | gold | persisted by turn | recovered at | valid |
|---|---|---|---|---|---|---|---|
| cr_gen_02 | incremental | `traffic_control` | "Stop Sign" | null | 1/0/0 | 4 | yes |
| cr_gen_02 | oracle | `traffic_control` | "Stop Sign" | null | 1/0/0 | - | yes |
| cr_gen_03 | incremental | `traffic_control` | "Stop Sign" | null | 1/1/1 | never | yes |
| cr_gen_03 | oracle | `traffic_control` | "Stop Sign" | null | 1/1/1 | never | yes |
| pa_gen_01 | incremental | `appetite_change` | "Yes" | null | 1/1/1 | never | yes |
| pa_gen_01 | oracle | `appetite_change` | "Yes" | null | 1/1/1 | never | yes |
| pa_gen_02 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | 1/1/0 | 5 | yes |
| pa_gen_02 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | 1/1/1 | never | yes |
| pa_gen_04 | incremental | `appetite_change` | "Yes" | null | 1/1/1 | never | yes |
| pa_gen_04 | oracle | `appetite_change` | "Yes" | null | 1/1/1 | never | yes |
| pa_gen_05 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | 1/1/1 | never | yes |
| pa_gen_05 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | 0/0/0 | 3 | yes |
| pa_handmade_01 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | 1/1/1 | never | yes |
| pa_handmade_01 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | 1/1/1 | never | yes |

| condition | valid trajectories | survived first post-injection turn | silently recovered | never recovered |
|---|---|---|---|---|
| incremental | 7 | 7/7 | 2/7 | 5/7 |
| oracle | 7 | 6/7 | 1/7 | 5/7 |

### 3. Natural structured errors: inherited vs re-derived (clean, turns 2+)

- incremental wrong structured leaf-turns (T2+): **18**, inherited from its own previous output: 11 (61%)
- (rebuild condition not run in this out-dir, so the inherited-vs-re-derived split is not available)

## r2_fabricated_dtv

solver `async_solvers:dtv_solve` model `na` trajectories 7 solver_errors 0 billed in/out 627079/9250

### 1. Clean accuracy by turn (macro over trajectories; failed-call rows excluded)

| condition | metric | T1 | T2 | T3 | T4 | T5 | mean T2+ | excluded rows |
|---|---|---|---|---|---|---|---|---|
| incremental | all_field_acc | 97.7 | 94.6 | 92.3 | 90.5 | 89.6 | 91.8 | 0 |
| incremental | structured_acc | 98.2 | 96.0 | 93.8 | 93.4 | 93.5 | 94.1 | 0 |
| oracle | all_field_acc | 97.7 | 96.4 | 94.6 | 94.7 | 98.6 | 96.1 | 0 |
| oracle | structured_acc | 98.2 | 97.7 | 96.9 | 98.4 | 99.4 | 98.1 | 0 |

### 2. Injected corruption per trajectory (incremental / oracle)

| trajectory | condition | field | injected | gold | persisted by turn | recovered at | valid |
|---|---|---|---|---|---|---|---|
| cr_gen_02 | incremental | `traffic_control` | "Stop Sign" | null | 1/0/0 | 4 | yes |
| cr_gen_02 | oracle | `traffic_control` | "Stop Sign" | null | 1/0/0 | 4 | yes |
| cr_gen_03 | incremental | `traffic_control` | "Stop Sign" | null | 0/0/0 | - | yes |
| cr_gen_03 | oracle | `traffic_control` | "Stop Sign" | null | 1/0/0 | 4 | yes |
| pa_gen_01 | incremental | `appetite_change` | "Yes" | null | 0/0/0 | 3 | yes |
| pa_gen_01 | oracle | `appetite_change` | "Yes" | null | 1/1/1 | never | yes |
| pa_gen_02 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | 1/1/1 | never | yes |
| pa_gen_02 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | 1/1/1 | never | yes |
| pa_gen_04 | incremental | `appetite_change` | "Yes" | null | 1/1/1 | never | yes |
| pa_gen_04 | oracle | `appetite_change` | "Yes" | null | 1/1/1 | never | yes |
| pa_gen_05 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | 1/1/1 | never | yes |
| pa_gen_05 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | 1/1/1 | never | yes |
| pa_handmade_01 | incremental | `ambulatory_aid_use` | "Yes (uses)" | null | 1/1/1 | never | yes |
| pa_handmade_01 | oracle | `ambulatory_aid_use` | "Yes (uses)" | null | 1/1/1 | never | yes |

| condition | valid trajectories | survived first post-injection turn | silently recovered | never recovered |
|---|---|---|---|---|
| incremental | 7 | 5/7 | 2/7 | 4/7 |
| oracle | 7 | 7/7 | 2/7 | 5/7 |

### 3. Natural structured errors: inherited vs re-derived (clean, turns 2+)

- incremental wrong structured leaf-turns (T2+): **31**, inherited from its own previous output: 20 (65%)
- (rebuild condition not run in this out-dir, so the inherited-vs-re-derived split is not available)

## r2_ambiguous_direct

solver `conformbench.systems.direct:solve` model `deepseek-flash:thinking=disabled` trajectories 10 solver_errors 0 billed in/out 615597/52558

### 1. Clean accuracy by turn (macro over trajectories; failed-call rows excluded)

| condition | metric | T1 | T2 | T3 | T4 | T5 | mean T2+ | excluded rows |
|---|---|---|---|---|---|---|---|---|
| incremental | all_field_acc | 98.4 | 91.8 | 87.3 | 89.4 | 87.8 | 89.1 | 0 |
| incremental | structured_acc | 99.1 | 94.4 | 89.5 | 94.7 | 95.4 | 93.5 | 0 |
| oracle | all_field_acc | 98.4 | 92.8 | 93.4 | 95.6 | 95.2 | 94.3 | 0 |
| oracle | structured_acc | 99.1 | 95.4 | 95.2 | 99.5 | 99.2 | 97.3 | 0 |

### 2. Injected corruption per trajectory (incremental / oracle)

| trajectory | condition | field | injected | gold | persisted by turn | recovered at | valid |
|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `time_of_accident` | "18:30" | null | 0/0/0 | - | yes |
| cr_gen_01 | oracle | `time_of_accident` | "18:30" | null | 1/1/1 | never | yes |
| cr_gen_02 | incremental | `lighting` | "Dark\u2013Lit" | null | 0/0/0 | 3 | yes |
| cr_gen_02 | oracle | `lighting` | "Dark\u2013Lit" | null | 1/0/0 | 4 | yes |
| cr_gen_03 | incremental | `road_surface_condition` | "Wet" | null | 0/0/0 | 3 | yes |
| cr_gen_03 | oracle | `road_surface_condition` | "Wet" | null | 0/0/0 | 3 | yes |
| cr_gen_04 | incremental | `lighting` | "Dark\u2013Lit" | null | 0/0/0 | 3 | yes |
| cr_gen_04 | oracle | `lighting` | "Dark\u2013Lit" | null | 1/0/0 | 4 | yes |
| pa_gen_01 | incremental | `pain_details[0].pain_severity` | "Mild" | "Moderate" | 1/1/1 | never | yes |
| pa_gen_01 | oracle | `pain_details[0].pain_severity` | "Mild" | "Moderate" | 1/1/1 | never | yes |
| pa_gen_02 | incremental | `allergies[0].allergy_severity` | "Severe" | null | 1/1/1 | never | yes |
| pa_gen_02 | oracle | `allergies[0].allergy_severity` | "Severe" | null | 1/1/0 | - | yes |
| pa_gen_03 | incremental | `upper_denture` | "No" | null | 0/0/0 | 3 | yes |
| pa_gen_03 | oracle | `upper_denture` | "No" | null | 0/0/0 | 3 | yes |
| pa_gen_04 | incremental | `ambulatory_aid_use` | "Has but does not use" | null | 1/1/1 | never | yes |
| pa_gen_04 | oracle | `ambulatory_aid_use` | "Has but does not use" | null | 1/1/1 | never | yes |
| pa_gen_05 | incremental | `pain_details[0].pain_severity` | "Moderate" | "Mild" | 1/1/1 | never | yes |
| pa_gen_05 | oracle | `pain_details[0].pain_severity` | "Moderate" | "Mild" | 1/1/1 | never | yes |
| pa_handmade_01 | incremental | `sputum_amount` | "Moderate" | null | 1/1/1 | never | yes |
| pa_handmade_01 | oracle | `sputum_amount` | "Moderate" | null | 1/1/1 | never | yes |

| condition | valid trajectories | survived first post-injection turn | silently recovered | never recovered |
|---|---|---|---|---|
| incremental | 10 | 5/10 | 4/10 | 5/10 |
| oracle | 10 | 8/10 | 4/10 | 5/10 |

### 3. Natural structured errors: inherited vs re-derived (clean, turns 2+)

- incremental wrong structured leaf-turns (T2+): **50**, inherited from its own previous output: 32 (64%)
- (rebuild condition not run in this out-dir, so the inherited-vs-re-derived split is not available)

## r2_ambiguous_flatagent

solver `async_solvers:flatagent_solve` model `na` trajectories 10 solver_errors 0 billed in/out 1456723/22745

### 1. Clean accuracy by turn (macro over trajectories; failed-call rows excluded)

| condition | metric | T1 | T2 | T3 | T4 | T5 | mean T2+ | excluded rows |
|---|---|---|---|---|---|---|---|---|
| incremental | all_field_acc | 98.5 | 93.0 | 90.3 | 89.2 | 87.2 | 89.9 | 0 |
| incremental | structured_acc | 99.5 | 95.4 | 93.3 | 94.2 | 94.3 | 94.3 | 0 |
| oracle | all_field_acc | 98.5 | 93.1 | 95.6 | 97.0 | 96.7 | 95.6 | 0 |
| oracle | structured_acc | 99.5 | 95.4 | 96.3 | 98.9 | 100.0 | 97.6 | 0 |

### 2. Injected corruption per trajectory (incremental / oracle)

| trajectory | condition | field | injected | gold | persisted by turn | recovered at | valid |
|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `time_of_accident` | "18:30" | null | 1/1/1 | never | yes |
| cr_gen_01 | oracle | `time_of_accident` | "18:30" | null | 1/1/0 | - | yes |
| cr_gen_02 | incremental | `lighting` | "Dark\u2013Lit" | null | 1/1/0 | 5 | yes |
| cr_gen_02 | oracle | `lighting` | "Dark\u2013Lit" | null | 1/1/1 | never | yes |
| cr_gen_03 | incremental | `road_surface_condition` | "Wet" | null | 0/0/0 | 3 | yes |
| cr_gen_03 | oracle | `road_surface_condition` | "Wet" | null | 0/1/0 | 5 | yes |
| cr_gen_04 | incremental | `lighting` | "Dark\u2013Lit" | null | 1/1/1 | never | yes |
| cr_gen_04 | oracle | `lighting` | "Dark\u2013Lit" | null | 0/0/0 | 3 | yes |
| pa_gen_01 | incremental | `pain_details[0].pain_severity` | "Mild" | "Moderate" | 1/1/1 | never | yes |
| pa_gen_01 | oracle | `pain_details[0].pain_severity` | "Mild" | "Moderate" | 0/0/0 | 3 | yes |
| pa_gen_02 | incremental | `allergies[0].allergy_severity` | "Severe" | null | 1/1/1 | never | yes |
| pa_gen_02 | oracle | `allergies[0].allergy_severity` | "Severe" | null | 1/1/1 | never | yes |
| pa_gen_03 | incremental | `upper_denture` | "No" | null | 1/1/1 | never | yes |
| pa_gen_03 | oracle | `upper_denture` | "No" | null | 1/1/0 | 5 | yes |
| pa_gen_04 | incremental | `ambulatory_aid_use` | "Has but does not use" | null | 1/1/1 | never | yes |
| pa_gen_04 | oracle | `ambulatory_aid_use` | "Has but does not use" | null | 0/0/0 | - | yes |
| pa_gen_05 | incremental | `pain_details[0].pain_severity` | "Moderate" | "Mild" | 1/1/1 | never | yes |
| pa_gen_05 | oracle | `pain_details[0].pain_severity` | "Moderate" | "Mild" | 1/1/1 | never | yes |
| pa_handmade_01 | incremental | `sputum_amount` | "Moderate" | null | 1/0/0 | - | yes |
| pa_handmade_01 | oracle | `sputum_amount` | "Moderate" | null | 1/1/1 | never | yes |

| condition | valid trajectories | survived first post-injection turn | silently recovered | never recovered |
|---|---|---|---|---|
| incremental | 10 | 9/10 | 2/10 | 7/10 |
| oracle | 10 | 6/10 | 4/10 | 4/10 |

### 3. Natural structured errors: inherited vs re-derived (clean, turns 2+)

- incremental wrong structured leaf-turns (T2+): **42**, inherited from its own previous output: 28 (67%)
- (rebuild condition not run in this out-dir, so the inherited-vs-re-derived split is not available)

## r2_ambiguous_dtv

solver `async_solvers:dtv_solve` model `na` trajectories 10 solver_errors 0 billed in/out 2245890/35833

### 1. Clean accuracy by turn (macro over trajectories; failed-call rows excluded)

| condition | metric | T1 | T2 | T3 | T4 | T5 | mean T2+ | excluded rows |
|---|---|---|---|---|---|---|---|---|
| incremental | all_field_acc | 97.9 | 91.7 | 89.4 | 89.7 | 87.7 | 89.6 | 0 |
| incremental | structured_acc | 97.8 | 92.4 | 91.3 | 93.3 | 93.7 | 92.6 | 0 |
| oracle | all_field_acc | 97.9 | 93.8 | 95.1 | 95.7 | 94.6 | 94.8 | 0 |
| oracle | structured_acc | 97.8 | 95.4 | 95.9 | 97.9 | 97.9 | 96.8 | 0 |

### 2. Injected corruption per trajectory (incremental / oracle)

| trajectory | condition | field | injected | gold | persisted by turn | recovered at | valid |
|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `time_of_accident` | "18:30" | null | 1/1/1 | never | yes |
| cr_gen_01 | oracle | `time_of_accident` | "18:30" | null | 1/1/1 | never | yes |
| cr_gen_02 | incremental | `lighting` | "Dark\u2013Lit" | null | 0/0/0 | 3 | yes |
| cr_gen_02 | oracle | `lighting` | "Dark\u2013Lit" | null | 1/1/1 | never | yes |
| cr_gen_03 | incremental | `road_surface_condition` | "Wet" | null | 0/0/0 | 3 | yes |
| cr_gen_03 | oracle | `road_surface_condition` | "Wet" | null | 0/0/0 | - | yes |
| cr_gen_04 | incremental | `lighting` | "Dark\u2013Lit" | null | 1/1/1 | never | yes |
| cr_gen_04 | oracle | `lighting` | "Dark\u2013Lit" | null | 1/1/1 | never | yes |
| pa_gen_01 | incremental | `pain_details[0].pain_severity` | "Mild" | "Moderate" | 1/1/1 | never | yes |
| pa_gen_01 | oracle | `pain_details[0].pain_severity` | "Mild" | "Moderate" | 1/1/1 | never | yes |
| pa_gen_02 | incremental | `allergies[0].allergy_severity` | "Severe" | null | 1/1/1 | never | yes |
| pa_gen_02 | oracle | `allergies[0].allergy_severity` | "Severe" | null | 1/1/1 | never | yes |
| pa_gen_03 | incremental | `upper_denture` | "No" | null | 0/0/0 | 3 | yes |
| pa_gen_03 | oracle | `upper_denture` | "No" | null | 1/1/1 | never | yes |
| pa_gen_04 | incremental | `ambulatory_aid_use` | "Has but does not use" | null | 1/1/1 | never | yes |
| pa_gen_04 | oracle | `ambulatory_aid_use` | "Has but does not use" | null | 1/1/1 | never | yes |
| pa_gen_05 | incremental | `pain_details[0].pain_severity` | "Moderate" | "Mild" | 1/1/1 | never | yes |
| pa_gen_05 | oracle | `pain_details[0].pain_severity` | "Moderate" | "Mild" | 1/1/1 | never | yes |
| pa_handmade_01 | incremental | `sputum_amount` | "Moderate" | null | 1/1/1 | never | yes |
| pa_handmade_01 | oracle | `sputum_amount` | "Moderate" | null | 1/1/1 | never | yes |

| condition | valid trajectories | survived first post-injection turn | silently recovered | never recovered |
|---|---|---|---|---|
| incremental | 10 | 7/10 | 3/10 | 7/10 |
| oracle | 10 | 9/10 | 0/10 | 9/10 |

### 3. Natural structured errors: inherited vs re-derived (clean, turns 2+)

- incremental wrong structured leaf-turns (T2+): **57**, inherited from its own previous output: 32 (56%)
- (rebuild condition not run in this out-dir, so the inherited-vs-re-derived split is not available)

## r2_ambiguous_v4pro

solver `conformbench.systems.direct:solve` model `deepseek-v4-pro:thinking=disabled` trajectories 10 solver_errors 0 billed in/out 728166/61145

### 1. Clean accuracy by turn (macro over trajectories; failed-call rows excluded)

| condition | metric | T1 | T2 | T3 | T4 | T5 | mean T2+ | excluded rows |
|---|---|---|---|---|---|---|---|---|
| incremental | all_field_acc | 97.4 | 91.8 | 89.4 | 90.0 | 88.5 | 89.9 | 0 |
| incremental | structured_acc | 97.5 | 94.2 | 92.8 | 95.0 | 95.0 | 94.2 | 0 |
| oracle | all_field_acc | 97.4 | 94.1 | 95.7 | 96.8 | 97.1 | 95.9 | 0 |
| oracle | structured_acc | 97.5 | 95.8 | 97.3 | 99.5 | 100.0 | 98.1 | 0 |

### 2. Injected corruption per trajectory (incremental / oracle)

| trajectory | condition | field | injected | gold | persisted by turn | recovered at | valid |
|---|---|---|---|---|---|---|---|
| cr_gen_01 | incremental | `time_of_accident` | "18:30" | null | 1/1/1 | never | yes |
| cr_gen_01 | oracle | `time_of_accident` | "18:30" | null | 1/1/1 | never | yes |
| cr_gen_02 | incremental | `lighting` | "Dark\u2013Lit" | null | 1/0/0 | 4 | yes |
| cr_gen_02 | oracle | `lighting` | "Dark\u2013Lit" | null | 1/1/1 | never | yes |
| cr_gen_03 | incremental | `road_surface_condition` | "Wet" | null | 1/1/1 | never | yes |
| cr_gen_03 | oracle | `road_surface_condition` | "Wet" | null | 1/1/1 | never | yes |
| cr_gen_04 | incremental | `lighting` | "Dark\u2013Lit" | null | 1/1/1 | never | yes |
| cr_gen_04 | oracle | `lighting` | "Dark\u2013Lit" | null | 1/0/0 | 4 | yes |
| pa_gen_01 | incremental | `pain_details[0].pain_severity` | "Mild" | "Moderate" | 1/1/1 | never | yes |
| pa_gen_01 | oracle | `pain_details[0].pain_severity` | "Mild" | "Moderate" | 1/1/1 | never | yes |
| pa_gen_02 | incremental | `allergies[0].allergy_severity` | "Severe" | null | 1/1/1 | never | yes |
| pa_gen_02 | oracle | `allergies[0].allergy_severity` | "Severe" | null | 1/1/1 | never | yes |
| pa_gen_03 | incremental | `upper_denture` | "No" | null | 1/1/0 | 5 | yes |
| pa_gen_03 | oracle | `upper_denture` | "No" | null | 1/1/1 | never | yes |
| pa_gen_04 | incremental | `ambulatory_aid_use` | "Has but does not use" | null | 1/1/1 | never | yes |
| pa_gen_04 | oracle | `ambulatory_aid_use` | "Has but does not use" | null | 1/1/1 | never | yes |
| pa_gen_05 | incremental | `pain_details[0].pain_severity` | "Moderate" | "Mild" | 1/1/1 | never | yes |
| pa_gen_05 | oracle | `pain_details[0].pain_severity` | "Moderate" | "Mild" | 1/1/1 | never | yes |
| pa_handmade_01 | incremental | `sputum_amount` | "Moderate" | null | 1/1/1 | never | yes |
| pa_handmade_01 | oracle | `sputum_amount` | "Moderate" | null | 1/1/1 | never | yes |

| condition | valid trajectories | survived first post-injection turn | silently recovered | never recovered |
|---|---|---|---|---|
| incremental | 10 | 10/10 | 2/10 | 8/10 |
| oracle | 10 | 10/10 | 1/10 | 9/10 |

### 3. Natural structured errors: inherited vs re-derived (clean, turns 2+)

- incremental wrong structured leaf-turns (T2+): **43**, inherited from its own previous output: 31 (72%)
- (rebuild condition not run in this out-dir, so the inherited-vs-re-derived split is not available)
