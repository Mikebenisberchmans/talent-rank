# pipeline/reasoning.py
# Stage 5 — Template-based reasoning (no API, no network, no cost)
# Format: "{title} with {yoe} yrs; {n} AI core skills; response rate {rr}"

from config.skill_taxonomy import AI_SKILL_KEYWORDS


def _count_ai_skills(candidate: dict) -> int:
    """Count skills that overlap with the AI/ML taxonomy."""
    return sum(
        1 for s in candidate.get("skills", [])
        if any(kw in s.get("name", "").lower() for kw in AI_SKILL_KEYWORDS)
    )


def generate_reasoning(candidate: dict) -> str:
    """
    Build the 1-line reasoning string directly from candidate fields.
    No LLM, no API — pure template.
    """
    profile  = candidate.get("profile", {})
    signals  = candidate.get("redrob_signals", {})

    title    = profile.get("current_title", "N/A")
    yoe      = profile.get("years_of_experience", 0)
    ai_count = _count_ai_skills(candidate)
    rr       = signals.get("recruiter_response_rate", 0.0)

    return f"{title} with {yoe} yrs; {ai_count} AI core skills; response rate {rr:.2f}"
