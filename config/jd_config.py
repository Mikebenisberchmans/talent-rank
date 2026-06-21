# config/jd_config.py
# All tunable parameters for the Senior AI Engineer JD
# Change weights here, not in pipeline code

# ── Ensemble weights (must sum to 1.0) ──────────────────────────────────────
ENSEMBLE_WEIGHTS = {
    "skill":      0.35,
    "career":     0.25,
    "behavioral": 0.20,
    "semantic":   0.20,
}

# ── Pipeline throughput ──────────────────────────────────────────────────────
SEMANTIC_TOP_N = 500   # candidates sent to cross-encoder
FINAL_TOP_N    = 100   # final submission size

# ── Experience range (from JD) ───────────────────────────────────────────────
YOE_IDEAL_MIN = 5
YOE_IDEAL_MAX = 9

# ── Location preferences (from JD) ───────────────────────────────────────────
PREFERRED_CITIES = [
    "pune", "noida", "hyderabad", "mumbai", "delhi",
    "ncr", "gurgaon", "gurugram", "bengaluru", "bangalore", "chennai"
]

# ── Notice period thresholds (days) ─────────────────────────────────────────
NOTICE_EXCELLENT = 30
NOTICE_GOOD      = 60
NOTICE_MAX       = 90

# ── Salary range for role (INR LPA) ─────────────────────────────────────────
SALARY_EXPECTED_MIN = 15
SALARY_EXPECTED_MAX = 50

# ── Semantic model (CPU-compatible, no network at rank time) ─────────────────
SEMANTIC_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# ── JD text fed to cross-encoder ─────────────────────────────────────────────
JD_TEXT = """
Senior AI Engineer — Founding Team at Redrob AI (Series A startup).

Core mandate: own the intelligence layer — candidate-JD ranking, retrieval,
and matching systems. Ship a v2 ranker in weeks 4-8 using embeddings,
hybrid retrieval, and LLM-based re-ranking. Set up evaluation infrastructure
(NDCG, MRR, MAP, A/B testing, recruiter feedback loops).

Must have:
- Production embeddings-based retrieval (sentence-transformers, BGE, E5,
  OpenAI embeddings, bi-encoders). Handled embedding drift, index refresh,
  retrieval-quality regression in production.
- Production vector database or hybrid search (Pinecone, Weaviate, Qdrant,
  Milvus, OpenSearch, Elasticsearch, FAISS). Operational experience required.
- Strong Python. Code quality matters.
- Evaluation frameworks for ranking systems: NDCG, MRR, MAP,
  offline-to-online correlation, A/B test interpretation.
- 5-9 years, applied ML in production. Startup scrappy attitude.

Nice to have: LLM fine-tuning (LoRA, QLoRA, PEFT), learning-to-rank
(XGBoost, neural LTR), HR-tech or marketplace, distributed systems.

Not a fit: pure research without production, LangChain-only under 12 months,
consulting-only careers, computer vision/speech without NLP/IR, title-chasers.
"""
