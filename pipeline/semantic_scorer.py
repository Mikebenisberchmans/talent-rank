# pipeline/semantic_scorer.py
# Stage 3 — Local cross-encoder semantic scoring
# No network, no API, CPU-only.
# Model is loaded from models/cross-encoder/ (saved by setup.py).

import os
from config.jd_config import JD_TEXT, SEMANTIC_MODEL

# Path to the locally saved model (populated by setup.py)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
LOCAL_MODEL_PATH = os.path.join(_PROJECT_ROOT, "models", "cross-encoder")


def _resolve_model_path() -> str:
    """Use local model if setup.py has been run, else fall back to HF name."""
    if os.path.isdir(LOCAL_MODEL_PATH) and os.listdir(LOCAL_MODEL_PATH):
        return LOCAL_MODEL_PATH
    print(f"  Warning: models/cross-encoder/ not found — loading from HuggingFace cache.")
    print(f"  Run python setup.py first to save the model locally.")
    return SEMANTIC_MODEL


def _get_candidate_text(candidate: dict) -> str:
    """
    Build rich text from candidate fields for cross-encoder input.
    Prioritises career descriptions (most signal-dense field).
    Truncated to ~2000 chars to stay within model token limits.
    """
    profile = candidate.get("profile", {})
    parts   = []

    if profile.get("summary"):
        parts.append(profile["summary"])

    current_title = profile.get("current_title", "")
    if current_title:
        parts.append(f"Current role: {current_title} at {profile.get('current_company', '')}")

    for job in candidate.get("career_history", []):
        desc = job.get("description", "")
        if desc:
            parts.append(f"{job.get('title', '')}: {desc}")

    skill_names = [s["name"] for s in candidate.get("skills", [])]
    if skill_names:
        parts.append(f"Skills: {', '.join(skill_names)}")

    return " ".join(parts)[:2000]


def run_semantic_scoring(scored_candidates: list, top_n: int = 500) -> list:
    """
    Stage 3 entry point.
    Runs cross-encoder on the top_n candidates by heuristic score.
    Appends 'semantic_score' (0-100) to each score dict.
    Candidates outside top_n get semantic_score = 0.
    """
    from sentence_transformers import CrossEncoder
    import numpy as np

    top  = scored_candidates[:top_n]
    rest = scored_candidates[top_n:]

    model_path = _resolve_model_path()
    print(f"  Loading model from: {model_path}")
    model = CrossEncoder(model_path)

    pairs = [
        (JD_TEXT, _get_candidate_text(c["_candidate"]))
        for c in top
    ]

    print(f"  Scoring {len(pairs)} candidates...")
    raw_scores = model.predict(pairs, batch_size=32, show_progress_bar=True)

    # Normalise to 0-100
    lo, hi = float(np.min(raw_scores)), float(np.max(raw_scores))
    span   = hi - lo if hi != lo else 1.0

    for i, entry in enumerate(top):
        entry["semantic_score"] = round((float(raw_scores[i]) - lo) / span * 100, 2)

    for entry in rest:
        entry["semantic_score"] = 0.0

    return scored_candidates
