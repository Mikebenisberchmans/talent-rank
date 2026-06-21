# config/skill_taxonomy.py
# Skill groups with keyword lists for matching against
# both the skills[] array and career_history[].description text

SKILL_GROUPS = {
    # ── MUST HAVE (high points) ──────────────────────────────────────────────

    "embeddings_retrieval": {
        "label": "Embeddings / dense retrieval",
        "must_have": True,
        "max_points": 10,
        "skill_keywords": [
            "sentence-transformer", "sentence transformer", "sentencetransformer",
            "bge", "e5-", "ada-002", "text-embedding", "openai embedding",
            "dense retrieval", "bi-encoder", "semantic search", "embedding model",
            "faiss", "annoy", "hnswlib", "colbert", "dpr", "hybrid search",
            "sparse-dense", "bm25+", "dual encoder",
        ],
        "description_keywords": [
            "embedding", "semantic search", "dense retrieval", "vector search",
            "sentence transformer", "bi-encoder", "faiss", "retrieval system",
            "hybrid retrieval", "bm25", "approximate nearest neighbor",
            "vector index", "semantic similarity", "cosine similarity retrieval",
        ],
    },

    "vector_db": {
        "label": "Vector database / hybrid search infra",
        "must_have": True,
        "max_points": 10,
        "skill_keywords": [
            "pinecone", "weaviate", "qdrant", "milvus", "opensearch",
            "elasticsearch", "faiss", "chroma", "pgvector", "vespa",
            "redis vector", "turbopuffer", "lancedb",
        ],
        "description_keywords": [
            "pinecone", "weaviate", "qdrant", "milvus", "vector database",
            "vector store", "opensearch", "elasticsearch", "faiss",
            "vector search infrastructure", "chroma", "pgvector",
        ],
    },

    "python": {
        "label": "Python",
        "must_have": True,
        "max_points": 8,
        "skill_keywords": ["python"],
        "description_keywords": [
            "python", "pyspark", "pytorch", "tensorflow", "numpy",
            "pandas", "scikit-learn", "sklearn",
        ],
    },

    "eval_frameworks": {
        "label": "Ranking evaluation (NDCG / MRR / MAP)",
        "must_have": True,
        "max_points": 12,
        "skill_keywords": [
            "ndcg", "mrr", "map", "mean average precision",
            "mean reciprocal rank", "a/b testing", "ranking evaluation",
            "retrieval evaluation", "recall@k", "precision@k",
            "normalized discounted",
        ],
        "description_keywords": [
            "ndcg", "mrr", "mean reciprocal rank", "mean average precision",
            "a/b test", "offline evaluation", "online evaluation",
            "ranking metric", "retrieval metric", "eval framework",
            "evaluation pipeline", "relevance judgment", "recall@",
            "precision@", "hit rate", "map@",
        ],
    },

    # ── NICE TO HAVE (lower points) ──────────────────────────────────────────

    "llm_finetuning": {
        "label": "LLM fine-tuning (LoRA / QLoRA / PEFT)",
        "must_have": False,
        "max_points": 3,
        "skill_keywords": [
            "lora", "qlora", "peft", "fine-tuning", "finetuning", "sft",
            "rlhf", "instruction tuning", "dpo", "rlaif",
        ],
        "description_keywords": [
            "fine-tun", "finetuning", "lora", "qlora", "peft", "rlhf",
            "instruction tuning", "supervised fine", "sft", "dpo",
        ],
    },

    "learning_to_rank": {
        "label": "Learning to rank (LTR)",
        "must_have": False,
        "max_points": 3,
        "skill_keywords": [
            "learning to rank", "ltr", "lambdarank", "ranknet",
            "lambdamart", "listwise", "xgboost rank", "lightgbm rank",
        ],
        "description_keywords": [
            "learning to rank", "ltr", "lambdarank", "ranknet",
            "lambdamart", "pairwise ranking", "listwise ranking",
        ],
    },

    "llm_systems": {
        "label": "LLM pipelines / RAG / re-ranking",
        "must_have": False,
        "max_points": 2,
        "skill_keywords": [
            "rag", "retrieval augmented generation", "re-ranking", "reranking",
            "cross-encoder", "llm", "gpt", "llama", "mistral",
        ],
        "description_keywords": [
            "rag", "retrieval augmented", "re-rank", "rerank",
            "cross-encoder", "llm pipeline", "generative retrieval",
        ],
    },

    "mlops": {
        "label": "MLOps / model serving",
        "must_have": False,
        "max_points": 2,
        "skill_keywords": [
            "mlflow", "wandb", "weights & biases", "ray", "triton",
            "onnx", "torchserve", "kubeflow", "bentoml",
        ],
        "description_keywords": [
            "model serving", "inference optimization", "mlops",
            "model deployment", "feature store", "model monitoring",
        ],
    },
}

# AI skill keywords used for reasoning line
AI_SKILL_KEYWORDS = [
    "python", "pytorch", "tensorflow", "scikit", "nlp", "embedding",
    "vector", "transformer", "bert", "llm", "rag", "retrieval",
    "ranking", "faiss", "pinecone", "weaviate", "qdrant", "milvus",
    "sentence", "xgboost", "ndcg", "mlflow", "wandb", "ray", "lora",
    "peft", "langchain", "openai", "hugging", "elasticsearch",
    "opensearch", "colbert", "dpr", "rerank", "ltr",
]
