# main.py
# Redrob AI Candidate Ranker — full pipeline orchestrator
#
# Usage:
#   python main.py candidates.jsonl.gz
#   python main.py sample_candidates.json --output my_submission.csv
#   python main.py candidates.jsonl.gz --skip-semantic   (fast dev run)

import argparse
import csv
import sys
import time

from utils.candidate_loader import load_candidates_auto
from pipeline.hard_filter import hard_filter
from pipeline.heuristic_scorer import run_heuristic_scoring
from pipeline.semantic_scorer import run_semantic_scoring
from pipeline.ensemble import run_ensemble
from pipeline.reasoning import generate_reasoning
from config.jd_config import SEMANTIC_TOP_N, FINAL_TOP_N


def _banner(msg: str) -> None:
    print(f"\n{'─'*60}")
    print(f"  {msg}")
    print(f"{'─'*60}")


def run_pipeline(
    candidates_path: str,
    output_path: str = "submission.csv",
    skip_semantic: bool = False,
    semantic_top_n: int = SEMANTIC_TOP_N,
    final_top_n: int = FINAL_TOP_N,
) -> list:

    wall_start = time.time()

    # ── Load ─────────────────────────────────────────────────────────────────
    _banner("Loading candidates")
    t = time.time()
    candidates = load_candidates_auto(candidates_path)
    print(f"  Loaded {len(candidates):,} candidates  ({time.time()-t:.1f}s)")

    # ── Stage 1 ───────────────────────────────────────────────────────────────
    _banner("Stage 1 — Hard filters + honeypot detection")
    t = time.time()
    filtered, stats = hard_filter(candidates)
    print(f"  Passed :        {stats['passed']:>7,}")
    print(f"  Honeypots :     {stats['honeypot']:>7,}")
    print(f"  Consulting :    {stats['consulting_only']:>7,}")
    print(f"  Pure research : {stats['pure_research']:>7,}")
    print(f"  Non-NLP :       {stats['non_nlp']:>7,}")
    print(f"  Recent LLM :    {stats['recent_llm_only']:>7,}")
    print(f"  Time: {time.time()-t:.1f}s")

    if not filtered:
        print("ERROR: All candidates filtered out. Check filter thresholds.")
        sys.exit(1)

    # ── Stage 2 ───────────────────────────────────────────────────────────────
    _banner("Stage 2 — Heuristic scoring")
    t = time.time()
    scored = run_heuristic_scoring(filtered)
    top_entry = scored[0]
    print(f"  Scored {len(scored):,} candidates")
    print(f"  Top heuristic score : {top_entry['heuristic_total']:.1f}")
    print(f"  Top candidate       : {top_entry['candidate_id']}")
    print(f"  Time: {time.time()-t:.1f}s")

    # ── Stage 3 ───────────────────────────────────────────────────────────────
    if skip_semantic:
        _banner("Stage 3 — Semantic scoring SKIPPED (--skip-semantic)")
        for entry in scored:
            entry["semantic_score"] = 0.0
    else:
        _banner(f"Stage 3 — Semantic scoring (top {semantic_top_n})")
        t = time.time()
        scored = run_semantic_scoring(scored, top_n=semantic_top_n)
        print(f"  Time: {time.time()-t:.1f}s")

    # ── Stage 4 ───────────────────────────────────────────────────────────────
    _banner(f"Stage 4 — Ensemble + final top {final_top_n}")
    t = time.time()
    top = run_ensemble(scored, top_n=final_top_n)
    print(f"  #1  {top[0]['candidate_id']}  score={top[0]['final_score']:.2f}")
    print(f"  #50 {top[49]['candidate_id']}  score={top[49]['final_score']:.2f}"
          if len(top) >= 50 else "")
    print(f"  Time: {time.time()-t:.1f}s")

    # ── Stage 5 ───────────────────────────────────────────────────────────────
    _banner("Stage 5 — Reasoning generation")
    rows = []
    for entry in top:
        c = entry["_candidate"]
        rows.append({

            "candidate_id":     entry["candidate_id"],
            "rank":             entry["rank"],
            "score":      entry["final_score"],
            "reasoning":        generate_reasoning(c),
            })

    # ── Write CSV ─────────────────────────────────────────────────────────────
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    total = time.time() - wall_start
    _banner(f"Done — {output_path}")
    print(f"  Total wall time : {total:.1f}s")
    print(f"  Candidates in   : {len(candidates):,}")
    print(f"  Candidates out  : {len(rows)}")
    return rows


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Redrob AI Candidate Ranker",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("candidates",
                        help="Path to candidates.jsonl, .jsonl.gz, or sample .json")
    parser.add_argument("--output",         default="submission.csv")
    parser.add_argument("--skip-semantic",  action="store_true",
                        help="Skip cross-encoder (fast dev runs)")
    parser.add_argument("--semantic-top-n", type=int, default=SEMANTIC_TOP_N)
    parser.add_argument("--final-top-n",    type=int, default=FINAL_TOP_N)
    args = parser.parse_args()

    run_pipeline(
        candidates_path = args.candidates,
        output_path     = args.output,
        skip_semantic   = args.skip_semantic,
        semantic_top_n  = args.semantic_top_n,
        final_top_n     = args.final_top_n,
    )
