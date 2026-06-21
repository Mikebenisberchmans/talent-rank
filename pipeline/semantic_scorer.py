# pipeline/semantic_scorer.py
# Stage 3 — Local cross-encoder semantic scoring
# No network, no API, CPU-only. Model must be pre-downloaded.

from config.jd_config import JD_TEXT, SEMANTIC_MODEL


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


def download_model_if_needed(model_name: str = SEMANTIC_MODEL) -> None:
    """
    Pre-download the model so ranking runs offline.
    Call this once during setup — not during the timed ranking run.
    """
    from sentence_transformers import CrossEncoder
    print(f"Downloading / verifying model: {model_name}")
    CrossEncoder(model_name)
    print("Model ready.")


def run_semantic_scoring(scored_candidates: list, top_n: int = 500) -> list:
    """
    Stage 3 entry point.
    Runs cross-encoder on the top_n candidates by heuristic score.
    Appends 'semantic_score' (0–100) to each score dict.
    Candidates outside top_n get semantic_score = 0.
    """
    from sentence_transformers import CrossEncoder
    import numpy as np

    top      = scored_candidates[:top_n]
    rest     = scored_candidates[top_n:]

    print(f"  Loading model: {SEMANTIC_MODEL}")
    model = CrossEncoder(SEMANTIC_MODEL)

    pairs = [
        (JD_TEXT, _get_candidate_text(c["_candidate"]))
        for c in top
    ]

    print(f"  Scoring {len(pairs)} candidates...")
    raw_scores = model.predict(pairs, batch_size=32, show_progress_bar=True)

    # Normalise to 0–100
    lo, hi  = float(np.min(raw_scores)), float(np.max(raw_scores))
    span    = hi - lo if hi != lo else 1.0
    for i, entry in enumerate(top):
        entry["semantic_score"] = round((float(raw_scores[i]) - lo) / span * 100, 2)

    for entry in rest:
        entry["semantic_score"] = 0.0

    return scored_candidates
