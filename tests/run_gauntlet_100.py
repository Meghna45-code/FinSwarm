import os
import sys
import json
import time
import math
import asyncio
import logging
from typing import Dict, Any, List

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
env_path = os.path.join(project_root, ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip("\"'")

from backend.app.services.personas import initialize_personas
from backend.app.services.llm_client import GeminiLlmClient
from backend.app.services.llm_orchestrator import LlmOrchestrator
from backend.app.services.mock_fallbacks import generate_offline_company_profile

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("finswarm.gauntlet")

SCENARIOS_FILE = os.path.join(project_root, "tests", "scenarios_100.json")
RESULTS_FILE = os.path.join(project_root, "backend", "tests", "gauntlet_benchmark_results.json")

def clamp(val: float, min_v: float = -1.0, max_v: float = 1.0) -> float:
    if math.isnan(val) or math.isinf(val):
        return 0.0
    return max(min_v, min(val, max_v))

async def run_100_scenario_gauntlet():
    logger.info("=================================================================================")
    logger.info("   FINSWARM 100-SCENARIO ADVERSARIAL GAUNTLET (100% REAL LIVE API CALL ENGINE)")
    logger.info("=================================================================================")

    if not os.path.exists(SCENARIOS_FILE):
        logger.error(f"Scenarios file not found: {SCENARIOS_FILE}")
        return

    with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    personas = initialize_personas()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required for live API stress test.")
        
    llm_client = GeminiLlmClient(api_key=api_key)
    orchestrator = LlmOrchestrator(llm_client=llm_client)

    dummy_profile = generate_offline_company_profile("Reliance Industries Limited RELIANCE.NS")

    results_data = []
    agent_scorecard: Dict[str, Dict[str, Any]] = {
        name: {
            "total_evaluations": 0,
            "passed": 0,
            "failed": 0,
            "category_scores": {
                "Fundamental Traps": {"passed": 0, "total": 0},
                "Hype vs. Reality Tests": {"passed": 0, "total": 0},
                "Macro Shocks": {"passed": 0, "total": 0},
                "Technical vs. Legal Conflicts": {"passed": 0, "total": 0},
                "Pure Noise Baselines": {"passed": 0, "total": 0}
            }
        } for name in personas.keys()
    }

    # Load existing results if resuming
    completed_scenario_ids = set()
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                prev_data = json.load(f)
                if isinstance(prev_data, dict) and "detailed_results" in prev_data:
                    results_data = prev_data["detailed_results"]
                    for item in results_data:
                        completed_scenario_ids.add(item["scenario_id"])
                        cat = item["category"]
                        for agent_name, resp in item["agent_responses"].items():
                            if agent_name in agent_scorecard:
                                sc = agent_scorecard[agent_name]
                                sc["total_evaluations"] += 1
                                sc["category_scores"][cat]["total"] += 1
                                if resp.get("passed_guardrails"):
                                    sc["passed"] += 1
                                    sc["category_scores"][cat]["passed"] += 1
                                else:
                                    sc["failed"] += 1
                    logger.info(f"Resuming gauntlet: Loaded {len(completed_scenario_ids)} previously completed scenarios.")
        except Exception as e:
            logger.warning(f"Could not load previous results file ({e}). Starting fresh.")

    start_time = time.time()
    total_evals = len(scenarios) * len(personas)
    successful_live_api_calls = len(completed_scenario_ids) * len(personas)

    logger.info(f"Target: {len(scenarios)} scenarios across {len(personas)} agents ({total_evals} total LIVE LLM evaluations)...")

    for scenario_idx, scenario in enumerate(scenarios, 1):
        s_id = scenario["id"]
        cat = scenario["category"]
        headline = scenario["headline"]

        if s_id in completed_scenario_ids:
            continue

        expected_bullish = scenario.get("expected_bullish", [])
        expected_bearish = scenario.get("expected_bearish", [])
        expected_neutral = scenario.get("expected_neutral", [])

        scenario_responses = {}

        for agent_name, persona in personas.items():
            sys_prompt = orchestrator.get_primed_agent_prompt(
                company_profile=dummy_profile,
                agent_name=agent_name,
                personas=personas,
                current_sentiment=persona.initial_sentiment,
                current_conviction=persona.initial_conviction,
                current_reactivity=persona.reactivity_threshold
            )

            success = False
            attempts = 0
            res = {}

            while not success:
                attempts += 1
                try:
                    res = await orchestrator.generate_agent_argument(
                        system_prompt=sys_prompt,
                        news_content=headline,
                        news_sentiment=0.0,
                        news_impact=0.8,
                        agent_sentiment=persona.initial_sentiment,
                        agent_conviction=persona.initial_conviction,
                        reactivity_threshold=persona.reactivity_threshold,
                        debate_history=[]
                    )

                    spk = str(res.get("spoken_argument", ""))
                    if "429" in spk or "Quota" in spk or "ResourceExhausted" in spk or "quota" in spk.lower():
                        raise ValueError(f"Quota error returned: {spk}")

                    success = True
                    successful_live_api_calls += 1
                except Exception as e:
                    err_msg = str(e)
                    backoff = 15.0 if ("429" in err_msg or "Quota" in err_msg or "ResourceExhausted" in err_msg) else 5.0
                    logger.warning(f"[Attempt #{attempts}] Quota/Rate limit pause for {agent_name} (Scen #{s_id}): sleeping {backoff:.0f}s...")
                    await asyncio.sleep(backoff)

            sent = clamp(float(res.get("updated_sentiment", persona.initial_sentiment)))
            conv = clamp(float(res.get("updated_conviction", persona.initial_conviction)), 0.0, 1.0)
            reasoning = res.get("spoken_argument", "")

            # Guardrail compliance check
            if cat == "Pure Noise Baselines":
                if agent_name in expected_neutral:
                    passed = abs(sent) <= 0.35
                else:
                    passed = True
            elif agent_name in expected_bullish:
                passed = sent >= 0.15
            elif agent_name in expected_bearish:
                passed = sent <= -0.15
            else:
                passed = True

            scenario_responses[agent_name] = {
                "sentiment": sent,
                "conviction": conv,
                "reasoning": reasoning,
                "passed_guardrails": passed
            }

            sc_dict = agent_scorecard[agent_name]
            sc_dict["total_evaluations"] += 1
            sc_dict["category_scores"][cat]["total"] += 1
            if passed:
                sc_dict["passed"] += 1
                sc_dict["category_scores"][cat]["passed"] += 1
            else:
                sc_dict["failed"] += 1

            # Pacing between agent calls to respect 15 RPM free tier limits
            await asyncio.sleep(2.0)

        results_data.append({
            "scenario_id": s_id,
            "category": cat,
            "headline": headline,
            "agent_responses": scenario_responses
        })

        completed_scenario_ids.add(s_id)
        current_completed_evals = len(results_data) * len(personas)

        # Save checkpoint to disk after EVERY scenario
        output_dir = os.path.dirname(RESULTS_FILE)
        os.makedirs(output_dir, exist_ok=True)
        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "total_scenarios": len(scenarios),
                "total_evaluations": current_completed_evals,
                "successful_live_api_calls": successful_live_api_calls,
                "detailed_results": results_data
            }, f, indent=2)

        pct = (len(completed_scenario_ids) / len(scenarios)) * 100
        logger.info(f"Progress: [{len(completed_scenario_ids)}/{len(scenarios)}] Scenarios Completed ({pct:.1f}%) | Successful Live API Calls: {successful_live_api_calls}/{total_evals}")

    elapsed = time.time() - start_time
    logger.info(f"\n=================================================================================")
    logger.info(f"GAUNTLET AUDIT COMPLETED in {elapsed/60:.1f} minutes ({successful_live_api_calls} Successful Live API Calls)")
    logger.info(f"=================================================================================")

    # Print Summary Table
    print("\n" + "=" * 110)
    print("   FINSWARM 100-SCENARIO ADVERSARIAL GAUNTLET SCORECARD (100% LIVE LLM API CALLS)")
    print("=" * 110)
    print(f"{'AGENT NAME':<35} | {'EVALS':<6} | {'PASSED':<7} | {'ACCURACY %':<11} | {'STATUS'}")
    print("-" * 110)

    scorecard_output = []
    total_passed_all = 0
    total_evals_all = 0

    for agent_name, stats in agent_scorecard.items():
        total = stats["total_evaluations"]
        passed = stats["passed"]
        total_passed_all += passed
        total_evals_all += total
        acc = round((passed / total) * 100, 1) if total > 0 else 0.0
        status = "PASS" if acc >= 75.0 else "FAIL"

        print(f"{agent_name:<35} | {total:<6} | {passed:<7} | {acc:<11.1f} | {status}")

        scorecard_output.append({
            "agent": agent_name,
            "total_evaluations": total,
            "passed": passed,
            "accuracy_pct": acc,
            "status": status,
            "category_breakdown": stats["category_scores"]
        })

    print("-" * 110)
    overall_accuracy = round((total_passed_all / total_evals_all) * 100, 1) if total_evals_all > 0 else 0.0
    print(f"TOTAL SYSTEM PERFORMANCE: {total_passed_all}/{total_evals_all} PASSED ({overall_accuracy}%) across {successful_live_api_calls}/{total_evals} LIVE API CALLS")
    print("=" * 110 + "\n")

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "total_scenarios": len(scenarios),
            "total_evaluations": total_evals_all,
            "successful_live_api_calls": successful_live_api_calls,
            "overall_accuracy_pct": overall_accuracy,
            "execution_time_seconds": round(elapsed, 1),
            "scorecard": scorecard_output,
            "detailed_results": results_data
        }, f, indent=2)

    logger.info(f"Saved final benchmark results to: {RESULTS_FILE}")

if __name__ == "__main__":
    asyncio.run(run_100_scenario_gauntlet())
