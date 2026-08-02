import asyncio
import json
import time
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

from backend.app.services.personas import initialize_personas
from backend.app.services.llm_client import GeminiLlmClient
from backend.app.services.llm_orchestrator import LlmOrchestrator
from backend.app.services.mock_fallbacks import generate_offline_company_profile

async def test_scen1():
    personas = initialize_personas()
    client = GeminiLlmClient()
    orchestrator = LlmOrchestrator(client)
    profile = generate_offline_company_profile("Reliance Industries Limited RELIANCE.NS")
    
    start = time.time()
    count = 0
    for name, p in personas.items():
        sys_prompt = orchestrator.get_primed_agent_prompt(
            company_profile=profile,
            agent_name=name,
            personas=personas
        )
        
        success = False
        attempts = 0
        while not success:
            attempts += 1
            try:
                res = await orchestrator.generate_agent_argument(
                    system_prompt=sys_prompt,
                    news_content="Company revenues up 25% year-over-year.",
                    news_sentiment=0.0,
                    news_impact=0.8,
                    agent_sentiment=p.initial_sentiment,
                    agent_conviction=p.initial_conviction,
                    reactivity_threshold=p.reactivity_threshold,
                    debate_history=[]
                )
                success = True
                count += 1
                print(f"[{count}/14] {name:<35}: sent={res['updated_sentiment']:+.2f}, conv={res['updated_conviction']:.2f} (Attempt #{attempts})")
            except Exception as e:
                err = str(e)
                print(f"   [Quota/RateLimit] Retrying for {name} in 15s... Error: {err[:60]}")
                await asyncio.sleep(15.0)
                
        await asyncio.sleep(2.5) # Pace to stay under 15-30 RPM
        
    print(f"\nSuccessfully executed all 14 LIVE API calls in {time.time()-start:.2f} seconds!")

if __name__ == "__main__":
    asyncio.run(test_scen1())
