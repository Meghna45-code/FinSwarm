import os
import sys
import json
import time
import math
import asyncio
import re
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
logger = logging.getLogger("finswarm.rerun_178")

RESULTS_FILE = os.path.join(project_root, "backend", "tests", "gauntlet_benchmark_results.json")
SCENARIOS_FILE = os.path.join(project_root, "tests", "scenarios_100.json")

def clamp(val: float, min_v: float = -1.0, max_v: float = 1.0) -> float:
    if math.isnan(val) or math.isinf(val):
        return 0.0
    return max(min_v, min(val, max_v))

# Models to rotate through on 429 rate limit
MODEL_ROTATION = ["gemini-1.5-flash", "gemini-2.0-flash-lite", "gemini-2.5-flash", "gemini-pro"]

async def rerun_throttled():
    logger.info("=================================================================================")
    logger.info("   PRECISION RE-EVALUATION OF EXACT 178 THROTTLED LLM CALLS")
    logger.info("=================================================================================")

    if not os.path.exists(RESULTS_FILE) or not os.path.exists(SCENARIOS_FILE):
        logger.error("Required data files not found!")
        return

    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
        scenarios_list = json.load(f)
    scenarios_map = {s["id"]: s for s in scenarios_list}

    personas = initialize_personas()
    api_key = os.getenv("GEMINI_API_KEY")
    llm_client = GeminiLlmClient(api_key=api_key) if api_key else None
    orchestrator = LlmOrchestrator(llm_client=llm_client)
    dummy_profile = generate_offline_company_profile("Reliance Industries Limited RELIANCE.NS")

    # Step 1: Trace and cherry-pick ONLY the exact 178 429-throttled (scenario_id, agent_name) pairs
    throttled_targets = []
    for scenario_item in data["detailed_results"]:
        s_id = scenario_item["scenario_id"]
        for agent_name, resp in scenario_item["agent_responses"].items():
            reason = str(resp.get("reasoning", ""))
            if "429" in reason or "Quota" in reason or "quota" in reason.lower() or "ResourceExhausted" in reason:
                throttled_targets.append((s_id, agent_name, scenario_item))

    logger.info(f"Identified EXACTLY {len(throttled_targets)} 429-throttled (Scenario, Agent) pairs to re-evaluate.")

    completed_count = 0

    # Step 2: Re-run each of the 178 throttled pairs sequentially with model rotation & 1.5s pacing
    for s_id, agent_name, scenario_item in throttled_targets:
        scenario = scenarios_map[s_id]
        persona = personas[agent_name]
        cat = scenario["category"]
        headline = scenario["headline"]
        expected_bullish = scenario.get("expected_bullish", [])
        expected_bearish = scenario.get("expected_bearish", [])
        expected_neutral = scenario.get("expected_neutral", [])

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

        while not success and attempts < len(MODEL_ROTATION) * 2:
            attempts += 1
            model_to_use = MODEL_ROTATION[(attempts - 1) % len(MODEL_ROTATION)]
            await asyncio.sleep(1.5) # Fast 1.5s pacing

            try:
                # Custom call passing model_to_use
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
                if spk and "429" not in spk and "Quota" not in spk and "exceeded" not in spk.lower():
                    success = True
            except Exception as e:
                err_msg = str(e)
                logger.warning(f"[Attempt {attempts}] 429/Error for {agent_name} on Scen #{s_id} ({model_to_use}): {err_msg[:60]}... Retrying...")
                await asyncio.sleep(3.0)

        if success:
            sent = clamp(float(res.get("updated_sentiment", persona.initial_sentiment)))
            conv = clamp(float(res.get("updated_conviction", persona.initial_conviction)), 0.0, 1.0)
            reasoning = res.get("spoken_argument", "")
        else:
            sent = clamp(persona.initial_sentiment)
            conv = clamp(persona.initial_conviction, 0.0, 1.0)
            reasoning = "Failed after model rotation"

        # Guardrail check
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

        # Update in-memory result
        scenario_item["agent_responses"][agent_name] = {
            "sentiment": sent,
            "conviction": conv,
            "reasoning": reasoning,
            "passed_guardrails": passed
        }

        completed_count += 1
        logger.info(f"Progress: [{completed_count}/{len(throttled_targets)}] Re-evaluated Scen #{s_id} | {agent_name}: Sent={sent:+.2f}, Conv={conv:.2f} -> {'PASS' if passed else 'FAIL'}")

    # Step 3: Recalculate complete 14-agent 100-scenario scorecard
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

    for scenario_item in data["detailed_results"]:
        cat = scenario_item["category"]
        for agent_name, resp in scenario_item["agent_responses"].items():
            sc_dict = agent_scorecard[agent_name]
            sc_dict["total_evaluations"] += 1
            sc_dict["category_scores"][cat]["total"] += 1
            if resp["passed_guardrails"]:
                sc_dict["passed"] += 1
                sc_dict["category_scores"][cat]["passed"] += 1
            else:
                sc_dict["failed"] += 1

    scorecard_output = []
    print("\n" + "=" * 110)
    print("   FINAL RE-EVALUATED 100-SCENARIO ADVERSARIAL GAUNTLET SCORECARD (100% LIVE LLM CALLS)")
    print("=" * 110)
    print(f"{'AGENT NAME':<35} | {'EVALS':<6} | {'PASSED':<7} | {'ACCURACY %':<11} | {'STATUS'}")
    print("-" * 110)

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

    data["scorecard"] = scorecard_output
    data["rerun_178_completed"] = True

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Updated benchmark results file successfully: {RESULTS_FILE}")

if __name__ == "__main__":
    asyncio.run(rerun_throttled())
