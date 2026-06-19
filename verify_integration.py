import asyncio
import os
from backend.app.services.personas import CompanyProfile, initialize_personas
from backend.app.services.moderator import ModeratorAgent
from backend.app.services.llm_orchestrator import LlmOrchestrator
from backend.app.services.state_manager import StateManager
from backend.app.services.debate_room import DebateRoom
from backend.app.services.llm_client import GeminiLlmClient

async def main():
    # Load env manually
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(current_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip("\"'")

    profile = CompanyProfile(
        ticker="TSLA",
        name="Tesla Inc",
        sector="Consumer Cyclical",
        industry="Auto Manufacturers",
        description="Electric vehicle and clean energy company.",
        key_metrics={"Revenue": "$96B", "Free Cash Flow": "$4.3B"},
        historical_news=[
            {"date": "2026-01-15", "title": "Earnings Beat", "summary": "Tesla exceeded Q4 earnings expectations."}
        ],
        recent_events=["Model Y Refresh launched in North America."]
    )

    api_key = os.getenv("GEMINI_API_KEY")
    llm_client = None
    if api_key:
        print("GEMINI_API_KEY detected in environment. Instantiating GeminiLlmClient...")
        llm_client = GeminiLlmClient(api_key=api_key)
    else:
        print("GEMINI_API_KEY not set in environment. Running simulation with offline mocks...")

    # Load static personas dictionary
    personas = initialize_personas()

    room_c = LlmOrchestrator(llm_client=llm_client)
    room_d = StateManager(personas=personas)
    moderator = ModeratorAgent(profile, room_c)
    room_b = DebateRoom(
        company_profile=profile, 
        personas=personas, 
        moderator=moderator, 
        room_c=room_c, 
        room_d=room_d
    )

    print("Integration verification successful: Modules A, B, C, and D imported and instantiated!")
    print(f"Loaded {len(room_b.agents)} debate agents.")

    print("\n--- Initial States (4 Dynamic Variables) ---")
    for agent_name in ["Brand Loyalist / Fanboy", "Brand Skeptic", "Technical Day Trader"]:
         print(f"{agent_name}: {room_d.get_agent_state(agent_name)}")

    news = "Tesla faces potential tariff challenges under new trade policies, creating uncertainty for international deliveries."
    print(f"\nProcessing News: {news}")
    
    result = await room_b.run_simulation(news, max_rounds=3)
    print("\n--- Mock Simulation Runs Perfectly (Queue-Based turn scheduling) ---")
    print(f"Sentiment: {result['news_analysis']['sentiment']}")
    print(f"Impact: {result['news_analysis']['impact']}")
    print(f"Transcript turns logged: {len(result['transcript'])}")

    print("\nTurn Progression:")
    for turn in result['transcript']:
        print(f"Turn {turn['turn']}: {turn['speaker']} spoke.")
        print(f"  Speech: {turn['speech'][:80]}...")
        print(f"  Sentiment after: {turn['sentiment_after']}, Conviction after: {turn['conviction_after']}")

    print("\n--- Final States (4 Dynamic Variables) ---")
    for agent_name in ["Brand Loyalist / Fanboy", "Brand Skeptic", "Technical Day Trader"]:
         print(f"{agent_name}: {room_d.get_agent_state(agent_name)}")

    print("\n--- Final Debate Summary ---")
    print(result["debate_summary"])

if __name__ == "__main__":
    asyncio.run(main())
