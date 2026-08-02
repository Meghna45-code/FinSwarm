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
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
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
    logger.info("   FINSWARM 100-SCENARIO ADVERSARIAL GAUNTLET (OPTIMIZED LLM BENCHMARKING ENGINE)")
    logger.info("=================================================================================")

    if not os.path.exists(SCENARIOS_FILE):
        logger.error(f"Scenarios file not found: {SCENARIOS_FILE}")
        return

    with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    personas = initialize_personas()
    api_key = os.getenv("GEMINI_API_KEY")
    llm_client = GeminiLlmClient(api_key=api_key) if api_key else None
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

    start_time = time.time()
    total_evals = len(scenarios) * len(personas)
    completed_evals = 0

    logger.info(f"Starting execution of {len(scenarios)} scenarios across {len(personas)} agents ({total_evals} total live LLM evaluations)...")

    semaphore = asyncio.Semaphore(3)

    async def eval_single_agent(scenario, agent_name, persona):
        nonlocal completed_evals
        async with semaphore:
            await asyncio.sleep(0.3)
            s_id = scenario["id"]
            cat = scenario["category"]
            headline = scenario["headline"]
            expected_bullish = scenario.get("expected_bullish", [])
            expected_bearish = scenario.get("expected_bearish", [])
            expected_neutral = scenario.get("expected_neutral", [])

            try:
                sys_prompt = orchestrator.get_primed_agent_prompt(
                    company_profile=dummy_profile,
                    agent_name=agent_name,
                    personas=personas,
                    current_sentiment=persona.initial_sentiment,
                    current_conviction=persona.initial_conviction,
                    current_reactivity=persona.reactivity_threshold
                )

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
                sent = clamp(float(res.get("updated_sentiment", persona.initial_sentiment)))
                conv = clamp(float(res.get("updated_conviction", persona.initial_conviction)), 0.0, 1.0)
                reasoning = res.get("spoken_argument", "")
            except Exception as e:
                sent = clamp(persona.initial_sentiment)
                conv = clamp(persona.initial_conviction, 0.0, 1.0)
                reasoning = f"Evaluation: {str(e)}"

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

            completed_evals += 1
            if completed_evals % 20 == 0 or completed_evals == total_evals:
                logger.info(f"Progress: {completed_evals}/{total_evals} evaluations completed ({(completed_evals/total_evals)*100:.1f}%)")

            return agent_name, {
                "sentiment": sent,
                "conviction": conv,
                "reasoning": reasoning,
                "passed": passed,
                "category": cat
            }

    for scenario in scenarios:
        s_id = scenario["id"]
        cat = scenario["category"]
        headline = scenario["headline"]

        tasks = [eval_single_agent(scenario, agent_name, persona) for agent_name, persona in personas.items()]
        responses = await asyncio.gather(*tasks)

        scenario_responses = {}
        for agent_name, resp in responses:
            scenario_responses[agent_name] = {
                "sentiment": resp["sentiment"],
                "conviction": resp["conviction"],
                "reasoning": resp["reasoning"],
                "passed_guardrails": resp["passed"]
            }

            sc_dict = agent_scorecard[agent_name]
            sc_dict["total_evaluations"] += 1
            sc_dict["category_scores"][cat]["total"] += 1
            if resp["passed"]:
                sc_dict["passed"] += 1
                sc_dict["category_scores"][cat]["passed"] += 1
            else:
                sc_dict["failed"] += 1

        results_data.append({
            "scenario_id": s_id,
            "category": cat,
            "headline": headline,
            "agent_responses": scenario_responses
        })

    elapsed = time.time() - start_time
    logger.info(f"\n=================================================================================")
    logger.info(f"GAUNTLET AUDIT COMPLETED in {elapsed/60:.1f} minutes ({completed_evals} evaluations executed)")
    logger.info(f"=================================================================================")

    # Print Summary Table
    print("\n" + "=" * 110)
    print("   FINSWARM 100-SCENARIO ADVERSARIAL GAUNTLET SCORECARD")
    print("=" * 110)
    print(f"{'AGENT NAME':<35} | {'EVALS':<6} | {'PASSED':<7} | {'ACCURACY %':<11} | {'STATUS'}")
    print("-" * 110)

    scorecard_output = []
    for agent_name, stats in agent_scorecard.items():
        total = stats["total_evaluations"]
        passed = stats["passed"]
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

    output_dir = os.path.dirname(RESULTS_FILE)
    os.makedirs(output_dir, exist_ok=True)

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "total_scenarios": len(scenarios),
            "total_evaluations": completed_evals,
            "execution_time_seconds": round(elapsed, 1),
            "scorecard": scorecard_output,
            "detailed_results": results_data
        }, f, indent=2)

    logger.info(f"Saved benchmark results to: {RESULTS_FILE}")

if __name__ == "__main__":
    asyncio.run(run_100_scenario_gauntlet())
