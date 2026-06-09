import json
import re
import math
import random
from typing import Dict, Any
from .personas import CompanyProfile, AgentPersona

def generate_offline_company_profile(news_content: str) -> CompanyProfile:
    """Offline mock fallback for company profile generation."""
    content_lower = news_content.lower()
    if "apple" in content_lower or "aapl" in content_lower or "iphone" in content_lower:
        return CompanyProfile(
            ticker="AAPL",
            name="Apple Inc",
            sector="Technology",
            industry="Consumer Electronics",
            description="Consumer electronics, software, and services company.",
            key_metrics={"Revenue": "$383B", "Free Cash Flow": "$99.5B", "Stock Price": "$180.00", "Gross Margin": "44%"},
            historical_news=[
                {"date": "2023-09-12", "title": "iPhone 15 Launch", "summary": "Apple announced the iPhone 15 with USB-C ports."},
                {"date": "2024-02-02", "title": "Vision Pro Launch", "summary": "Apple released its spatial computing headset in the US."}
            ],
            recent_events=["Apple Intelligence AI features announced.", "WWDC keynote unveils iOS updates."],
            one_sentence_facts=[
                "Apple was founded in a garage by Steve Jobs, Steve Wozniak, and Ronald Wayne in 1976.",
                "Apple's first computer, the Apple I, sold for $666.66 because Wozniak liked repeating digits.",
                "Apple has more cash on hand than the US Treasury at various times in history.",
                "The company name was inspired by Steve Jobs' visit to an apple orchard while on a fruitarian diet.",
                "Apple's App Store was launched in 2008 with only 500 apps available.",
                "The iPhone was originally code-named 'Project Purple' and developed in complete secrecy.",
                "Apple's market capitalization was the first in the world to cross $1 trillion, $2 trillion, and $3 trillion.",
                "Steve Jobs was ousted from Apple in 1985 but returned in 1997 when Apple bought his company NeXT.",
                "Every iPhone advertisement shows the time 9:41 AM, which was when Steve Jobs first unveiled the iPhone in 2007.",
                "Apple's logo originally featured Sir Isaac Newton sitting under an apple tree.",
                "The Macintosh computer was named after a popular type of apple, the McIntosh.",
                "Apple launched the iPod in 2001 with the slogan '1,000 songs in your pocket'.",
                "Apple sold 340,000 iPhones per day in 2018.",
                "Steve Wozniak sold his scientific calculator to help raise funds for Apple's initial founding.",
                "Apple’s circular headquarters, Apple Park, is powered entirely by 100% renewable energy.",
                "The retail Apple Store in New York (Fifth Avenue) is one of the most photographed landmarks in the world.",
                "Apple is the largest taxpayer in the world, paying billions in corporate taxes annually.",
                "Siri was originally an independent iOS app before Apple acquired the company in 2010.",
                "Apple's iPad was originally conceived before the iPhone, but the iPhone was prioritized and launched first.",
                "Steve Jobs sold all but one share of Apple stock when he was forced out of the company in 1985."
            ]
        )
    elif "nvidia" in content_lower or "nvda" in content_lower or "gpu" in content_lower or "blackwell" in content_lower:
        return CompanyProfile(
            ticker="NVDA",
            name="NVIDIA Corporation",
            sector="Technology",
            industry="Semiconductors",
            description="Pioneer of GPU-accelerated computing, AI hardware, and chip design.",
            key_metrics={"Revenue": "$60.9B", "Free Cash Flow": "$27B", "Stock Price": "$950.00", "Gross Margin": "76%"},
            historical_news=[
                {"date": "2024-03-18", "title": "Blackwell GPU Announced", "summary": "NVIDIA unveiled its next-generation Blackwell architecture."},
                {"date": "2023-05-24", "title": "Trillion Dollar Club", "summary": "NVIDIA stock surged on massive AI chip demand."}
            ],
            recent_events=["H100 GPUs shipment expansion.", "Partnerships announced with key cloud providers."],
            one_sentence_facts=[
                "NVIDIA was founded in 1993 by Jen-Hsun Huang, Chris Malachowsky, and Curtis Priem at a Denny's diner in San Jose.",
                "The name NVIDIA comes from 'invidia', the Latin word for envy.",
                "NVIDIA's first product was the NV1, a multimedia PCI card released in 1995.",
                "NVIDIA popularized the term GPU (Graphics Processing Unit) with the launch of the GeForce 256 in 1999.",
                "NVIDIA's CUDA architecture, released in 2006, enabled GPUs to be used for general-purpose computing.",
                "Co-founder and CEO Jensen Huang is famous for wearing a signature black leather jacket at public appearances.",
                "NVIDIA's chip architecture Blackwell is named after David Blackwell, the famous mathematician and statistician.",
                "NVIDIA's chips power the world's fastest supercomputers, including Frontier and Aurora.",
                "NVIDIA acquired Mellanox Technologies for $6.9 billion in 2020 to build high-performance data center networking.",
                "NVIDIA's DLSS technology uses deep learning to upscale low-resolution images in video games in real-time.",
                "NVIDIA's market cap surged past $2 trillion in 2024, driven by the massive global demand for generative AI hardware.",
                "The company was originally funded with only $40,000 of starting capital.",
                "NVIDIA's headquarters in Santa Clara, California features massive geodesic domes.",
                "NVIDIA's DRIVE platform is a software-defined end-to-end platform for autonomous vehicles.",
                "The company developed the first custom GPU for Microsoft's original Xbox console in 2000.",
                "Jensen Huang's first job was washing dishes at a Denny's restaurant when he was 15.",
                "NVIDIA was added to the S&P 500 index in 2001.",
                "NVIDIA's hardware is crucial for training large language models like GPT-4 and Gemini.",
                "The company's employees are colloquially referred to as 'NVIDIANs'.",
                "NVIDIA co-founder Curtis Priem designed the first graphics processor for IBM PC compatibles in 1982."
            ]
        )
    else:
        # Default Tesla profile
        return CompanyProfile(
            ticker="TSLA",
            name="Tesla Inc",
            sector="Consumer Cyclical",
            industry="Auto Manufacturers",
            description="Electric vehicle and clean energy company.",
            key_metrics={"Revenue": "$96B", "Free Cash Flow": "$4.3B", "Stock Price": "$175.00", "Operating Margin": "9.2%"},
            historical_news=[
                {"date": "2026-01-15", "title": "Earnings Beat", "summary": "Tesla exceeded Q4 earnings expectations."}
            ],
            recent_events=["Model Y Refresh launched in North America."],
            one_sentence_facts=[
                "Tesla is named after Nikola Tesla, the famous electrical engineer and inventor.",
                "Tesla open-sourced all of its patents in 2014 to accelerate the world's transition to sustainable energy.",
                "The Tesla Model S features a medical-grade HEPA filter named 'Bioweapon Defense Mode'.",
                "Tesla's first car was the Roadster, which was launched in 2008 and based on a Lotus Elise chassis.",
                "In 2018, Elon Musk launched his midnight cherry Tesla Roadster into space on a Falcon Heavy rocket.",
                "Tesla was not founded by Elon Musk; it was founded by Martin Eberhard and Marc Tarpenning in 2003.",
                "The Tesla Model S has a glass roof that can withstand the weight of two full-grown elephants.",
                "Tesla's Gigafactory Shanghai was built and delivered its first cars in under 12 months.",
                "The Tesla Cybertruck uses custom ultra-hard cold-rolled stainless steel developed for SpaceX rockets.",
                "Tesla's Autopilot system is named after the autopilot software used in airplanes.",
                "Tesla's Model Y became the best-selling vehicle of any kind globally in 2023.",
                "Tesla does not spend money on traditional paid advertising campaigns, relying on organic buzz.",
                "The Model S, 3, X, and Y models spell out 'S3XY' (using 3 instead of E due to trademark conflicts).",
                "Tesla's Gigafactory Texas is one of the largest factories in the world by volume.",
                "Tesla manufactures its own battery cells, such as the 4680 cylindrical cells.",
                "The Tesla Supercharger network is the largest DC fast-charging network in the world.",
                "Tesla's Full Self-Driving (FSD) beta system has driven hundreds of millions of miles.",
                "Tesla's home battery system, the Powerwall, can run a home off solar energy overnight.",
                "Tesla was added to the S&P 500 index in December 2020 after multiple consecutive profitable quarters.",
                "Tesla’s humanoid robot, Optimus, uses the same computer vision system as Tesla’s cars."
            ]
        )

def offline_contextualize_personas(environmental_variables: Dict[str, str], default_personas: Dict[str, AgentPersona]) -> Dict[str, Any]:
    """Offline fallback to adjust agent parameters based on active variables."""
    adjusted = {name: p.__dict__.copy() for name, p in default_personas.items()}
    
    ceo = environmental_variables.get("CEO Status", "")
    rates = environmental_variables.get("Interest Rates", "")
    supply = environmental_variables.get("Supply Chain Status", "") or environmental_variables.get("Supply Chain", "")
    regulatory = environmental_variables.get("Regulatory Pressure", "")
    competitor = environmental_variables.get("Competitor Threat", "")
    market = environmental_variables.get("Market Sentiment", "")
    labor = environmental_variables.get("Labor Relations", "")
    custom = environmental_variables.get("Custom Scenario", "")

    # Convert values to floats/ints for numeric checking
    try:
        rates_val = float(rates) if rates not in ["Steady", ""] else 0.0
    except (TypeError, ValueError):
        rates_val = 1.0 if "hike" in str(rates).lower() or "1.0%" in str(rates).lower() else 0.0

    try:
        supply_val = float(supply) if supply not in ["Healthy", ""] else 0.0
    except (TypeError, ValueError):
        supply_val = 100.0 if "shortage" in str(supply).lower() or "severe" in str(supply).lower() else 0.0

    try:
        regulatory_val = float(regulatory) if regulatory not in ["Compliant", ""] else 0.0
    except (TypeError, ValueError):
        regulatory_val = 100.0 if "antitrust" in str(regulatory).lower() or "investigation" in str(regulatory).lower() else 0.0

    try:
        competitor_val = float(competitor) if competitor not in ["Steady", ""] else 0.0
    except (TypeError, ValueError):
        competitor_val = 100.0 if "competitor" in str(competitor).lower() or "cheaper" in str(competitor).lower() or "30%" in str(competitor).lower() else 0.0

    try:
        market_val = float(market) if market not in ["Neutral", ""] else 0.0
    except (TypeError, ValueError):
        market_val = 100.0 if "recession" in str(market).lower() or "panic" in str(market).lower() else 0.0

    try:
        labor_val = float(labor) if labor not in ["Stable", ""] else 0.0
    except (TypeError, ValueError):
        labor_val = 100.0 if "strike" in str(labor).lower() or "labor" in str(labor).lower() else 0.0

    # Apply deterministic adjustments
    if "resigns" in str(ceo).lower() or "scandal" in str(ceo).lower():
        # CEO Scandal
        for name, p in adjusted.items():
            if name in ["Brand Loyalist / Fanboy", "Company Insider / Employee", "Panic-Prone Retail Trader"]:
                p["initial_sentiment"] = max(-1.0, p["initial_sentiment"] - 0.4)
                p["initial_conviction"] = max(0.1, p["initial_conviction"] - 0.2)
            elif name in ["Aggressive Short-Seller", "Brand Skeptic"]:
                p["initial_sentiment"] = -0.9
                p["initial_conviction"] = 0.95
                p["reactivity_threshold"] = 0.1

    if rates_val != 0.0:
        # Rates Hiked
        for name, p in adjusted.items():
            if name in ["Macro Economist", "Institutional Value Investor", "Dividend Growth Investor"]:
                p["initial_sentiment"] = max(-1.0, p["initial_sentiment"] - 0.3 * rates_val)
                p["initial_conviction"] = min(1.0, p["initial_conviction"] + 0.1 * abs(rates_val))

    if supply_val > 0.0:
        # Supply shortage
        fraction = supply_val / 100.0
        for name, p in adjusted.items():
            if name in ["B2B Supply Chain Partner / Vanguard", "Industry Tech Expert", "Company Insider / Employee"]:
                p["initial_sentiment"] = max(-1.0, p["initial_sentiment"] - 0.4 * fraction)
                p["initial_conviction"] = min(1.0, p["initial_conviction"] + 0.1 * fraction)

    if regulatory_val > 0.0:
        # Regulatory investigation
        fraction = regulatory_val / 100.0
        for name, p in adjusted.items():
            if name in ["Regulatory Compliance Watchdog", "Institutional Value Investor"]:
                p["initial_sentiment"] = max(-1.0, p["initial_sentiment"] - 0.3 * fraction)
                p["initial_conviction"] = min(1.0, p["initial_conviction"] + 0.1 * fraction)

    if competitor_val > 0.0:
        # Competitor Threat
        fraction = competitor_val / 100.0
        for name, p in adjusted.items():
            if name in ["Brand Skeptic", "Technical Day Trader", "Aggressive Short-Seller"]:
                p["initial_sentiment"] = max(-1.0, p["initial_sentiment"] - 0.2 * fraction)
            elif name in ["Brand Loyalist / Fanboy"]:
                p["initial_sentiment"] = max(-1.0, p["initial_sentiment"] - 0.1 * fraction)
                p["initial_conviction"] = max(0.1, p["initial_conviction"] - 0.1 * fraction)

    if market_val > 0.0:
        # Global recession
        fraction = market_val / 100.0
        for name, p in adjusted.items():
            if name in ["Panic-Prone Retail Trader", "Technical Day Trader"]:
                p["initial_sentiment"] = max(-1.0, p["initial_sentiment"] - 0.9 * fraction)
                p["initial_conviction"] = min(1.0, p["initial_conviction"] + 0.6 * fraction)
            elif name in ["Macro Economist", "Aggressive Short-Seller"]:
                p["initial_sentiment"] = max(-1.0, p["initial_sentiment"] - 0.4 * fraction)

    if labor_val > 0.0:
        # Nationwide employee strike
        fraction = labor_val / 100.0
        for name, p in adjusted.items():
            if name in ["Company Insider / Employee", "ESG Specialist", "B2B Supply Chain Partner / Vanguard"]:
                p["initial_sentiment"] = max(-1.0, p["initial_sentiment"] - 0.9 * fraction)
                p["initial_conviction"] = min(1.0, p["initial_conviction"] + 0.25 * fraction)

    if custom:
        # Custom negative scenarios
        if any(term in custom.lower() for term in ["fire", "explosion", "disaster", "fail", "ban"]):
            for name, p in adjusted.items():
                p["initial_sentiment"] = max(-1.0, p["initial_sentiment"] - 0.2)
                p["initial_conviction"] = max(0.1, p["initial_conviction"] - 0.1)

    # Standard round off
    for p in adjusted.values():
        p["initial_sentiment"] = round(p["initial_sentiment"], 3)
        p["initial_conviction"] = round(p["initial_conviction"], 3)
        p["reactivity_threshold"] = round(p["reactivity_threshold"], 3)
        
    return adjusted

def offline_process_swarm_command(command: str, current_agents: Dict[str, Any]) -> Dict[str, Any]:
    """Simple regex/string match offline command processor."""
    updated = {k: v.copy() if isinstance(v, dict) else v.__dict__.copy() for k, v in current_agents.items()}
    cmd_lower = command.lower()

    # 1. Check for Removal commands
    if "remove" in cmd_lower or "delete" in cmd_lower:
        removed_any = False
        for name in list(updated.keys()):
            if name.lower() in cmd_lower:
                del updated[name]
                removed_any = True
        
        if not removed_any:
            for name in list(updated.keys()):
                for word in name.lower().split():
                    if len(word) > 3 and word in cmd_lower:
                        del updated[name]
                        removed_any = True
                        break

    # 2. Check for "make everyone bearish" or "make everyone bullish"
    elif "make everyone bullish" in cmd_lower or "all bullish" in cmd_lower:
        for p in updated.values():
            p["initial_sentiment"] = 0.8
            p["initial_conviction"] = 0.85
    elif "make everyone bearish" in cmd_lower or "all bearish" in cmd_lower:
        for p in updated.values():
            p["initial_sentiment"] = -0.8
            p["initial_conviction"] = 0.85
    elif "make everyone neutral" in cmd_lower or "all neutral" in cmd_lower:
        for p in updated.values():
            p["initial_sentiment"] = 0.0
            p["initial_conviction"] = 0.5

    # 3. Check for specific sentiment changes
    else:
        matched_agent = None
        for name in updated.keys():
            if name.lower() in cmd_lower:
                matched_agent = name
                break

        if matched_agent:
            nums = re.findall(r'-?\d+(?:\.\d+)?', cmd_lower)
            if nums:
                val = float(nums[0])
                if "sentiment" in cmd_lower:
                    updated[matched_agent]["initial_sentiment"] = max(-1.0, min(1.0, val))
                elif "conviction" in cmd_lower:
                    updated[matched_agent]["initial_conviction"] = max(0.0, min(1.0, val))
                elif "reactivity" in cmd_lower:
                    updated[matched_agent]["reactivity_threshold"] = max(0.0, min(1.0, val))

    # 4. Check for adding
    if "add" in cmd_lower:
        name_match = re.search(r'named\s+([a-zA-Z0-9_\s\-]+?)(?:\s+who|\s+with|\s+to|$)', cmd_lower)
        if not name_match:
            name_match = re.search(r'add\s+(?:a\s+)?(?:new\s+)?([a-zA-Z0-9_\s\-]+?)(?:\s+who|\s+named|\s+with|\s+to|$)', cmd_lower)
        
        if name_match:
            candidate_name = name_match.group(1).strip().title()
            exclude_words = ["agent", "persona", "day trader", "investor", "retailer", "short", "bull", "bear", "analyst"]
            clean_name = " ".join([w for w in candidate_name.split() if w.lower() not in exclude_words]).strip()
            if not clean_name:
                clean_name = "Custom Persona"

            if clean_name not in updated:
                sent = 0.7 if "bull" in cmd_lower or "optimistic" in cmd_lower else (-0.7 if "bear" in cmd_lower or "pessimistic" in cmd_lower else 0.0)
                updated[clean_name] = {
                    "name": clean_name,
                    "swarm_type": "Trading & Analytical Swarm" if "analyst" in cmd_lower or "quant" in cmd_lower else "Retail & Consumer Swarm",
                    "role_identity": f"Custom agent {clean_name} added on conversational basis.",
                    "primary_metrics": ["Stock Price", "Sentiment dynamics"],
                    "cognitive_biases": ["Confirmation Bias"],
                    "linguistic_style": "Informal and direct.",
                    "good_news_reaction": "Favorable.",
                    "bad_news_reaction": "Unfavorable.",
                    "initial_sentiment": sent,
                    "initial_conviction": 0.6,
                    "reactivity_threshold": 0.25
                }

    return updated
