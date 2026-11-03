# ECE 6256 Final Project (Fall 2026)

**Working title:** *Is That for Me? Addressee-Aware Turn-Keeping for Open Full-Duplex Speech Models under Same-Voice Side-Talk*

Georgia Tech ECE 6256 Conversational AI, final-project repository. Open full-duplex speech models (Moshi, PersonaPlex, Freeze-Omni) answer when the user turns to a third person; the shipped fixes have no published method, and the open remedies gate on speaker identity, which cannot help when the side-talk is in the user's own voice. We propose to measure how much identity gating solves, build a de-shortcut same-voice side-talk test set with voice cloning, LoRA-fine-tune Moshi on cue-controlled synthetic side-talk, and ablate lexical against acoustic cues.

Status (2026-11-03): proposal draft ready for the 11/5 deadline; topic pilots done on a laptop; PACE jobs prepared but not yet run.

| deadline | deliverable |
|---|---|
| 11/5 | proposal (2-page ACL format, >= 5 team-verified citations) |
| 11/19 | milestone |
| 12/3 | poster |
| 12/8 | paper + code |

## Layout

| path | what |
|---|---|
| `proposal/` | ACL-format proposal: `proposal.tex`, `proposal.bib` (14 verified entries), compiled `proposal.pdf`, `build.sh`, and a `README.md` with the citation-verification record and the must-change list (author placeholders!) |
| `pilot_R/` | Pilot for the main topic on Full-Duplex-Bench v1.5: ECAPA identity cue per scenario, the G0 window gate, the vocative/far-field shortcut check, Chatterbox voice-clone timing. Results, figure and exact commands in `pilot_R/README_pilot.md`; Table 1 of the proposal comes from `pilot_R/runs/similarity/` and `pilot_R/runs/g0/` |
| `pilot_B/` | Pilot for Plan B (ConFormBench closed-loop error persistence, DeepSeek API). Results in `pilot_B/README_pilot.md` and `pilot_B/runs/r2_analysis.md`; LLM-generated trajectories in `pilot_B/runs/*.jsonl` |
| `选题建议-2026-11-02.md` | Topic survey and recommendation (Chinese): what is already taken in the field, the recommended topic R plus three backups, analysis of the two directions from the team doc, both pilot results, pointer to the proposal |
| `pilot_R/fdb`, `pilot_B/conformbench` | Git submodules: [Full-Duplex-Bench](https://github.com/DanielLin94144/Full-Duplex-Bench) @ `3e799c4` (CC BY-NC 4.0) and [ConFormBench](https://github.com/tveigel/conformbench) @ `23cbfd0` (MIT) |

## Clone

```bash
git clone --recursive https://github.com/WYI1223/ece6256-final-project.git
```

Already cloned without `--recursive`? Run `git submodule update --init`.

## Build the proposal

```bash
cd proposal && bash build.sh
```

Needs `pdflatex` and `bibtex` (any TeX Live). For Overleaf, upload `proposal.tex`, `proposal.bib`, `acl.sty` and `acl_natbib.bst`. Two author emails in `proposal.tex` (line 16) are still `TODO`; fill them before submitting. ACL convention does not count references toward the page limit (body is exactly 2 pages, references on page 3); `proposal/README.md` says which entries to cut if the instructor counts them.

## Reproduce the pilots

Not in git (see `.gitignore`): downloaded data, model weights, the 502 G0 muted wavs, and API keys.

**pilot_R** (Python 3.11, torch CPU, speechbrain 1.0.3; exact env and commands in `pilot_R/README_pilot.md`)
1. Download the four FDB v1.5 zips from the Google Drive folder listed in the README into `pilot_R/data/zips/` and unzip into `pilot_R/data/v1_5/`.
2. Download `speechbrain/spkrec-ecapa-voxceleb` from Hugging Face into `pilot_R/runs/models/spkrec-ecapa-voxceleb/`.
3. Run the scripts in the order given in the README (all with `python -I`, from `pilot_R/`).
4. The Moshi baseline on PACE-ICE: `pilot_R/slurm/run_moshi_fdb.sbatch` and `pilot_R/scripts/run_moshi_offline.py` (start with `--limit 3`).

**pilot_B** (Python 3.11; `pip install -e pilot_B/conformbench`)
1. Download `conformbench-data-v1.0.0` from Zenodo and extract it to `pilot_B/data_zenodo/conformbench-data-v1.0.0/`.
2. Copy `pilot_B/env.example` to `pilot_B/conformbench/.env`, fill in your DeepSeek (or other OpenAI-compatible) key and the absolute data path.
3. `pilot_B/scripts/round2_rerun.sh` reruns the round-2 experiments; `scripts/r2_analyze.py` writes `runs/r2_analysis.md`.

The pilot READMEs mention local absolute paths (conda envs, data dirs) from the laptop they ran on; adjust them to your machine.
