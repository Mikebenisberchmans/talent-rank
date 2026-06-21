# pipeline/heuristic_scorer.py
# Stage 2 — Fast rule-based scoring (no model, no network)
# Four sub-scores that map to the four columns in the checklist

from datetime import date, datetime
from config.jd_config import (
    YOE_IDEAL_MIN, YOE_IDEAL_MAX,
    PREFERRED_CITIES, NOTICE_EXCELLENT, NOTICE_GOOD,
)
from config.skill_taxonomy import SKILL_GROUPS
from config.disqualifiers import CONSULTING_COMPANIES


# ── Helpers ──────────────────────────────────────────────────────────────────

def _norm(text: str) -> str:
    return (text or "").lower().strip()


def _days_since(date_str: str) -> int:
    if not date_str:
        return 9999
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (date.today() - d).days
    except Exception:
        return 9999


def _career_text(candidate: dict) -> str:
    parts = [candidate.get("profile", {}).get("summary", "")]
    for job in candidate.get("career_history", []):
        parts.append(job.get("description", ""))
    return " ".join(parts).lower()


# ── Sub-score 1: Skill match (0–40 pts) ─────────────────────────────────────

def _score_skills(candidate: dict) -> float:
    skills      = candidate.get("skills", [])
    career_text = _career_text(candidate)
    assessment  = candidate.get("redrob_signals", {}).get("skill_assessment_scores", {})

    total = 0.0

    for group in SKILL_GROUPS.values():
        max_pts = group["max_points"]

        # Find matching skill entry
        skill_match = None
        for s in skills:
            s_name = _norm(s.get("name", ""))
            if any(kw in s_name for kw in group["skill_keywords"]):
                skill_match = s
                break

        # Check description text
        desc_match = any(kw in career_text for kw in group["description_keywords"])

        if skill_match is None and not desc_match:
            continue  # not present at all

        if skill_match:
            prof_mult = {
                "beginner":    0.40,
                "intermediate":0.65,
                "advanced":    0.90,
                "expert":      1.00,
            }.get(_norm(skill_match.get("proficiency", "")), 0.40)

            duration_mult = min(1.0, skill_match.get("duration_months", 0) / 24)
            endorse_mult  = min(1.0, skill_match.get("endorsements", 0) / 20)

            pts = max_pts * (0.35 + 0.30 * prof_mult + 0.20 * duration_mult + 0.15 * endorse_mult)

            # Penalise keyword stuffers: advanced claim + low assessment score
            assess_val = assessment.get(skill_match.get("name", ""), None)
            if assess_val is not None and assess_val < 35 and prof_mult >= 0.90:
                pts *= 0.50

        else:
            # Description match only — weaker signal
            pts = max_pts * 0.35

        total += pts

    return min(40.0, total)


# ── Sub-score 2: Career quality (0–25 pts) ───────────────────────────────────

def _score_career(candidate: dict) -> float:
    profile   = candidate.get("profile", {})
    career    = candidate.get("career_history", [])
    education = candidate.get("education", [])

    total = 0.0

    # YOE in ideal band (0–8 pts)
    yoe = profile.get("years_of_experience", 0)
    if YOE_IDEAL_MIN <= yoe <= YOE_IDEAL_MAX:
        total += 8.0
    elif yoe > YOE_IDEAL_MAX:
        total += max(0.0, 8.0 - (yoe - YOE_IDEAL_MAX) * 0.6)
    else:
        total += max(0.0, 8.0 - (YOE_IDEAL_MIN - yoe) * 2.0)

    # Product company ratio (0–8 pts)
    if career:
        product_jobs = [
            j for j in career
            if not any(cons in _norm(j.get("company", "")) for cons in CONSULTING_COMPANIES)
        ]
        total += 8.0 * (len(product_jobs) / len(career))

    # Education tier (0–4 pts)
    if education:
        tier = education[0].get("tier", "tier_4")
        total += {"tier_1": 4.0, "tier_2": 3.0, "tier_3": 1.5, "tier_4": 0.5}.get(tier, 0.0)

    # Career stability — penalise job-hopping < 18 months (0–5 pts)
    if career:
        short_stints = sum(
            1 for j in career
            if j.get("duration_months", 99) < 18 and not j.get("is_current", False)
        )
        total += max(0.0, 5.0 - short_stints * 1.5)

    return min(25.0, total)


# ── Sub-score 3: Behavioral signals (0–20 pts) ───────────────────────────────

def _score_behavioral(candidate: dict) -> float:
    signals = candidate.get("redrob_signals", {})
    profile = candidate.get("profile", {})

    total = 0.0

    # Availability (0–6 pts)
    if signals.get("open_to_work_flag", False):
        total += 3.0

    days_inactive = _days_since(signals.get("last_active_date", ""))
    if days_inactive <= 7:
        total += 3.0
    elif days_inactive <= 30:
        total += 2.0
    elif days_inactive <= 90:
        total += 1.0

    # Recruiter engagement (0–4 pts)
    rr = signals.get("recruiter_response_rate", 0.0)
    if rr >= 0.70:
        total += 2.0
    elif rr >= 0.40:
        total += 1.0

    avg_hrs = signals.get("avg_response_time_hours", 9999)
    if avg_hrs <= 24:
        total += 2.0
    elif avg_hrs <= 72:
        total += 1.0

    # Notice period (0–3 pts)
    notice = signals.get("notice_period_days", 180)
    if notice <= NOTICE_EXCELLENT:
        total += 3.0
    elif notice <= NOTICE_GOOD:
        total += 1.5

    # Location (0–3 pts)
    location = _norm(profile.get("location", ""))
    country  = _norm(profile.get("country", ""))
    if "india" in country or country == "in":
        if any(city in location for city in PREFERRED_CITIES):
            total += 3.0
        else:
            total += 1.5  # India but non-preferred city
    elif signals.get("willing_to_relocate", False):
        total += 1.0

    # GitHub activity (0–2 pts)
    github = signals.get("github_activity_score", -1)
    if github >= 60:
        total += 2.0
    elif github >= 30:
        total += 1.0

    # Trust signals (0–2 pts)
    total += 0.5 * signals.get("verified_email", False)
    total += 0.5 * signals.get("verified_phone", False)
    total += 1.0 * signals.get("linkedin_connected", False)

    return min(20.0, total)


# ── Sub-score 4: Anti-fraud / social proof (0–15 pts) ───────────────────────

def _score_anti_fraud(candidate: dict) -> float:
    signals = candidate.get("redrob_signals", {})

    total = 0.0

    # Recruiter saves — hard to game (0–4 pts)
    saved = signals.get("saved_by_recruiters_30d", 0)
    total += min(4.0, saved * 0.5)

    # Endorsements received (0–2 pts)
    endorse = signals.get("endorsements_received", 0)
    total += min(2.0, endorse / 15)

    # Interview completion rate (0–3 pts)
    icr = signals.get("interview_completion_rate", 0.0)
    total += icr * 3.0

    # Offer acceptance rate (0–2 pts, skip if no prior offers)
    oar = signals.get("offer_acceptance_rate", -1)
    if oar >= 0:
        total += min(2.0, oar * 2.0)

    # Profile completeness (0–4 pts)
    completeness = signals.get("profile_completeness_score", 0)
    total += (completeness / 100) * 4.0

    return min(15.0, total)


# ── Main stage entry point ────────────────────────────────────────────────────

def score_candidate(candidate: dict) -> dict:
    """Compute all four heuristic sub-scores for one candidate."""
    skill     = _score_skills(candidate)
    career    = _score_career(candidate)
    behavioral = _score_behavioral(candidate)
    anti_fraud = _score_anti_fraud(candidate)

    return {
        "candidate_id":    candidate["candidate_id"],
        "skill_score":     round(skill, 2),
        "career_score":    round(career, 2),
        "behavioral_score":round(behavioral, 2),
        "anti_fraud_score":round(anti_fraud, 2),
        "heuristic_total": round(skill + career + behavioral + anti_fraud, 2),
        "_candidate":      candidate,   # keep reference for later stages
    }


def run_heuristic_scoring(candidates: list) -> list:
    """
    Stage 2 entry point.
    Returns list of score dicts sorted by heuristic_total descending.
    """
    scored = [score_candidate(c) for c in candidates]
    scored.sort(key=lambda x: x["heuristic_total"], reverse=True)
    return scored
