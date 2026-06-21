# pipeline/ensemble.py
# Stage 4 — Weighted ensemble + final ranking

from config.jd_config import ENSEMBLE_WEIGHTS, FINAL_TOP_N

# Max possible values for each sub-score (used for normalisation)
_MAX = {"skill": 40.0, "career": 25.0, "behavioral": 20.0, "anti_fraud": 15.0}


def _normalise(value: float, max_val: float) -> float:
    return (value / max_val) * 100.0 if max_val > 0 else 0.0


def compute_final_score(entry: dict) -> float:
    """
    Weighted ensemble score (0–100).

    skill      → 35%  (normalised from 0–40)
    career     → 25%  (normalised from 0–25)
    behavioral → 20%  (normalised from 0–20)
    semantic   → 20%  (already 0–100)
    """
    w = ENSEMBLE_WEIGHTS
    return round(
        w["skill"]      * _normalise(entry.get("skill_score", 0),      _MAX["skill"])
        + w["career"]   * _normalise(entry.get("career_score", 0),     _MAX["career"])
        + w["behavioral"]* _normalise(entry.get("behavioral_score", 0), _MAX["behavioral"])
        + w["semantic"] * entry.get("semantic_score", 0.0),
        3,
    )


def run_ensemble(scored_candidates: list, top_n: int = FINAL_TOP_N) -> list:
    """
    Stage 4 entry point.
    Computes final scores, sorts, and returns top_n with rank attached.
    """
    for entry in scored_candidates:
        entry["final_score"] = compute_final_score(entry)

    scored_candidates.sort(key=lambda x: x["final_score"], reverse=True)

    top = scored_candidates[:top_n]
    for i, entry in enumerate(top, start=1):
        entry["rank"] = i

    return top
