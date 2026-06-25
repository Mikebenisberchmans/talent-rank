# talent-rank

AI-powered candidate ranking pipeline — multi-stage filtering, heuristic scoring, and semantic re-ranking against a job description.

---

## Directory structure

```
talent-rank/
├── main.py                        # Entry point — runs the full pipeline
├── setup.py                       # One-time model download (run before first use)
├── requirements.txt
├── .gitignore
│
├── config/
│   ├── jd_config.py               # Ensemble weights, thresholds, JD text, model name
│   ├── disqualifiers.py           # Hard-filter rules (consulting firms, research-only, etc.)
│   └── skill_taxonomy.py          # Skill groups with keyword lists for matching
│
├── pipeline/
│   ├── hard_filter.py             # Stage 1 — disqualifiers + honeypot detection
│   ├── heuristic_scorer.py        # Stage 2 — rule-based scoring (skill, career, behavioral, anti-fraud)
│   ├── semantic_scorer.py         # Stage 3 — cross-encoder re-ranking (local, offline)
│   ├── ensemble.py                # Stage 4 — weighted final score
│   └── reasoning.py               # Stage 5 — template reasoning string
│
├── utils/
│   └── candidate_loader.py        # Loads .json, .jsonl, and .jsonl.gz
│
├── models/
│   └── cross-encoder/             # Created by setup.py — not committed to git
│
├── data/                          # Not committed to git
│   └── sample_candidates.json
│
└── sandbox/
    └── app.py                     # Streamlit demo (required for submission)
```

---

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Download the cross-encoder model**
```bash
python setup.py
```
This saves `cross-encoder/ms-marco-MiniLM-L-6-v2` to `models/cross-encoder/`.
Run this once — needs internet. After this, the entire pipeline is offline.

---

## Running

**Full run (100K candidates)**
```bash
python main.py data/candidates.jsonl.gz
```

**Full run with custom output path**
```bash
python main.py data/candidates.jsonl.gz --output my_submission.csv
```

**Fast dev run — skip semantic stage**
```bash
python main.py data/sample_candidates.json --skip-semantic
```

**Streamlit sandbox demo**
```bash
streamlit run sandbox/app.py
```
Upload `sample_candidates.json` in the UI to see the pipeline run interactively.

---

## Pipeline stages

| Stage | What it does | Runtime |
|---|---|---|
| 1 — Hard filter | Blocks consulting-only, pure research, non-NLP, recent LLM-only, honeypots | ~2–5s |
| 2 — Heuristic scoring | Scores skill match, career quality, behavioral signals, anti-fraud | ~30s |
| 3 — Semantic scoring | Cross-encoder ranks top 500 against JD text | ~45s |
| 4 — Ensemble | Weighted final score: 35% skill + 25% career + 20% behavioral + 20% semantic | ~1s |
| 5 — Reasoning | Template string from candidate fields — no API, no cost | ~1s |

Total runtime on 100K candidates: **under 5 minutes on CPU**.

---

## Tuning

All weights and thresholds live in `config/jd_config.py` — change them there, not in pipeline code.

To add or modify skill keywords, edit `config/skill_taxonomy.py`.

To update disqualifier rules, edit `config/disqualifiers.py`.

---

## Common questions

**The model folder is empty / missing.**
Run `python setup.py`. It downloads and saves the model to `models/cross-encoder/`.

**`ModuleNotFoundError` when running main.py.**
Run from the project root: `cd talent-rank && python main.py ...`

**Pipeline crashes on the full `.jsonl.gz` file.**
Check available RAM — the full candidate pool needs ~4–6 GB. Use `--skip-semantic` to reduce peak usage during testing.

**Submission CSV format doesn't match.**
Run `python validate_submission.py submission.csv` before uploading.

**Sandbox link for submission.**
Deploy `sandbox/app.py` to [Streamlit Cloud](https://streamlit.io/cloud) — connect your GitHub repo and set the main file path to `sandbox/app.py`.
