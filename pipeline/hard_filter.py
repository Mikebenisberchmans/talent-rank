# pipeline/hard_filter.py
# Stage 1 — Hard filters + honeypot detection
# Every rule here maps directly to a JD disqualifier or signals doc warning

from datetime import date, datetime
from config.disqualifiers import (
    CONSULTING_COMPANIES, NON_NLP_DOMAINS, NLP_REDEMPTION_KEYWORDS,
    RESEARCH_ONLY_TITLES, PRODUCTION_SIGNALS,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _norm(text: str) -> str:
    return (text or "").lower().strip()


def _all_companies(candidate: dict) -> list:
    return [_norm(j.get("company", "")) for j in candidate.get("career_history", [])]


def _all_titles(candidate: dict) -> list:
    return [_norm(j.get("title", "")) for j in candidate.get("career_history", [])]


def _full_text(candidate: dict) -> str:
    """All free-text fields concatenated and lowercased."""
    parts = [candidate.get("profile", {}).get("summary", "")]
    for job in candidate.get("career_history", []):
        parts.append(job.get("description", ""))
        parts.append(job.get("title", ""))
    for s in candidate.get("skills", []):
        parts.append(s.get("name", ""))
    return " ".join(parts).lower()


# ── Individual filter checks ──────────────────────────────────────────────────

def _is_consulting_only(candidate: dict) -> bool:
    """Entire career at consulting firms with no product-company experience."""
    companies = _all_companies(candidate)
    if not companies:
        return False
    consulting_count = sum(
        1 for c in companies
        if any(cons in c for cons in CONSULTING_COMPANIES)
    )
    return consulting_count == len(companies)


def _is_pure_research(candidate: dict) -> bool:
    """All roles are research roles AND no production deployment evidence."""
    titles = _all_titles(candidate)
    if not titles:
        return False
    research_count = sum(
        1 for t in titles
        if any(rt in t for rt in RESEARCH_ONLY_TITLES)
    )
    if research_count < len(titles):
        return False  # at least one non-research role — OK
    text = _full_text(candidate)
    return not any(sig in text for sig in PRODUCTION_SIGNALS)


def _is_non_nlp_specialist(candidate: dict) -> bool:
    """Primarily CV/Speech/Robotics with no NLP/IR signal at all."""
    text = _full_text(candidate)
    has_non_nlp = any(domain in text for domain in NON_NLP_DOMAINS)
    if not has_non_nlp:
        return False
    has_nlp = any(kw in text for kw in NLP_REDEMPTION_KEYWORDS)
    return not has_nlp


def _is_recent_llm_only(candidate: dict) -> bool:
    """Only AI experience is recent LangChain/wrapper work under 12 months."""
    skills = candidate.get("skills", [])
    ai_skills = [
        s for s in skills
        if any(kw in _norm(s.get("name", "")) for kw in
               ["llm", "gpt", "langchain", "openai", "chatgpt", "generative ai"])
    ]
    if not ai_skills:
        return False  # no AI skills listed at all — will be caught by skill scorer

    all_very_recent = all(s.get("duration_months", 0) < 12 for s in ai_skills)
    if not all_very_recent:
        return False

    text = _full_text(candidate)
    has_pre_llm_ml = any(kw in text for kw in [
        "tensorflow", "pytorch", "scikit-learn", "sklearn", "xgboost",
        "spark ml", "ranking", "retrieval", "embedding model", "word2vec",
        "bert", "recommendation system", "information retrieval",
    ])
    return not has_pre_llm_ml


def _is_honeypot(candidate: dict) -> tuple:
    """
    Detect statistically impossible / planted profiles.
    Returns (is_honeypot: bool, reason: str)
    """
    profile  = candidate.get("profile", {})
    signals  = candidate.get("redrob_signals", {})
    skills   = candidate.get("skills", [])
    career   = candidate.get("career_history", [])

    # 1. YOE vs sum of career durations
    yoe = profile.get("years_of_experience", 0)
    career_months = sum(j.get("duration_months", 0) for j in career)
    career_years  = career_months / 12 if career_months else 0
    if yoe > 0 and career_years > 0 and abs(yoe - career_years) > 4:
        return True, f"YOE ({yoe:.1f}) vs career history ({career_years:.1f} yrs)"

    # 2. Advanced skills with zero supporting evidence
    assessment = signals.get("skill_assessment_scores", {})
    zero_evidence = sum(
        1 for s in skills
        if (s.get("proficiency") == "advanced"
            and s.get("duration_months", 0) == 0
            and s.get("endorsements", 0) == 0
            and assessment.get(s["name"], 100) < 35)
    )
    if zero_evidence >= 3:
        return True, f"{zero_evidence} advanced skills with zero evidence"

    # 3. All behavioral signals simultaneously perfect (too good to be real)
    perfect = sum([
        signals.get("interview_completion_rate", 0) == 1.0,
        signals.get("offer_acceptance_rate", 0)     == 1.0,
        signals.get("recruiter_response_rate", 0)   == 1.0,
        signals.get("profile_completeness_score", 0) == 100,
        signals.get("github_activity_score", 0)      == 100,
    ])
    if perfect >= 4:
        return True, "Suspiciously perfect behavioral signals"

    # 4. Impossible YOE values
    if not (0 < yoe < 45):
        return True, f"Impossible YOE: {yoe}"

    return False, ""


# ── Main stage entry point ────────────────────────────────────────────────────

def hard_filter(candidates: list) -> tuple:
    """
    Stage 1: Apply all hard filters to candidate list.

    Returns:
        passed  (list[dict])  — candidates that cleared all filters
        stats   (dict)        — breakdown of how many were removed and why
    """
    passed = []
    stats = {
        "total":            len(candidates),
        "honeypot":         0,
        "consulting_only":  0,
        "pure_research":    0,
        "non_nlp":          0,
        "recent_llm_only":  0,
        "passed":           0,
    }

    for c in candidates:
        # Honeypot first — most critical check
        is_honey, reason = _is_honeypot(c)
        if is_honey:
            stats["honeypot"] += 1
            c["_filter_reason"] = f"honeypot:{reason}"
            continue

        if _is_consulting_only(c):
            stats["consulting_only"] += 1
            c["_filter_reason"] = "consulting_only"
            continue

        if _is_pure_research(c):
            stats["pure_research"] += 1
            c["_filter_reason"] = "pure_research"
            continue

        if _is_non_nlp_specialist(c):
            stats["non_nlp"] += 1
            c["_filter_reason"] = "non_nlp_specialist"
            continue

        if _is_recent_llm_only(c):
            stats["recent_llm_only"] += 1
            c["_filter_reason"] = "recent_llm_only"
            continue

        passed.append(c)

    stats["passed"] = len(passed)
    return passed, stats
