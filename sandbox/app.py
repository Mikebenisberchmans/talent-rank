# sandbox/app.py
# Streamlit demo — required for submission
# Run: streamlit run sandbox/app.py

import sys, os, io, gzip, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd

from pipeline.hard_filter import hard_filter
from pipeline.heuristic_scorer import run_heuristic_scoring
from pipeline.semantic_scorer import run_semantic_scoring
from pipeline.ensemble import run_ensemble
from pipeline.reasoning import generate_reasoning

st.set_page_config(page_title="talent-rank", layout="wide", page_icon="🎯")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎯 talent-rank")
st.caption("AI-powered candidate ranking pipeline — upload candidates to run the full 5-stage pipeline.")

# ── File loader ───────────────────────────────────────────────────────────────
def load_candidates(uploaded_file) -> list:
    """Load candidates from .json, .jsonl, or .jsonl.gz — auto-detected."""
    name = uploaded_file.name
    raw  = uploaded_file.read()

    if name.endswith(".jsonl.gz"):
        with gzip.open(io.BytesIO(raw), "rt", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    if name.endswith(".jsonl"):
        return [
            json.loads(line)
            for line in raw.decode("utf-8").splitlines()
            if line.strip()
        ]

    # .json — plain array
    return json.loads(raw.decode("utf-8"))


uploaded = st.file_uploader(
    "Upload candidates file",
    type=["json", "jsonl", "gz"],
    help="Accepts sample_candidates.json · candidates.jsonl · candidates.jsonl.gz",
)

if not uploaded:
    st.info("Upload a candidates file above to begin.")
    st.stop()

# ── Load ──────────────────────────────────────────────────────────────────────
with st.spinner("Loading candidates…"):
    t0         = time.time()
    candidates = load_candidates(uploaded)
    load_time  = time.time() - t0

st.success(f"Loaded **{len(candidates):,}** candidates from `{uploaded.name}` in {load_time:.2f}s")

st.divider()

# ── Run pipeline ──────────────────────────────────────────────────────────────
run_btn = st.button("▶ Run full pipeline", type="primary", use_container_width=True)

if run_btn:
    progress = st.progress(0, text="Starting pipeline…")
    timings  = {}

    # Stage 1
    progress.progress(10, text="Stage 1 — Hard filters + honeypot detection…")
    t = time.time()
    filtered, stats = hard_filter(candidates)
    timings["Stage 1 — Hard filter"] = time.time() - t

    if not filtered:
        st.error("All candidates were filtered out. Check filter thresholds.")
        st.stop()

    # Stage 2
    progress.progress(30, text="Stage 2 — Heuristic scoring…")
    t = time.time()
    scored = run_heuristic_scoring(filtered)
    timings["Stage 2 — Heuristic scoring"] = time.time() - t

    # Stage 3
    progress.progress(50, text="Stage 3 — Cross-encoder semantic scoring (this takes ~45s on CPU)…")
    t = time.time()
    try:
        scored = run_semantic_scoring(scored, top_n=min(500, len(scored)))
        timings["Stage 3 — Semantic scoring"] = time.time() - t
        semantic_ran = True
    except Exception as e:
        st.warning(f"Semantic scoring skipped: {e}. Run `python setup.py` to download the model.")
        for entry in scored:
            entry["semantic_score"] = 0.0
        timings["Stage 3 — Semantic scoring"] = 0.0
        semantic_ran = False

    # Stage 4
    progress.progress(85, text="Stage 4 — Ensemble ranking…")
    t = time.time()
    top = run_ensemble(scored, top_n=min(100, len(scored)))
    timings["Stage 4 — Ensemble"] = time.time() - t

    # Stage 5
    progress.progress(95, text="Stage 5 — Reasoning generation…")
    t = time.time()
    for entry in top:
        entry["_reasoning"] = generate_reasoning(entry["_candidate"])
    timings["Stage 5 — Reasoning"] = time.time() - t

    progress.progress(100, text="Done.")

    # ── Pipeline stats ────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Pipeline summary")

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total in",      f"{stats['total']:,}")
    col2.metric("Passed filter", f"{stats['passed']:,}")
    col3.metric("Honeypots",     stats["honeypot"])
    col4.metric("Consulting",    stats["consulting_only"])
    col5.metric("Non-NLP",       stats["non_nlp"])
    col6.metric("Output",        len(top))

    # Timing breakdown
    st.subheader("Stage timings")
    timing_cols = st.columns(len(timings))
    for col, (label, secs) in zip(timing_cols, timings.items()):
        col.metric(label, f"{secs:.2f}s")

    total_time = sum(timings.values())
    st.caption(f"Total wall time: **{total_time:.2f}s** — "
               f"{'✅ well within' if total_time < 280 else '⚠️ close to'} the 5-minute competition limit.")

    if not semantic_ran:
        st.info("ℹ️ Semantic scores are 0 (model not loaded). Run `python setup.py` to enable Stage 3.")

    # ── Filter breakdown ──────────────────────────────────────────────────────
    with st.expander("Filter breakdown"):
        filter_data = {
            "Reason":         ["Honeypot", "Consulting-only", "Pure research", "Non-NLP specialist", "Recent LLM-only"],
            "Removed":        [stats["honeypot"], stats["consulting_only"], stats["pure_research"], stats["non_nlp"], stats["recent_llm_only"]],
        }
        st.dataframe(pd.DataFrame(filter_data), use_container_width=True, hide_index=True)

    # ── Results table ─────────────────────────────────────────────────────────
    st.divider()
    st.subheader(f"Top {len(top)} ranked candidates")

    rows = []
    for entry in top:
        c = entry["_candidate"]
        p = c["profile"]
        rows.append({
            "Rank":      entry["rank"],
            "ID":        entry["candidate_id"],
            "Title":     p.get("current_title", ""),
            "YOE":       p.get("years_of_experience", ""),
            "Location":  p.get("location", ""),
            "Skill":     entry["skill_score"],
            "Career":    entry["career_score"],
            "Behavioral":entry["behavioral_score"],
            "Semantic":  entry["semantic_score"],
            "Final ▼":   entry["final_score"],
            "Reasoning": entry["_reasoning"],
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ── CSV download ──────────────────────────────────────────────────────────
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇ Download submission.csv",
        data=csv_bytes,
        file_name="submission.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # ── Candidate detail cards ────────────────────────────────────────────────
    st.divider()
    st.subheader("Candidate detail")

    for entry in top:
        c = entry["_candidate"]
        p = c["profile"]
        signals = c.get("redrob_signals", {})

        with st.expander(
            f"#{entry['rank']}  {p.get('current_title', 'N/A')}  "
            f"·  {p.get('current_company', '')}  "
            f"·  Final score {entry['final_score']:.1f}"
        ):
            # Score breakdown
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            sc1.metric("Skill",      entry["skill_score"])
            sc2.metric("Career",     entry["career_score"])
            sc3.metric("Behavioral", entry["behavioral_score"])
            sc4.metric("Semantic",   entry["semantic_score"])
            sc5.metric("Final",      entry["final_score"])

            st.caption(f"**Reasoning:** {entry['_reasoning']}")

            # Key signals
            sig1, sig2, sig3, sig4 = st.columns(4)
            sig1.markdown(f"**Open to work:** {'✅' if signals.get('open_to_work_flag') else '❌'}")
            sig2.markdown(f"**Notice period:** {signals.get('notice_period_days', 'N/A')} days")
            sig3.markdown(f"**Response rate:** {signals.get('recruiter_response_rate', 'N/A')}")
            sig4.markdown(f"**GitHub score:** {signals.get('github_activity_score', 'N/A')}")

            st.write(p.get("summary", ""))

            skills = [s["name"] for s in c.get("skills", [])]
            st.write("**Skills:** " + ", ".join(skills))