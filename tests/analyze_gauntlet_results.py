import json
import os

results_path = r"c:\Users\HP\OneDrive\Desktop\FinSwarm\backend\tests\gauntlet_benchmark_results.json"

with open(results_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total Scenarios: {data.get('total_scenarios')}")
print(f"Total Evaluations: {data.get('total_evaluations')}")
print(f"Successful Live API Calls: {data.get('successful_live_api_calls')}")
print(f"Overall Accuracy %: {data.get('overall_accuracy_pct')}%\n")

# Scorecard summary
print("--- INDIVIDUAL AGENT SCORECARD ---")
for sc in data["scorecard"]:
    agent = sc["agent"]
    passed = sc["passed"]
    total = sc["total_evaluations"]
    acc = sc["accuracy_pct"]
    status = sc["status"]
    print(f"{agent:<38} | {passed}/{total} ({acc:.1f}%) | {status}")

# Category Breakdown
cat_stats = {}
for sc in data["scorecard"]:
    for cat_name, cat_data in sc["category_breakdown"].items():
        if cat_name not in cat_stats:
            cat_stats[cat_name] = {"passed": 0, "total": 0}
        cat_stats[cat_name]["passed"] += cat_data["passed"]
        cat_stats[cat_name]["total"] += cat_data["total"]

print("\n--- CATEGORY ACCURACY BREAKDOWN ---")
for cat_name, cat_data in cat_stats.items():
    p = cat_data["passed"]
    t = cat_data["total"]
    pct = (p / t) * 100 if t > 0 else 0.0
    print(f"{cat_name:<35} | {p}/{t} ({pct:.1f}%)")

# Swarm Breakdown
swarms = {
    "Analytical Swarm": [
        "Algorithmic Quantitative Trader",
        "Institutional Value Investor",
        "Macro Economist",
        "Regulatory Compliance Watchdog",
        "Industry Tech Expert",
        "ESG Specialist"
    ],
    "Structural Swarm": [
        "Dividend Growth Investor",
        "B2B Supply Chain Partner / Vanguard",
        "Company Insider / Employee"
    ],
    "Behavioral & Retail Swarm": [
        "Brand Loyalist / Fanboy",
        "Brand Skeptic",
        "Aggressive Short-Seller",
        "Technical Day Trader",
        "Panic-Prone Retail Trader"
    ]
}

agent_acc_map = {sc["agent"]: sc["accuracy_pct"] for sc in data["scorecard"]}

print("\n--- SWARM PERFORMANCE VS HARNESS BENCHMARK TARGETS ---")
harness_targets = {
    "Analytical Swarm": {"target_min": 75.0, "target_max": 100.0},
    "Structural Swarm": {"target_min": 65.0, "target_max": 100.0},
    "Behavioral & Retail Swarm": {"target_min": 45.0, "target_max": 100.0}
}

for swarm_name, agent_list in swarms.items():
    accs = [agent_acc_map[a] for a in agent_list if a in agent_acc_map]
    avg_acc = sum(accs) / len(accs) if accs else 0.0
    t_min = harness_targets[swarm_name]["target_min"]
    status = "EXCEEDED TARGET" if avg_acc >= t_min else "BELOW TARGET"
    print(f"{swarm_name:<28} | Average Accuracy: {avg_acc:.1f}% | Harness Target: >={t_min}% | {status}")
    for a in agent_list:
        print(f"  - {a:<35}: {agent_acc_map.get(a, 0.0):.1f}%")
