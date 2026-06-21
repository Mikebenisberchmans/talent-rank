# sandbox/app.py
# Streamlit demo — required for submission
# Run: streamlit run sandbox/app.py

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import streamlit as st
import pandas as pd

from pipeline.hard_filter import hard_filter
from pipeline.heuristic_scorer import run_heuristic_scoring
from pipeline.ensemble import run_ensemble
from pipeline.reasoning import generate_reasoning

st.set_page_config(page_title="Redrob AI Ranker", layout="wide")
st.title("Redrob AI Candidate Ranker")
st.caption("Upload `sample_candidates.json` to see the pipeline in action.")

uploaded = st.file_uploader("Upload candidates JSON", type=["json"])

if uploaded:
    candidates = json.load(uploaded)
    st.info(f"Loaded **{len(candidates)}** candidates")

    with st.spinner("Running pipeline (semantic stage skipped for speed)..."):
        filtered, stats = hard_filter(candidates)
        scored          = run_heuristic_scoring(filtered)
        # Skip semantic in sandbox for speed; weights still applied
        for e in scored:
            e["semantic_score"] = 0.0
        top = run_ensemble(scored, top_n=min(10, len(scored)))

    # ── Stats bar ────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total",       stats["total"])
    c2.metric("Passed",      stats["passed"])
    c3.metric("Honeypots",   stats["honeypot"])
    c4.metric("Consulting",  stats["consulting_only"])
    c5.metric("Non-NLP",     stats["non_nlp"])

    st.divider()
    st.subheader("Top Candidates")

    # ── Results table ─────────────────────────────────────────────────────────
    table_rows = []
    for entry in top:
        c = entry["_candidate"]
        p = c["profile"]
        table_rows.append({
            "Rank":      entry["rank"],
            "ID":        entry["candidate_id"],
            "Title":     p.get("current_title", ""),
            "YOE":       p.get("years_of_experience", ""),
            "Location":  p.get("location", ""),
            "Skill":     entry["skill_score"],
            "Career":    entry["career_score"],
            "Behavioral":entry["behavioral_score"],
            "Final":     entry["final_score"],
            "Reasoning": generate_reasoning(c),
        })

    df = pd.DataFrame(table_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Expandable detail cards ───────────────────────────────────────────────
    st.divider()
    st.subheader("Candidate Detail")
    for entry in top:
        c = entry["_candidate"]
        p = c["profile"]
        with st.expander(
            f"#{entry['rank']} — {p.get('current_title', 'N/A')}  "
            f"| {p.get('current_company', '')}  "
            f"| Score {entry['final_score']:.1f}"
        ):
            col1, col2, col3 = st.columns(3)
            col1.metric("Skill",      entry["skill_score"])
            col2.metric("Career",     entry["career_score"])
            col3.metric("Behavioral", entry["behavioral_score"])

            st.caption(f"**Reasoning:** {generate_reasoning(c)}")
            st.write(p.get("summary", ""))

            skills = [s["name"] for s in c.get("skills", [])]
            st.write("**Skills:** " + ", ".join(skills))
