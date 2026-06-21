# utils/candidate_loader.py
# Efficient candidate loading — handles both .jsonl and .jsonl.gz

import gzip
import json
from typing import Iterator


def stream_candidates(path: str) -> Iterator[dict]:
    """Stream candidates one at a time — memory efficient for 100K."""
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_all_candidates(path: str) -> list:
    """Load all candidates into memory. Use stream_candidates for very large files."""
    print(f"  Reading from: {path}")
    candidates = list(stream_candidates(path))
    return candidates


def load_json_list(path: str) -> list:
    """Load from a pretty-printed JSON array (e.g. sample_candidates.json)."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_candidates_auto(path: str) -> list:
    """Auto-detect format: .jsonl, .jsonl.gz, or .json array."""
    if path.endswith(".json") and not path.endswith(".jsonl"):
        return load_json_list(path)
    return load_all_candidates(path)
