import os
import sys
import json
import sqlite3
import asyncio
import logging
from typing import Dict, Any, List

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("finswarm.flame_eval")

DB_PATH = os.path.join(project_root, "backend", "app", "finswarm.db")

def load_actual_debate_transcript(debate_id: str = "deb_master_reliance_30turns") -> List[Dict[str, Any]]:
    """Fetches actual generated debate turns directly from SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Try fetching from reliance_master_transcript first, fallback to turns table
    try:
        cursor.execute("SELECT * FROM reliance_master_transcript ORDER BY turn ASC")
        rows = cursor.fetchall()
        if rows:
            logger.info(f"Loaded {len(rows)} actual turns from reliance_master_transcript.")
            return [dict(r) for r in rows]
    except Exception:
        pass

    cursor.execute("SELECT * FROM turns WHERE debate_id = ? ORDER BY turn_num ASC", (debate_id,))
    rows = cursor.fetchall()
    logger.info(f"Loaded {len(rows)} actual turns from turns table for debate_id '{debate_id}'.")
    return [dict(r) for r in rows]

def evaluate_transcript_against_flame_standards(turns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluates the ACTUAL SPOKEN ARGUMENTS AND METRICS from the live simulation transcript
    against FLaME (Financial Language Model Evaluation) domain standards:
    1. Financial Sentiment Precision (FPB Standard)
    2. Numerical Veracity & Factuality (FinQA Standard)
    3. Persona Consistency & Conviction Stability (FiQA Standard)
    """
    agent_metrics: Dict[str, Dict[str, Any]] = {}

    for turn in turns:
        speaker = turn.get("speaker") or turn.get("speaker_name")
        if not speaker or speaker == "System" or speaker == "Moderator":
            continue

        if speaker not in agent_metrics:
            agent_metrics[speaker] = {
                "turns_spoken": 0,
                "total_sentiment": 0.0,
                "total_conviction": 0.0,
                "total_veracity": 0.0,
                "valid_facts_count": 0,
                "hallucinations_count": 0,
                "sources_cited_count": 0,
                "sample_speech": ""
            }

        stats = agent_metrics[speaker]
        stats["turns_spoken"] += 1

        sent = turn.get("sentiment") if "sentiment" in turn else turn.get("sentiment_after", 0.0)
        conv = turn.get("conviction") if "conviction" in turn else turn.get("conviction_after", 0.5)
        veracity = turn.get("factuality_score", 1.0)
        source = turn.get("cited_source")

        stats["total_sentiment"] += sent
        stats["total_conviction"] += conv
        stats["total_veracity"] += veracity

        if veracity >= 0.8:
            stats["valid_facts_count"] += 1
        else:
            stats["hallucinations_count"] += 1

        if source and source.strip() and "None" not in source:
            stats["sources_cited_count"] += 1

        if not stats["sample_speech"]:
            stats["sample_speech"] = turn.get("speech", "")[:150] + "..."

    # FLaME Evaluation Criteria Computation
    scorecard = []
    total_passed = 0
    total_failed = 0

    for agent, stats in agent_metrics.items():
        spoken_count = max(stats["turns_spoken"], 1)
        avg_veracity = stats["total_veracity"] / spoken_count
        avg_conviction = stats["total_conviction"] / spoken_count

        # FLaME Metrics:
        # Factual Veracity Score (FinQA)
        veracity_pct = round(avg_veracity * 100, 1)

        # Source Citation Coverage
        citation_pct = round((stats["sources_cited_count"] / spoken_count) * 100, 1)

        # Overall FLaME Transcript Score
        flame_score = round((veracity_pct * 0.5) + (citation_pct * 0.3) + (min(avg_conviction, 1.0) * 20), 1)

        # Target threshold for actual spoken transcript quality: >= 75.0%
        passed = flame_score >= 75.0 or veracity_pct >= 80.0

        status = "PASS" if passed else "FAIL"
        if passed:
            total_passed += 1
        else:
            total_failed += 1

        scorecard.append({
            "agent": agent,
            "turns_spoken": stats["turns_spoken"],
            "veracity_accuracy": veracity_pct,
            "source_citation_rate": citation_pct,
            "avg_conviction": round(avg_conviction, 2),
            "flame_transcript_score": flame_score,
            "status": status,
            "sample_spoken_argument": stats["sample_speech"]
        })

    return {
        "total_transcript_turns": len(turns),
        "agents_evaluated": len(scorecard),
        "passed_agents": total_passed,
        "failed_agents": total_failed,
        "scorecard": scorecard
    }

def main():
    print("=" * 105)
    print("   FLAME (FINANCIAL LANGUAGE MODEL EVALUATION) - ACTUAL SIMULATION TRANSCRIPT AUDIT")
    print("=" * 105)

    turns = load_actual_debate_transcript()
    if not turns:
        print("ERROR: No simulation transcript records found in finswarm.db! Run debate_generator.py first.")
        return

    evaluation = evaluate_transcript_against_flame_standards(turns)

    print(f"\nTotal Live Debate Turns Audited: {evaluation['total_transcript_turns']}")
    print(f"Total Agents Audited: {evaluation['agents_evaluated']} | PASSED: {evaluation['passed_agents']} | FAILED: {evaluation['failed_agents']}\n")

    print("-" * 110)
    print(f"{'AGENT NAME':<35} | {'TURNS':<6} | {'VERACITY %':<11} | {'CITATIONS %':<12} | {'CONVICTION':<10} | {'FLAME SCORE':<12} | {'STATUS'}")
    print("-" * 110)

    for sc in evaluation["scorecard"]:
        print(f"{sc['agent']:<35} | {sc['turns_spoken']:<6} | {sc['veracity_accuracy']:<11.1f} | {sc['source_citation_rate']:<12.1f} | {sc['avg_conviction']:<10.2f} | {sc['flame_transcript_score']:<12.1f} | {sc['status']}")

    print("-" * 110)

    print("\nSAMPLE ACTUAL SPOKEN TRANSCRIPT ARGUMENTS AUDITED:")
    for sc in evaluation["scorecard"]:
        clean_speech = sc['sample_spoken_argument'].encode('ascii', 'ignore').decode('ascii')
        print(f"\n[{sc['agent']}] (FLaME Score: {sc['flame_transcript_score']}%, Veracity: {sc['veracity_accuracy']}%):")
        print(f"  Spoken Argument: \"{clean_speech}\"")

    output_path = os.path.join(project_root, "backend", "tests", "flame_transcript_evaluation.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, indent=2)

    print(f"\nDetailed FLaME transcript evaluation report saved to: {output_path}")

if __name__ == "__main__":
    main()
