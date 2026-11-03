# Plausible-alternative proposals (LLM-proposed, to be hand-reviewed)

| trajectory | field | gold | round-1 wrong | proposed alt | p | reason |
|---|---|---|---|---|---|---|
| pa_gen_01 | `pain_details[0].pain_severity` | Moderate | High | None | 1 | The user explicitly stated the pain is 'moderate,' matching the gold value directly with no ambiguity. |
| pa_gen_01 | `sputum_amount` | Small | Moderate | None | 1 | The user explicitly says "just a small amount," which uniquely and unambiguously maps to Small with no defensible basis for another option. |
| pa_gen_02 | `allergies[0].allergy_severity` | Moderate | Severe | None | 1 | The user explicitly stated the penicillin allergy severity is moderate, so no other option is defensible. |
| pa_gen_02 | `pain_details[0].pain_severity` | High | Mild | None | 1 | The user explicitly states the pain is 'high,' which directly and unambiguously maps to the 'High' option, leaving no defensible alternative. |
| pa_gen_03 | `ambulatory_aid_use` | No | Yes (uses) | None | 1 | The user explicitly says they don't use a cane or walker, which directly licenses 'No' for ambulatory aid use with no defensible alternative. |
| pa_gen_03 | `lower_denture` | No | Yes | None | 1 | The user explicitly states they wear an upper denture but no lower one, which unambiguously licenses the gold value 'No'. |
| pa_gen_03 | `upper_denture` | Yes | No | None | 1 | The user explicitly states they wear an upper denture, so 'Yes' is the only defensible reading. |
| pa_gen_04 | `ambulatory_aid_use` | Yes (uses) | Has but does not use | None | 1 | The user explicitly states "I use a walker now," which directly and unambiguously licenses "Yes (uses)" for this field. |
| pa_gen_04 | `current_medications[0].route` | Oral | Inhaled | None | 1 | The user explicitly says warfarin is taken 'by mouth,' which uniquely maps to the Oral route. |
| pa_gen_05 | `pain_details[0].pain_severity` | Mild | Moderate | None | 1 | The user explicitly described the pain as a 'mild ache,' which directly and unambiguously licenses the gold value 'Mild' with no defensible alternative. |
| cr_gen_01 | `date_of_accident` | 2024-03-14 | 2024-03-17 | None | 1 | The user gave an explicit, unambiguous date (14 March 2024), which maps uniquely to 2024-03-14 with no rounding or vagueness. |
| cr_gen_01 | `time_of_accident` | 18:45 | 20:45 | None | 1 | The user stated 'around 6:45 in the evening,' which unambiguously maps to 18:45; 'around' is mild hedging but does not license a different specific time value. |
| cr_gen_02 | `lighting` | Dark–Unlit | Daylight | None | 1 | The user explicitly said it was "pitch dark with no streetlights anywhere," which uniquely supports Dark–Unlit and rules out the lit options. |
| cr_gen_02 | `road_surface_condition` | Snow / Ice | Debris | None | 1 | The user explicitly states the road was covered in snow and ice, so Snow / Ice is the only defensible reading with no other option licensed. |
| cr_gen_02 | `date_of_accident` | 2024-02-03 | 2024-02-06 | 2024-02-04 | 2 | The user said it was 'the night of February 3rd' but 'just after midnight, so the early hours of the 3rd,' a self-contradictory phrasing where 'night of February 3rd' could be read as the small hours of the 4th, though the explicit 'early hours of the 3rd' makes that reading weak. |
| cr_gen_03 | `lighting` | Daylight | Dusk / Dawn | None | 1 | The user explicitly said it was 'sunny and clear,' which unambiguously licenses Daylight and no other lighting option. |
| cr_gen_03 | `road_surface_condition` | Dry | Wet | None | 1 | The user explicitly stated 'dry road,' which unambiguously maps to the Dry option. |
| cr_gen_03 | `weather` | Clear | Rain | None | 1 | The user explicitly said 'sunny and clear,' which directly and unambiguously maps to the 'Clear' option with no overlapping or vague reading. |
| cr_gen_03 | `date_of_accident` | 2025-03-14 | 2025-03-17 | None | 1 | The user explicitly stated the date as 'the 14th of March 2025,' which uniquely maps to 2025-03-14 with no ambiguity. |
| cr_gen_03 | `time_of_accident` | 08:40 | 10:40 | 08:40 | 1 | The user explicitly said 'around 8:40 in the morning,' and 08:40 is the only defensible reading given the time field format; any other time would be a guess. |
| cr_gen_04 | `lighting` | Dusk / Dawn | Dark–Lit | None | 1 | The user explicitly said 'at dusk', which unambiguously maps to the 'Dusk / Dawn' option with no overlapping or vague adjective warranting another choice. |
| cr_gen_04 | `road_surface_condition` | Dry | Wet | None | 1 | The user explicitly stated 'the road was dry,' which unambiguously licenses the gold value Dry with no competing option. |
| cr_gen_04 | `weather` | Clear | Rain | None | 1 | The user explicitly stated 'The weather was clear,' which unambiguously maps to the Clear option with no competing reading. |
| cr_gen_04 | `date_of_accident` | 2024-03-14 | 2024-03-17 | None | 1 | The user explicitly stated the fourteenth of March, 2024, which maps uniquely to 2024-03-14 with no rounding or ambiguity. |
| pa_handmade_01 | `current_medications[0].route` | Oral | Inhaled | None | 1 | The user explicitly says aspirin is taken "by mouth daily," which uniquely maps to the Oral route among the options. |
| pa_handmade_01 | `hemoptysis_any` | No | Yes (single episode) | None | 5 | The user explicitly states 'no blood' in the sputum, which unambiguously licenses the 'No' value with no defensible alternative. |
| pa_handmade_01 | `sputum_amount` | Small | Moderate | None | 1 | The user explicitly states "a small amount of green phlegm," which maps directly to the "Small" option and licenses no other defensible value. |

## Evidence per field

### pa_gen_01 `pain_details[0].pain_severity`

```
[turn 1] assistant: Hello! I'll help you complete the clinical screening questionnaire. To start, are you experiencing any pain right now?
[turn 1] user: Yes, my right knee has been aching for about three months, and I'd call it moderate.
```

### pa_gen_01 `sputum_amount`

```
[turn 2] assistant: Thanks. Do you have a cough, and if so, how long has it been going on?
[turn 2] user: Yes, I've had a chesty cough for about a week now, and there's some white phlegm coming up, just a small amount.
```

### pa_gen_02 `allergies[0].allergy_severity`

```
[turn 2] assistant: Thanks for that. Do you have any known allergies, and are you currently taking any medications?
[turn 2] user: I'm allergic to penicillin, it gives me a rash, and I'd say it's moderate. I don't take any medications right now.
```

### pa_gen_02 `pain_details[0].pain_severity`

```
[turn 1] assistant: Hello! I'll be asking a few health screening questions today. First, are you experiencing any pain right now?
[turn 1] user: Yes, I've got lower back pain that started about a week ago after I lifted something heavy at work. It's pretty bad, I'd call it high.
```

### pa_gen_03 `ambulatory_aid_use`

```
[turn 2] assistant: Thanks for sharing. Do you currently use any ambulatory aid like a cane or walker, and do you wear dentures?
[turn 2] user: I don't use any cane or walker. I do wear an upper denture, but no lower one.
```

### pa_gen_03 `lower_denture`

```
[turn 2] assistant: Thanks for sharing. Do you currently use any ambulatory aid like a cane or walker, and do you wear dentures?
[turn 2] user: I don't use any cane or walker. I do wear an upper denture, but no lower one.
```

### pa_gen_03 `upper_denture`

```
[turn 2] assistant: Thanks for sharing. Do you currently use any ambulatory aid like a cane or walker, and do you wear dentures?
[turn 2] user: I don't use any cane or walker. I do wear an upper denture, but no lower one.
```

### pa_gen_04 `ambulatory_aid_use`

```
[turn 2] assistant: Thank you. Have you fallen at any point in the last 12 months?
[turn 2] user: Yes, I had a fall last month, and I use a walker now. I also take a blood thinner called warfarin daily by mouth.
```

### pa_gen_04 `current_medications[0].route`

```
[turn 2] assistant: Thank you. Have you fallen at any point in the last 12 months?
[turn 2] user: Yes, I had a fall last month, and I use a walker now. I also take a blood thinner called warfarin daily by mouth.
```

### pa_gen_05 `pain_details[0].pain_severity`

```
[turn 1] assistant: Hello! Thanks for taking the time to fill this out. Let's start simple — do you have any pain right now?
[turn 1] user: Yes, I do — my hip has been bothering me. It's a mild ache.
```

### cr_gen_01 `date_of_accident`

```
[turn 1] assistant: Hello, I'll help you complete the crash report. To start, what date did the accident happen?
[turn 1] user: It happened on the fourteenth of March, 2024.
```

### cr_gen_01 `time_of_accident`

```
[turn 2] assistant: Thanks. What time did the accident occur, and where did it happen?
[turn 2] user: It was around 6:45 in the evening, at the intersection of Maple Avenue and Route 9 in Riverton, right by the gas station.
```

### cr_gen_02 `lighting`

```
[turn 2] assistant: Thanks. Where did the accident occur — street or route, town, and any landmark?
[turn 2] user: On Route 9 heading out of Millbrook, about half a mile past the old grain silo. It was snowing pretty hard, the road was covered in snow and ice, and it was pitch dark with no streetlights anywhere.
```

### cr_gen_02 `road_surface_condition`

```
[turn 2] assistant: Thanks. Where did the accident occur — street or route, town, and any landmark?
[turn 2] user: On Route 9 heading out of Millbrook, about half a mile past the old grain silo. It was snowing pretty hard, the road was covered in snow and ice, and it was pitch dark with no streetlights anywhere.
```

### cr_gen_02 `date_of_accident`

```
[turn 1] assistant: Hello! I'll help you file the crash report. Let's start with the basics — what date did the accident happen?
[turn 1] user: It was the night of February 3rd, 2024 — well, just after midnight, so the early hours of the 3rd.
```

### cr_gen_03 `lighting`

```
[turn 2] assistant: Got it. Where exactly did this happen — street, town, and any nearby landmark?
[turn 2] user: On Elm Street in Springfield, just past the second set of lights near the post office. It was a straight stretch, dry road, sunny and clear, and I was in my blue Honda Civic.
```

### cr_gen_03 `road_surface_condition`

```
[turn 2] assistant: Got it. Where exactly did this happen — street, town, and any nearby landmark?
[turn 2] user: On Elm Street in Springfield, just past the second set of lights near the post office. It was a straight stretch, dry road, sunny and clear, and I was in my blue Honda Civic.
```

### cr_gen_03 `weather`

```
[turn 2] assistant: Got it. Where exactly did this happen — street, town, and any nearby landmark?
[turn 2] user: On Elm Street in Springfield, just past the second set of lights near the post office. It was a straight stretch, dry road, sunny and clear, and I was in my blue Honda Civic.
```

### cr_gen_03 `date_of_accident`

```
[turn 1] assistant: Hi there — I'm sorry about the accident. Let's get your crash report started. What was the date of the accident?
[turn 1] user: Thanks. It happened on the 14th of March 2025, around 8:40 in the morning.
```

### cr_gen_03 `time_of_accident`

```
[turn 1] assistant: Hi there — I'm sorry about the accident. Let's get your crash report started. What was the date of the accident?
[turn 1] user: Thanks. It happened on the 14th of March 2025, around 8:40 in the morning.
```

### cr_gen_04 `lighting`

```
[turn 2] assistant: Thanks. What time did the accident occur?
[turn 2] user: Around 7:15 in the evening, at dusk. It was at the stop sign on Elm Street in Springfield, near the corner with Oak Avenue. The weather was clear and the road was dry. Three vehicles were involved. I was the driver of the first car, a black Toyota Corolla, plate ABC-123, stopped at the sign when I was rear-ended.
```

### cr_gen_04 `road_surface_condition`

```
[turn 2] assistant: Thanks. What time did the accident occur?
[turn 2] user: Around 7:15 in the evening, at dusk. It was at the stop sign on Elm Street in Springfield, near the corner with Oak Avenue. The weather was clear and the road was dry. Three vehicles were involved. I was the driver of the first car, a black Toyota Corolla, plate ABC-123, stopped at the sign when I was rear-ended.
```

### cr_gen_04 `weather`

```
[turn 2] assistant: Thanks. What time did the accident occur?
[turn 2] user: Around 7:15 in the evening, at dusk. It was at the stop sign on Elm Street in Springfield, near the corner with Oak Avenue. The weather was clear and the road was dry. Three vehicles were involved. I was the driver of the first car, a black Toyota Corolla, plate ABC-123, stopped at the sign when I was rear-ended.
```

### cr_gen_04 `date_of_accident`

```
[turn 1] assistant: Hello, I'll help you complete the crash report. First, what was the date of the accident?
[turn 1] user: It happened on the fourteenth of March, 2024.
```

### pa_handmade_01 `current_medications[0].route`

```
[turn 2] assistant: Thanks. Tell me about the cough, and do you bring anything up?
[turn 2] user: The cough started 5 days ago and I bring up a small amount of green phlegm, no blood. I take aspirin 81 mg by mouth daily.
```

### pa_handmade_01 `hemoptysis_any`

```
[turn 2] assistant: Thanks. Tell me about the cough, and do you bring anything up?
[turn 2] user: The cough started 5 days ago and I bring up a small amount of green phlegm, no blood. I take aspirin 81 mg by mouth daily.
```

### pa_handmade_01 `sputum_amount`

```
[turn 2] assistant: Thanks. Tell me about the cough, and do you bring anything up?
[turn 2] user: The cough started 5 days ago and I bring up a small amount of green phlegm, no blood. I take aspirin 81 mg by mouth daily.
```
