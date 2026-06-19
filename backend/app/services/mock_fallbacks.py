import json
import re
import math
import random
from typing import Dict, Any
from .personas import CompanyProfile, AgentPersona

def generate_offline_company_profile(news_content: str) -> CompanyProfile:
    """Offline mock fallback for company profile generation.
    Supports major companies by keyword matching. Falls back to a generic
    named profile so it never incorrectly defaults to Tesla.
    """
    content_lower = news_content.lower()

    # ---- Apple ----
    if any(k in content_lower for k in ["apple", "aapl", "iphone", "ipad", "macbook", "macos"]):
        return CompanyProfile(
            ticker="AAPL", name="Apple Inc",
            sector="Technology", industry="Consumer Electronics",
            description="Consumer electronics, software, and services company.",
            key_metrics={"Revenue": "$383B", "Free Cash Flow": "$99.5B", "Stock Price": "$180.00", "Gross Margin": "44%", "R&D Spend": "$29.9B"},
            historical_news=[
                {"date": "2015-04-24", "title": "Apple Watch Released", "summary": "Apple officially entered the wearables market with the launch of the Apple Watch series."},
                {"date": "2018-08-02", "title": "$1 Trillion Cap reached", "summary": "Apple became the first public US company to cross the $1 trillion valuation milestone."},
                {"date": "2020-11-10", "title": "Apple M1 Silicon Launch", "summary": "Apple announced custom ARM-based Apple Silicon architecture, phasing out Intel processors."},
                {"date": "2023-09-12", "title": "iPhone 15 Launch", "summary": "Apple announced the iPhone 15 with titanium frames and USB-C ports."},
                {"date": "2024-02-02", "title": "Vision Pro Launch", "summary": "Apple officially released its Apple Vision Pro spatial computing headset in the US."}
            ],
            recent_events=[
                "Apple Intelligence AI features announced across ecosystem.",
                "WWDC keynote unveils iOS layout improvements and system updates.",
                "EU DMA compliance: enabling third-party app marketplaces in Europe.",
                "Strategic partnerships with global carriers for satellite SOS connectivity.",
                "Supply chain updates focusing on 100% carbon neutral production targets."
            ],
            recent_news=[
                {"date": "2025-09-15", "title": "iPhone 17 and Pro models unveiled", "summary": "Apple unveiled the iPhone 17 lineup with enhanced neural processors for local AI workloads."},
                {"date": "2025-11-05", "title": "Advanced Health Patents Approved", "summary": "Apple was granted patents for non-invasive glucose monitoring sensors in future wearables."},
                {"date": "2026-02-14", "title": "Services Segment Revenue Record", "summary": "Apple Services division reached an all-time high quarterly revenue of $26B, up 12% YoY."},
                {"date": "2026-04-20", "title": "Renewable Supply Chain Update", "summary": "Apple reports that 95% of direct manufacturing partners have committed to 100% clean energy."},
                {"date": "2026-06-12", "title": "Siri Advanced LLM integration", "summary": "Initial developer betas showcase next-generation Siri with deep contextual reasoning."}
            ],
            one_sentence_facts=[
                "Apple was founded in a garage by Steve Jobs, Steve Wozniak, and Ronald Wayne in 1976.",
                "Apple's market capitalization was the first in the world to cross $1 trillion, $2 trillion, and $3 trillion.",
                "Every iPhone advertisement shows the time 9:41 AM, which was when Steve Jobs first unveiled the iPhone.",
                "Apple's App Store was launched in 2008 with only 500 apps available.",
                "The iPhone was originally code-named 'Project Purple' and developed in complete secrecy."
            ]
        )

    # ---- NVIDIA ----
    elif any(k in content_lower for k in ["nvidia", "nvda", "gpu", "blackwell", "cuda", "h100", "geforce"]):
        return CompanyProfile(
            ticker="NVDA", name="NVIDIA Corporation",
            sector="Technology", industry="Semiconductors",
            description="Pioneer of GPU-accelerated computing, AI hardware, and chip design.",
            key_metrics={"Revenue": "$60.9B", "Free Cash Flow": "$27B", "Stock Price": "$950.00", "Gross Margin": "76%"},
            historical_news=[
                {"date": "2006-11-08", "title": "CUDA Architecture Launch", "summary": "NVIDIA introduced CUDA, allowing general-purpose computing on GPUs."},
                {"date": "2018-08-20", "title": "RTX Real-time Ray Tracing", "summary": "NVIDIA introduced GeForce RTX series based on the Turing GPU architecture."},
                {"date": "2022-03-22", "title": "Hopper H100 GPU Debut", "summary": "NVIDIA announced the H100 Tensor Core GPU, setting new AI training records."},
                {"date": "2023-05-24", "title": "Trillion Dollar Club", "summary": "NVIDIA stock surged past $1T valuation on massive global generative AI demand."},
                {"date": "2024-03-18", "title": "Blackwell GPU Architecture", "summary": "NVIDIA unveiled its next-generation Blackwell architecture for multi-trillion parameter LLMs."}
            ],
            recent_events=[
                "H100 and H200 GPUs shipment volume expansion.",
                "Strategic cloud partnerships for AI enterprise software infrastructure.",
                "Unveiling custom chip design initiatives for hyperscaler platforms.",
                "Developing Sovereign AI cloud platforms for global governmental agencies.",
                "Expanding autonomous driving platform partnerships with major EV automakers."
            ],
            recent_news=[
                {"date": "2025-10-18", "title": "Blackwell B200 Volume Shipments", "summary": "NVIDIA started high-volume shipments of Blackwell B200 platforms to cloud clients."},
                {"date": "2025-12-05", "title": "NVIDIA AI Enterprise Update", "summary": "NVIDIA released NIM microservices, boosting corporate software suite adoption by 40%."},
                {"date": "2026-02-22", "title": "Record Data Center Earnings", "summary": "NVIDIA data center division posted a record quarterly revenue of $22.6B, up 150% YoY."},
                {"date": "2026-04-10", "title": "Custom Chip Design Unit launch", "summary": "NVIDIA launched a new business unit focused on designing custom silicon for gaming and automotive."},
                {"date": "2026-06-05", "title": "Rubin Next-Gen Architecture", "summary": "CEO Jensen Huang teased the Rubin GPU architecture scheduled for launch in 2026."}
            ],
            one_sentence_facts=[
                "NVIDIA was founded in 1993 by Jen-Hsun Huang at a Denny's diner in San Jose.",
                "NVIDIA popularized the term GPU with the launch of the GeForce 256 in 1999.",
                "NVIDIA's market cap surged past $2 trillion in 2024, driven by massive global AI demand.",
                "NVIDIA's CUDA architecture, released in 2006, enabled GPUs for general-purpose computing.",
                "Jensen Huang is famous for wearing a signature black leather jacket at public appearances."
            ]
        )

    # ---- Google / Alphabet ----
    elif any(k in content_lower for k in ["google", "alphabet", "goog", "googl", "gemini", "youtube", "android", "pixel", "waymo", "deepmind"]):
        return CompanyProfile(
            ticker="GOOGL", name="Alphabet Inc (Google)",
            sector="Technology", industry="Internet Content & Information",
            description="Global leader in internet search, advertising, cloud computing, and AI.",
            key_metrics={"Revenue": "$307B", "Free Cash Flow": "$69B", "Stock Price": "$175.00", "Gross Margin": "57%"},
            historical_news=[
                {"date": "2004-08-19", "title": "Google Initial Public Offering", "summary": "Google went public at $85 per share under ticker GOOG."},
                {"date": "2015-08-10", "title": "Alphabet Restructuring", "summary": "Google reorganized under parent company Alphabet Inc. to separate core search from other bets."},
                {"date": "2020-12-10", "title": "AlphaFold 2 Breakthrough", "summary": "Google DeepMind's AlphaFold model solved the 50-year-old protein folding challenge."},
                {"date": "2023-12-06", "title": "Gemini AI Launch", "summary": "Google introduced Gemini, its most capable native multimodal foundation model."},
                {"date": "2024-05-14", "title": "Google I/O 2024", "summary": "Google unveiled Gemini 1.5 Pro and new AI Overviews in Search features."}
            ],
            recent_events=[
                "Gemini AI integration across all Google Workspace, Android, and Search products.",
                "Waymo robotaxi commercial ride-hailing expansion to San Francisco and Los Angeles.",
                "Google Cloud business reaching sustained profitability and accelerating market share.",
                "Global antitrust scrutiny regarding search defaults and digital advertising market power.",
                "Expanding custom TPU (Tensor Processing Unit) design for AI data centers."
            ],
            recent_news=[
                {"date": "2025-09-08", "title": "Gemini 2.0 Multimodal release", "summary": "Google released Gemini 2.0 with enhanced real-time voice, video, and reasoning capabilities."},
                {"date": "2025-11-12", "title": "Pixel 10 custom Tensor chip", "summary": "Google announced the Pixel 10 built on its first fully custom TSMC-manufactured Tensor chip."},
                {"date": "2026-02-05", "title": "Cloud Revenue Milestone", "summary": "Google Cloud segment reached $11.2B in quarterly revenue, driven by enterprise AI services."},
                {"date": "2026-04-15", "title": "Waymo passes 10 million miles", "summary": "Waymo autonomous vehicles completed 10 million fully driverless commercial miles."},
                {"date": "2026-06-01", "title": "AI Search Overviews expansion", "summary": "Google expanded AI-generated Search Overviews to 50 additional countries, boosting click-through metrics."}
            ],
            one_sentence_facts=[
                "Google was founded by Larry Page and Sergey Brin in 1998 while they were PhD students at Stanford.",
                "The name 'Google' is a misspelling of 'googol', which is the number 1 followed by 100 zeros.",
                "Google processes over 8.5 billion searches per day.",
                "Google's parent company Alphabet was created in 2015 to separate its core business from moonshot projects.",
                "YouTube, owned by Google, has over 2.5 billion monthly active logged-in users."
            ]
        )

    # ---- Microsoft ----
    elif any(k in content_lower for k in ["microsoft", "msft", "azure", "windows", "copilot", "openai", "xbox", "linkedin", "office 365"]):
        return CompanyProfile(
            ticker="MSFT", name="Microsoft Corporation",
            sector="Technology", industry="Software—Infrastructure",
            description="Global technology leader in cloud computing, productivity software, and AI.",
            key_metrics={"Revenue": "$245B", "Free Cash Flow": "$74B", "Stock Price": "$415.00", "Gross Margin": "70%"},
            historical_news=[
                {"date": "2016-06-13", "title": "LinkedIn Acquisition", "summary": "Microsoft announced the acquisition of LinkedIn for $26.2 billion, expanding its enterprise network."},
                {"date": "2019-10-23", "title": "JEDI Cloud Contract Award", "summary": "Microsoft won the Pentagon's $10B JEDI cloud contract, later replaced by JWCC."},
                {"date": "2023-01-23", "title": "OpenAI Partnership Expansion", "summary": "Microsoft announced a third-phase multi-billion dollar investment in OpenAI."},
                {"date": "2023-10-13", "title": "Activision Blizzard Purchase", "summary": "Microsoft closed the $69 billion acquisition of gaming publisher Activision Blizzard."},
                {"date": "2024-01-09", "title": "Azure AI Growth", "summary": "Microsoft Azure reported 28% YoY growth driven by enterprise generative AI services."}
            ],
            recent_events=[
                "Copilot AI integration across all Office 365 enterprise productivity suites.",
                "Azure OpenAI services expanding globally to support custom enterprise LLMs.",
                "Integrating generative AI tools into Bing search engine and Windows OS.",
                "Capital expenditure ramp-up for constructing next-generation green data centers.",
                "Regulatory scrutiny over partnership terms and influence with OpenAI."
            ],
            recent_news=[
                {"date": "2025-08-20", "title": "Copilot Studio Upgrades", "summary": "Microsoft launched autonomous AI agents building blocks inside Copilot Studio for enterprise clients."},
                {"date": "2025-10-14", "title": "Windows 12 AI Features", "summary": "Microsoft showcased Windows 12 built around deep local NPU processing and agentic workflows."},
                {"date": "2025-12-18", "title": "Geothermal Data Center Deal", "summary": "Microsoft signed a power purchase agreement to buy clean energy from geothermal projects."},
                {"date": "2026-03-05", "title": "Azure AI revenue contribution", "summary": "Azure reported that AI services accounted for a record 35% of total cloud infrastructure growth."},
                {"date": "2026-05-24", "title": "AI PC Ecosystem Expansion", "summary": "Microsoft and partners announced new Copilot+ PCs with advanced on-device SLM capabilities."}
            ],
            one_sentence_facts=[
                "Microsoft was founded by Bill Gates and Paul Allen in Albuquerque, New Mexico in 1975.",
                "Microsoft is the largest software company in the world by revenue.",
                "Microsoft acquired LinkedIn in 2016 for $26.2 billion.",
                "Microsoft's Azure is the second-largest cloud provider globally, behind AWS.",
                "Bill Gates stepped down as CEO of Microsoft in 2000."
            ]
        )

    # ---- Amazon ----
    elif any(k in content_lower for k in ["amazon", "amzn", "aws", "prime", "alexa", "kindle", "whole foods", "twitch"]):
        return CompanyProfile(
            ticker="AMZN", name="Amazon.com Inc",
            sector="Consumer Cyclical", industry="Internet Retail",
            description="E-commerce giant and world's largest cloud provider via AWS.",
            key_metrics={"Revenue": "$575B", "Free Cash Flow": "$36B", "Stock Price": "$185.00", "Gross Margin": "48%"},
            historical_news=[
                {"date": "2017-06-16", "title": "Whole Foods Acquisition", "summary": "Amazon acquired grocery chain Whole Foods Market for $13.7 billion in cash."},
                {"date": "2020-04-30", "title": "COVID-19 E-commerce Surge", "summary": "Amazon experienced unprecedented sales growth and expanded fulfillment infrastructure."},
                {"date": "2021-07-05", "title": "Andy Jassy becomes CEO", "summary": "Founder Jeff Bezos stepped down as CEO, transitioned to Executive Chair; Andy Jassy took over."},
                {"date": "2023-11-14", "title": "Anthropic AI Alliance", "summary": "Amazon announced an investment of up to $4B in generative AI developer Anthropic."},
                {"date": "2024-02-01", "title": "AWS $100B Run Rate", "summary": "AWS segment net sales reached $25B in Q4, positioning it on a $100B annual run rate."}
            ],
            recent_events=[
                "Amazon Rufus AI shopping assistant rollout to all US customers.",
                "AWS Bedrock generative AI platform expansion with new foundation models.",
                "Expanding Just Walk Out checkout-free technology to international retail locations.",
                "Integrating AI-based logistics routing to speed up same-day deliveries.",
                "Fulfillment warehouse automation with next-generation robotic systems."
            ],
            recent_news=[
                {"date": "2025-09-10", "title": "Project Kuiper Satellite launch", "summary": "Amazon launched its first operational Project Kuiper satellites to build a global broadband network."},
                {"date": "2025-11-20", "title": "Anthropic Claude 3.5 Integration", "summary": "Amazon AWS announced exclusive early access features for Anthropic's Claude 3.5 models on Bedrock."},
                {"date": "2026-01-15", "title": "Warehouse Robotics Milestone", "summary": "Amazon deployed Sequoia and Proteus autonomous warehouse robots across 100 fulfillment centers."},
                {"date": "2026-03-30", "title": "AWS Nuclear Power deal", "summary": "Amazon AWS acquired a data center campus powered directly by a nearby nuclear power station."},
                {"date": "2026-06-08", "title": "Prime Member Record Count", "summary": "Amazon announced that global Prime membership has surpassed 240 million active subscribers."}
            ],
            one_sentence_facts=[
                "Amazon was founded by Jeff Bezos in his garage in Bellevue, Washington in 1994.",
                "Amazon started as an online bookstore before expanding into virtually every retail category.",
                "AWS (Amazon Web Services) generates more operating profit than Amazon's entire retail business.",
                "Amazon Prime has over 200 million global members.",
                "Amazon is the largest private employer in the United States."
            ]
        )

    # ---- Meta ----
    elif any(k in content_lower for k in ["meta", "facebook", "instagram", "whatsapp", "oculus", "zuckerberg", "fb", "reels", "threads"]):
        return CompanyProfile(
            ticker="META", name="Meta Platforms Inc",
            sector="Technology", industry="Internet Content & Information",
            description="Social media conglomerate owning Facebook, Instagram, WhatsApp and leading the metaverse.",
            key_metrics={"Revenue": "$135B", "Free Cash Flow": "$43B", "Stock Price": "$510.00", "Gross Margin": "81%"},
            historical_news=[
                {"date": "2012-04-09", "title": "Instagram Acquisition", "summary": "Facebook acquired photo-sharing app Instagram for $1 billion in cash and stock."},
                {"date": "2014-02-19", "title": "WhatsApp Purchase", "summary": "Facebook acquired messaging app WhatsApp for $19 billion to expand international messaging reach."},
                {"date": "2021-10-28", "title": "Meta Rebranding", "summary": "Facebook Inc. renamed itself Meta Platforms Inc. to reflect its strategic focus on the metaverse."},
                {"date": "2023-10-04", "title": "Threads App Launch", "summary": "Meta launched Threads, a text-based conversational app, hitting 100M signups in 5 days."},
                {"date": "2024-01-31", "title": "First-Ever Share Dividend", "summary": "Meta reported stellar Q4 profits and declared its first-ever quarterly cash dividend."}
            ],
            recent_events=[
                "Llama 3 open-source large language model released for commercial developers.",
                "Ray-Ban Meta Smart Glasses volume sales surpassing internal company projections.",
                "Meta AI assistant rollout across Instagram, WhatsApp, and Facebook feeds.",
                "Shifting hardware focus from VR headsets to AR smart glasses and mixed reality.",
                "Cost restructuring and efficiency measures reducing overall corporate overhead."
            ],
            recent_news=[
                {"date": "2025-08-14", "title": "Llama 4 Training infrastructure", "summary": "Meta completed building a cluster of 100k H100 GPUs to train its next-generation Llama 4 models."},
                {"date": "2025-10-25", "title": "Ray-Ban Meta translation features", "summary": "Meta rolled out real-time audio translation capabilities to Ray-Ban Meta glasses."},
                {"date": "2026-02-18", "title": "Meta AI active users count", "summary": "CEO Mark Zuckerberg reported that Meta AI has reached 500 million active monthly users."},
                {"date": "2026-04-05", "title": "Orion AR Glasses Showcase", "summary": "Meta previewed Orion, its first true augmented reality glasses, to positive feedback."},
                {"date": "2026-05-30", "title": "Ad Monetization Growth", "summary": "Meta announced record-high click-through metrics on Instagram Reels ads using AI recommendation engines."}
            ],
            one_sentence_facts=[
                "Facebook was founded by Mark Zuckerberg in his Harvard dorm room in 2004.",
                "Meta's apps are used by over 3.2 billion people daily across the world.",
                "Instagram was acquired by Facebook in 2012 for $1 billion — it was 2 years old at the time.",
                "WhatsApp was acquired by Facebook in 2014 for $19 billion.",
                "Meta spent over $36 billion on its metaverse Reality Labs division between 2021 and 2023."
            ]
        )

    # ---- Netflix ----
    elif any(k in content_lower for k in ["netflix", "nflx", "streaming", "reed hastings"]):
        return CompanyProfile(
            ticker="NFLX", name="Netflix Inc",
            sector="Communication Services", industry="Entertainment",
            description="World's largest subscription streaming service.",
            key_metrics={"Revenue": "$37B", "Free Cash Flow": "$6.9B", "Stock Price": "$650.00", "Subscribers": "270M+"},
            historical_news=[
                {"date": "2013-02-01", "title": "House of Cards Release", "summary": "Netflix launched House of Cards, its first high-profile original drama series."},
                {"date": "2016-01-06", "title": "Global Launch Expansion", "summary": "Netflix went live in 130 new countries, completing its global distribution expansion."},
                {"date": "2021-09-17", "title": "Squid Game Phenomenon", "summary": "Squid Game premiered, becoming Netflix's biggest-ever launch with 1.65B hours viewed."},
                {"date": "2023-05-23", "title": "Paid Sharing Rollout", "summary": "Netflix rolled out password sharing restrictions globally, driving record subscriber sign-ups."},
                {"date": "2024-01-23", "title": "WWE Raw Live Streaming Deal", "summary": "Netflix signed a $5B, 10-year deal to stream WWE Raw live, entering live entertainment."}
            ],
            recent_events=[
                "Ad-supported subscription tier reaching over 40 million monthly active users.",
                "Strategic expansion of live streaming events, including comedy specials and sports.",
                "Expanding mobile games catalog available for all subscribers at no extra cost.",
                "Content localization initiatives to drive subscription growth in APAC and LATAM.",
                "Gradual phase-out of basic ad-free plans in key geographic markets."
            ],
            recent_news=[
                {"date": "2025-07-22", "title": "Squid Game Season 2", "summary": "Netflix officially scheduled the premiere of Squid Game Season 2 for late 2025."},
                {"date": "2025-10-10", "title": "NFL Christmas Live Games Deal", "summary": "Netflix secured exclusive global rights to stream NFL Christmas Day games for three seasons."},
                {"date": "2026-01-28", "title": "Subscriber Count Reaches 295M", "summary": "Netflix reported Q4 earnings, showing paid memberships grew to 295 million globally."},
                {"date": "2026-03-15", "title": "Netflix Games Expansion", "summary": "Netflix announced a partnership with major studios to bring high-profile IP games to mobile."},
                {"date": "2026-05-20", "title": "Ad Tier Revenue contribution", "summary": "Netflix announced that the ad-supported tier now contributes 15% of total average revenue per member in US."}
            ],
            one_sentence_facts=[
                "Netflix was founded in 1997 as a DVD-by-mail service before pivoting to streaming in 2007.",
                "Netflix's recommendation algorithm saves the company an estimated $1 billion per year in churn.",
                "Netflix has produced original content in over 190 countries.",
                "The company turned down a chance to sell itself to Blockbuster for $50 million in 2000.",
                "Netflix's top shows like Squid Game reach over 100 million households in the first 28 days."
            ]
        )

    # ---- Tesla ----
    elif any(k in content_lower for k in ["tesla", "tsla", "elon musk", "model y", "model 3", "cybertruck", "gigafactory", "fsd", "powerwall"]):
        return CompanyProfile(
            ticker="TSLA", name="Tesla Inc",
            sector="Consumer Cyclical", industry="Auto Manufacturers",
            description="Electric vehicle and clean energy company.",
            key_metrics={"Revenue": "$96B", "Free Cash Flow": "$4.3B", "Stock Price": "$175.00", "Operating Margin": "9.2%"},
            historical_news=[
                {"date": "2012-06-22", "title": "Model S Deliveries Begin", "summary": "Tesla delivered the first Model S sedans, revolutionizing consumer perceptions of EVs."},
                {"date": "2017-07-28", "title": "Model 3 Production launch", "summary": "Tesla launched Model 3 production, aiming to bring EVs to mass-market price points."},
                {"date": "2020-01-07", "title": "Gigafactory Shanghai Deliveries", "summary": "Tesla delivered the first China-built Model 3 cars from Gigafactory Shanghai in record time."},
                {"date": "2023-11-30", "title": "Cybertruck Deliveries Event", "summary": "Tesla delivered the first custom stainless-steel Cybertruck pickups at Gigafactory Texas."},
                {"date": "2026-01-15", "title": "Earnings Beat", "summary": "Tesla exceeded Q4 earnings expectations despite global pricing headwinds."}
            ],
            recent_events=[
                "Model Y Refresh launched in North America with upgraded interior design.",
                "Full Self-Driving (FSD) Supervised v12 rollout using end-to-end neural network controls.",
                "Expansion of Megapack battery storage factory output in Lathrop and Shanghai.",
                "Supercharger network expansion and adoption of NACS connector by rival automakers.",
                "Next-generation low-cost vehicle platform development under project Redwood."
            ],
            recent_news=[
                {"date": "2025-08-08", "title": "Robotaxi Platform Unveiled", "summary": "Tesla showcased its dedicated Robotaxi platform with Cybercab design in Los Angeles."},
                {"date": "2025-11-12", "title": "FSD international approvals", "summary": "Tesla secured regulatory approvals to launch FSD Beta in Europe and China markets next year."},
                {"date": "2026-02-14", "title": "Optimus Humanoid Bot Gen 2", "summary": "Tesla deployed its Optimus Gen 2 humanoid robots on real tasks across the Texas Gigafactory."},
                {"date": "2026-04-18", "title": "Megapack Shanghai Online", "summary": "Tesla's Shanghai Megafactory started production of heavy energy storage units ahead of schedule."},
                {"date": "2026-06-12", "title": "Redwood low-cost model production", "summary": "Elon Musk confirmed that pilot production of the next-generation $25k vehicle has begun."}
            ],
            one_sentence_facts=[
                "Tesla is named after Nikola Tesla, the famous electrical engineer and inventor.",
                "Tesla open-sourced all of its patents in 2014 to accelerate the world's transition to sustainable energy.",
                "The Tesla Model S features a medical-grade HEPA filter named 'Bioweapon Defense Mode'.",
                "Tesla's first car was the Roadster, which was launched in 2008 and based on a Lotus Elise chassis.",
                "In 2018, Elon Musk launched his midnight cherry Tesla Roadster into space on a Falcon Heavy rocket."
            ]
        )

    # ---- Generic fallback: use the queried company name ----
    else:
        # Extract the actual company name from the news_content string
        # e.g. "Profile for Goldman Sachs" → "Goldman Sachs"
        cleaned = news_content.strip()
        for prefix in ["profile for ", "ticker ", "company "]:
            if cleaned.lower().startswith(prefix):
                cleaned = cleaned[len(prefix):]
                break
        
        # Take the first line
        cleaned = cleaned.split('\n')[0].strip()
        
        # Stop before common verbs/indicators in headlines
        indicators = [
            " abruptly", " suspends", " announces", " reports", " launches", 
            " acquires", " buys", " sells", " faces", " hits", " drops", 
            " surges", " jumps", " falls", " plummets", " beats", " misses", 
            " declares", " posts", " plans", " files", " sues", " warns", 
            " expects", " share", " stock", " ceo", " to ", " in ", " at ",
            " for ", " on ", " with ", " is ", " has ", " will "
        ]
        
        stop_idx = len(cleaned)
        lower_cleaned = cleaned.lower()
        for indicator in indicators:
            idx = lower_cleaned.find(indicator)
            if idx != -1 and idx < stop_idx:
                stop_idx = idx
                
        for char in [":", " -", " —", " |"]:
            idx = cleaned.find(char)
            if idx != -1 and idx < stop_idx:
                stop_idx = idx
                
        candidate = cleaned[:stop_idx].strip()
        candidate = re.sub(r'[,.\-:\s]+$', '', candidate)
        
        if len(candidate) < 2:
            company_name = cleaned[:30].strip().title() or "Unknown Company"
        else:
            company_name = candidate.title()
        ticker_guess = re.sub(r'[^A-Z]', '', company_name.upper())[:5] or "UNKN"
        
        # Calculate dynamic mock metrics based on company name length to make them realistic & stable
        name_len = len(company_name)
        price_val = 45.0 + (name_len * 7.7) + (ord(company_name[0]) if company_name else 0) % 50
        rev_val = 12.0 + (name_len * 3.4)
        fcf_val = 1.5 + (name_len * 0.7)
        margin_val = 25 + (name_len % 30)
        
        # Determine sector based on company name keywords
        lower_name = company_name.lower()
        if any(w in lower_name for w in ["bank", "sachs", "morgan", "capital", "finance", "wealth", "asset", "credit"]):
            sector_val = "Financials"
            industry_val = "Diversified Financial Services"
        elif any(w in lower_name for w in ["pharma", "health", "biotech", "medical", "clinic", "cure"]):
            sector_val = "Healthcare"
            industry_val = "Biotechnology"
        elif any(w in lower_name for w in ["oil", "gas", "energy", "power", "solar", "wind", "fuel"]):
            sector_val = "Energy"
            industry_val = "Oil & Gas Exploration"
        elif any(w in lower_name for w in ["shop", "retail", "store", "buy", "brand", "market", "wear"]):
            sector_val = "Consumer Cyclical"
            industry_val = "Specialty Retail"
        else:
            sector_val = "Technology"
            industry_val = "Software—Application"

        return CompanyProfile(
            ticker=ticker_guess,
            name=company_name,
            sector=sector_val,
            industry=industry_val,
            description=f"{company_name} is a leading player in the {industry_val.lower()} sector. Configure a Gemini API key in your .env file to enable live real-time LLM profile extraction.",
            key_metrics={
                "Stock Price": f"${price_val:.2f}",
                "Revenue": f"${rev_val:.1f}B",
                "Free Cash Flow": f"${fcf_val:.1f}B",
                "Gross Margin": f"{margin_val}%",
                "Target Rating": "Hold"
            },
            historical_news=[
                {"date": "2020-04-18", "title": "Corporate Formation", "summary": f"{company_name} was founded or restructured, scaling operations globally."},
                {"date": "2021-11-05", "title": "Series A Funding & Expansion", "summary": f"{company_name} secured major growth capital and completed its first key strategic acquisition."},
                {"date": "2022-08-30", "title": "Sustainability Pledge", "summary": f"{company_name} committed to a net-zero carbon operational plan to improve ESG scores."},
                {"date": "2023-05-12", "title": "Headquarters Relocation", "summary": f"{company_name} officially opened new headquarters to handle global market demand."},
                {"date": "2024-03-22", "title": "Fiscal Year Record Results", "summary": f"{company_name} reported record-breaking revenue figures driven by adoption of core services."}
            ],
            recent_events=[
                f"{company_name} announced new operational efficiency and cost optimization measures.",
                "Integrating AI-driven systems to improve analytical and customer operations.",
                "Expanding key corporate customer success networks in North America and EMEA.",
                "Participating in major upcoming global industry panel keynotes.",
                "Recent board meeting approved expansion of capital expenditure plans for R&D."
            ],
            recent_news=[
                {"date": "2025-09-14", "title": "Corporate Restructuring", "summary": f"{company_name} announced a streamline of organizational divisions to optimize resource allocation."},
                {"date": "2025-12-01", "title": "Advanced AI Integration", "summary": f"{company_name} partnered with leading research labs to embed generative AI models in customer operations."},
                {"date": "2026-02-18", "title": "Stock Buyback Program", "summary": f"{company_name} approved a multi-billion dollar stock repurchase plan, signaling high confidence."},
                {"date": "2026-04-05", "title": "New CEO Appointed", "summary": f"{company_name} board named a veteran industry executive as the incoming Chief Executive Officer."},
                {"date": "2026-06-10", "title": "Product Launch Announcement", "summary": f"{company_name} teased a brand-new service lineup set to debut next quarter."}
            ],
            one_sentence_facts=[
                f"{company_name} is a publicly traded company on global stock exchanges.",
                "Configure a Gemini API key in your .env file to unlock real-time company profiles.",
                "FinSwarm uses Google Gemini to generate detailed financial profiles, metrics, and historical context.",
                f"The core operations of {company_name} are heavily influenced by macro rate fluctuations and supply chains.",
                f"Customer reviews show a high degree of brand satisfaction across {company_name}'s key demographics."
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
    if "add" in cmd_lower or "create" in cmd_lower or "introduce" in cmd_lower:
        # Extract name using named X pattern
        name_match = re.search(r'\bnamed\s+([a-zA-Z0-9_\s\-]+?)(?:\s+who|\s+that|\s+does|\s+is|\s+focusing|\s+with|\s+to|\s+has|\b|$|\.|\,)', cmd_lower)
        candidate_name = ""
        if name_match:
            candidate_name = name_match.group(1).strip().title()
        else:
            # Extract name using add X who pattern
            pattern = r'\b(?:add|create|introduce)\s+(?:a\s+|an\s+|new\s+|additional\s+|another\s+)?(?:agent\s+|persona\s+|investor\s+|trader\s+)?([a-zA-Z0-9_\s\-]+?)(?:\s+who|\s+that|\s+does|\s+is|\s+focusing|\s+with|\s+to|\s+has|\b|$|\.|\,)'
            add_match = re.search(pattern, cmd_lower)
            if add_match:
                candidate_name = add_match.group(1).strip().title()
        
        # Clean candidate_name of common descriptors
        exclude_words = ["agent", "persona", "day trader", "investor", "retailer", "short", "bull", "bear", "analyst", "this", "additional", "new", "another", "the", "a", "an", "some"]
        if candidate_name:
            name_words = candidate_name.split()
            clean_name = " ".join([w for w in name_words if w.lower() not in exclude_words]).strip()
        else:
            clean_name = ""
            
        if not clean_name or clean_name.lower() in ["agent", "persona", "investor", "trader"]:
            # Auto-generate name based on content keywords
            if "esg" in cmd_lower or "green" in cmd_lower or "sustain" in cmd_lower:
                clean_name = "ESG Specialist"
            elif "tech" in cmd_lower or "ai" in cmd_lower or "software" in cmd_lower or "semiconductor" in cmd_lower:
                clean_name = "Tech Analyst"
            elif "meme" in cmd_lower or "reddit" in cmd_lower or "hype" in cmd_lower or "wsb" in cmd_lower or "retail" in cmd_lower:
                clean_name = "Meme Trader"
            elif "value" in cmd_lower or "buffett" in cmd_lower or "dividend" in cmd_lower or "fundamental" in cmd_lower:
                clean_name = "Value Investor"
            elif "macro" in cmd_lower or "fed" in cmd_lower or "rate" in cmd_lower or "inflation" in cmd_lower:
                clean_name = "Macro Strategist"
            elif "short" in cmd_lower or "critic" in cmd_lower or "skeptic" in cmd_lower:
                clean_name = "Short Seller"
            elif "growth" in cmd_lower or "momentum" in cmd_lower or "trend" in cmd_lower:
                clean_name = "Growth Investor"
            elif "quant" in cmd_lower or "math" in cmd_lower or "algo" in cmd_lower or "data" in cmd_lower:
                clean_name = "Quant Trader"
            else:
                clean_name = "Custom Persona"

        # Ensure uniqueness
        base_name = clean_name
        counter = 1
        while clean_name in updated:
            clean_name = f"{base_name} {counter}"
            counter += 1

        # Extract role description
        desc = ""
        for delimiter in [r'\bwho focuses on\b', r'\bfocusing on\b', r'\bwho specializes in\b', r'\bspecializing in\b', r'\bwho does\b', r'\bthat does\b', r'\bwho is\b', r'\bthat is\b', r'\bwho has\b', r'\bthat has\b']:
            matches = re.split(delimiter, cmd_lower, maxsplit=1)
            if len(matches) > 1:
                desc = matches[1].strip()
                break
        
        if not desc:
            desc = command
            for w in ["add", "create", "introduce", "new", "additional", "another", "agent", "persona", "named", clean_name] + clean_name.split():
                desc = re.sub(r'\b' + re.escape(w) + r'\b', '', desc, flags=re.IGNORECASE)
            desc = desc.strip(" ,.!?")
            
        # Clean description of sentiment/conviction words to keep it professional
        desc = re.sub(r'\b(?:and\s+)?(?:has\s+)?(?:highly\s+|very\s+|extremely\s+)?(?:bullish|bearish|neutral)\s+(?:sentiment|conviction|stance|attitude)?\b.*', '', desc, flags=re.IGNORECASE)
        desc = desc.strip(" ,.!?")
        
        if desc:
            desc = desc[0].upper() + desc[1:]
        else:
            desc = f"A customized agent focused on parsing market sentiment."

        # Parse Sentiment
        sent_val = 0.0
        sent_match = re.search(r'sentiment\s+(?:of\s+)?(-?\d+(?:\.\d+)?)', cmd_lower)
        if sent_match:
            try:
                sent_val = max(-1.0, min(1.0, float(sent_match.group(1))))
            except ValueError:
                pass
        else:
            if "highly bullish" in cmd_lower or "very bullish" in cmd_lower or "extremely bullish" in cmd_lower:
                sent_val = 0.9
            elif "highly bearish" in cmd_lower or "very bearish" in cmd_lower or "extremely bearish" in cmd_lower:
                sent_val = -0.9
            elif "bullish" in cmd_lower or "optimistic" in cmd_lower or "positive" in cmd_lower:
                sent_val = 0.7
            elif "bearish" in cmd_lower or "pessimistic" in cmd_lower or "negative" in cmd_lower:
                sent_val = -0.7
            elif "neutral" in cmd_lower or "flat" in cmd_lower:
                sent_val = 0.0

        # Parse Conviction
        conv_val = 0.6
        conv_match = re.search(r'conviction\s+(?:of\s+)?(\d+(?:\.\d+)?)(%?)', cmd_lower)
        if conv_match:
            try:
                val = float(conv_match.group(1))
                is_pct = conv_match.group(2) == '%'
                if is_pct or val > 1.0:
                    conv_val = max(0.0, min(1.0, val / 100.0))
                else:
                    conv_val = max(0.0, min(1.0, val))
            except ValueError:
                pass
        else:
            if "high conviction" in cmd_lower or "strong conviction" in cmd_lower or "highly convinced" in cmd_lower:
                conv_val = 0.85
            elif "low conviction" in cmd_lower or "weak conviction" in cmd_lower:
                conv_val = 0.35

        updated[clean_name] = {
            "name": clean_name,
            "swarm_type": "Trading & Analytical Swarm" if any(w in cmd_lower for w in ["analyst", "quant", "macro", "value", "short", "research", "expert"]) else "Retail & Consumer Swarm",
            "role_identity": desc,
            "primary_metrics": ["Stock Price", "Sentiment dynamics"],
            "cognitive_biases": ["Confirmation Bias"],
            "linguistic_style": "Informal and direct." if "retail" in cmd_lower or "meme" in cmd_lower else "Pragmatic and professional.",
            "good_news_reaction": "Favorable.",
            "bad_news_reaction": "Unfavorable.",
            "initial_sentiment": sent_val,
            "initial_conviction": conv_val,
            "reactivity_threshold": 0.25,
            "market_influence_weight": 0.2,
            "social_influence_susceptibility": 0.5,
            "risk_tolerance": 0.5,
            "expertise_domains": []
        }

    return updated
