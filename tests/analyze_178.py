import json

with open("backend/tests/gauntlet_benchmark_results.json", "r", encoding="utf-8") as f:
    d = json.load(f)

api_failures = []
for res in d["detailed_results"]:
    s_id = res["scenario_id"]
    cat = res["category"]
    headline = res["headline"]
    for agent, data in res["agent_responses"].items():
        reason = data.get("reasoning", "")
        if not data["passed_guardrails"] and ("429" in reason or "Fallback" in reason or "quota" in reason.lower()):
            api_failures.append({
                "scenario_id": s_id,
                "category": cat,
                "agent": agent,
                "headline": headline
            })

print(f"Total Throttled Calls Identified: {len(api_failures)}\n")

# Group by category
by_cat = {}
for item in api_failures:
    by_cat.setdefault(item["category"], []).append(item)

for cat, items in by_cat.items():
    print(f"=== {cat} ({len(items)} Throttled Calls) ===")
    for it in items:
        print(f"  • Scenario #{it['scenario_id']}: [{it['agent']}] -> \"{it['headline'][:65]}...\"")
    print()

# Group by agent
by_agent = {}
for item in api_failures:
    by_agent.setdefault(item["agent"], []).append(item)

print("\n" + "="*80)
print("SUMMARY BY AGENT:")
for agent, items in sorted(by_agent.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  - {agent}: {len(items)} throttled calls")
