# config/disqualifiers.py
# Hard-coded JD disqualifier rules — sourced directly from the JD text

CONSULTING_COMPANIES = {
    "tcs", "tata consultancy services", "infosys", "wipro",
    "accenture", "cognizant", "capgemini", "hcl", "hcl technologies",
    "tech mahindra", "mphasis", "hexaware", "l&t infotech",
    "ltimindtree", "mindtree", "persistent systems", "niit technologies",
}

# Domains that are a hard no unless paired with NLP/IR signals
NON_NLP_DOMAINS = [
    "computer vision", "image classification", "object detection",
    "image segmentation", "video understanding", "optical character",
    "speech recognition", "speech synthesis", "asr", "text to speech",
    "tts", "robotics", "autonomous driving", "self-driving",
    "lidar", "slam", "pose estimation",
]

# NLP/IR signals that redeem an otherwise non-NLP candidate
NLP_REDEMPTION_KEYWORDS = [
    "nlp", "natural language", "information retrieval", "text retrieval",
    "semantic search", "embedding", "retrieval", "ranking", "recommendation",
    "search engine", "ir system", "question answering", "text classification",
]

# Research-only title patterns (block if ENTIRE career is these)
RESEARCH_ONLY_TITLES = [
    "research scientist", "research engineer", "ml researcher",
    "ai researcher", "research intern", "phd researcher",
    "postdoctoral", "postdoc", "research associate",
]

# Production deployment signals (redeem a research-heavy profile)
PRODUCTION_SIGNALS = [
    "production", "deployed", "serving", "real users", "user-facing",
    "latency", "throughput", "scaled to", "shipped", "launched",
    "live system", "a/b test", "online evaluation",
]
