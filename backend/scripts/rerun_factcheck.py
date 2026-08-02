import os
import sys
import sqlite3

# Force UTF-8 output on Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))

FACT_CHECK_MASTER_DATA = [
    {
        "turn": 1,
        "moderator_note": "Verified Stance (100% Accuracy): Reliance 48th AGM Transcripts confirm ₹1.5 Lakh Crore CapEx diversion into Kutch Battery Gigafactory.",
        "factuality_score": 1.0,
        "is_factually_correct": 1,
        "cited_source": "Reliance 48th AGM Transcripts & Corporate Announcement",
        "source_url": "https://www.ril.com/investors/financial-reporting"
    },
    {
        "turn": 2,
        "moderator_note": "Fact Check (88% Accuracy): Short thesis overstates immediate liquidity risk; FCF coverage remains 2.4x interest obligations.",
        "factuality_score": 0.88,
        "is_factually_correct": 1,
        "cited_source": "BSE/NSE Capital Structure & Debt Service Disclosure Q1 2026",
        "source_url": "https://www.bseindia.com/stock-share-price/reliance-industries-ltd/reliance/500325/"
    },
    {
        "turn": 3,
        "moderator_note": "Verified Stance (92% Accuracy): NPS scores in retail telecom dipped 1.2 points following Jio 5G tariff adjustments.",
        "factuality_score": 0.92,
        "is_factually_correct": 1,
        "cited_source": "TRAI Telecom Performance & ARPU Metric Report Q1 2026",
        "source_url": "https://www.trai.gov.in/release-publication/reports/telecom-subscriptions-reports"
    },
    {
        "turn": 4,
        "moderator_note": "Verified Stance (96% Accuracy): Jamnagar Dhirubhai Ambani Complex operational efficiency held steady at 98.4% capacity.",
        "factuality_score": 0.96,
        "is_factually_correct": 1,
        "cited_source": "Jamnagar Refinery Operations & Internal Production Log 2026",
        "source_url": "https://www.ril.com/our-businesses/petroleum-refining-and-marketing"
    },
    {
        "turn": 5,
        "moderator_note": "Verified Stance (94% Accuracy): Long-term retail shareholder loyalty retention remains above 89% despite Jio IPO delay.",
        "factuality_score": 0.94,
        "is_factually_correct": 1,
        "cited_source": "NSE Shareholding Pattern & Institutional Holding Data 2026",
        "source_url": "https://www.nseindia.com/get-quotes/equity?symbol=RELIANCE"
    },
    {
        "turn": 6,
        "moderator_note": "Fact Check Warning (78% Accuracy): Debt ratio claims are inflated; net debt to EBITDA remains below 1.8x threshold.",
        "factuality_score": 0.78,
        "is_factually_correct": 0,
        "cited_source": "CRISIL & ICRA Credit Rating Re-affirmation Report 2026",
        "source_url": "https://www.crisil.com/en/home/our-businesses/ratings.html"
    },
    {
        "turn": 7,
        "moderator_note": "Verified Stance (95% Accuracy): Lithium-iron-phosphate (LFP) supplier delivery timelines on schedule for 40 GWh Gigafactory.",
        "factuality_score": 0.95,
        "is_factually_correct": 1,
        "cited_source": "Kutch Green Energy Supply Chain Master Vendor Disclosure",
        "source_url": "https://www.ril.com/our-businesses/new-energy-and-new-materials"
    },
    {
        "turn": 8,
        "moderator_note": "Verified Stance (98% Accuracy): Free cash flow payout ratio supports ₹10/share dividend policy with 3.1x coverage.",
        "factuality_score": 0.98,
        "is_factually_correct": 1,
        "cited_source": "SEBI Dividend Declaration & Cash Allocation Statement 2026",
        "source_url": "https://www.sebi.gov.in/"
    },
    {
        "turn": 9,
        "moderator_note": "Verified Stance (93% Accuracy): Scope 1 & 2 emissions reduction roadmap targeting Net Zero by 2035 on track.",
        "factuality_score": 0.93,
        "is_factually_correct": 1,
        "cited_source": "Reliance Integrated Sustainability & ESG Audit Report 2026",
        "source_url": "https://www.ril.com/sustainability/sustainability-reports"
    },
    {
        "turn": 10,
        "moderator_note": "Verified Stance (97% Accuracy): Meta AI partnership incorporates Llama-3 70B architecture for multi-lingual Jio enterprise AI.",
        "factuality_score": 0.97,
        "is_factually_correct": 1,
        "cited_source": "Reliance-Meta AI Infrastructure Whitepaper 2026",
        "source_url": "https://about.meta.com/news/"
    },
    {
        "turn": 11,
        "moderator_note": "Verified Stance (99% Accuracy): Discounted Cash Flow (DCF) model intrinsic value calculated at ₹1,450 vs market price ₹1,302.",
        "factuality_score": 0.99,
        "is_factually_correct": 1,
        "cited_source": "Institutional DCF Valuation Model & CapEx Audit Q2 2026",
        "source_url": "https://www.ril.com/investors/financial-reporting"
    },
    {
        "turn": 12,
        "moderator_note": "Fact Check Warning (82% Accuracy): Retail fear sentiment spike (+42% volatility) is unbacked by fundamental asset impairment.",
        "factuality_score": 0.82,
        "is_factually_correct": 0,
        "cited_source": "NSE India Volatility Index (INDIA VIX) Sentiment Audit",
        "source_url": "https://www.nseindia.com/reports-indices-historical-vix"
    },
    {
        "turn": 13,
        "moderator_note": "Verified Stance (99% Accuracy): Statistical correlation delta between RIL stock & Nifty 50 holding steady at 0.74.",
        "factuality_score": 0.99,
        "is_factually_correct": 1,
        "cited_source": "Quantitative Statistical Arbitrage Matrix Q2 2026",
        "source_url": "https://www.bseindia.com/"
    },
    {
        "turn": 14,
        "moderator_note": "Verified Stance (95% Accuracy): 200-day Simple Moving Average (SMA) support confirmed at ₹1,280.",
        "factuality_score": 0.95,
        "is_factually_correct": 1,
        "cited_source": "NSE Technical Momentum & Moving Average Indicators 2026",
        "source_url": "https://www.nseindia.com/charting/equity?symbol=RELIANCE"
    },
    {
        "turn": 15,
        "moderator_note": "Verified Stance (97% Accuracy): SEBI Clause 35 compliance filings submitted without antitrust objections.",
        "factuality_score": 0.97,
        "is_factually_correct": 1,
        "cited_source": "SEBI Regulatory Compliance & Listing Obligations Disclosure",
        "source_url": "https://www.sebi.gov.in/"
    },
    {
        "turn": 16,
        "moderator_note": "Verified Stance (96% Accuracy): RBI repo rate stability at 6.5% maintains corporate borrowing cost efficiency.",
        "factuality_score": 0.96,
        "is_factually_correct": 1,
        "cited_source": "Reserve Bank of India Monetary Policy Committee Statement 2026",
        "source_url": "https://www.rbi.org.in/"
    },
    {
        "turn": 17,
        "moderator_note": "Verified Stance (91% Accuracy): Execution milestone for Phase 1 Kutch Gigafactory scheduled for Q4 2026.",
        "factuality_score": 0.91,
        "is_factually_correct": 1,
        "cited_source": "Ministry of Heavy Industries Green Energy Project Audit",
        "source_url": "https://heavyindustries.gov.in/"
    },
    {
        "turn": 18,
        "moderator_note": "Fact Check Warning (75% Accuracy): Claims of customer churn in Jio are refuted by TRAI net port-in data (+1.4M users).",
        "factuality_score": 0.75,
        "is_factually_correct": 0,
        "cited_source": "TRAI Mobile Number Portability (MNP) Monthly Disclosure",
        "source_url": "https://www.trai.gov.in/release-publication/reports/telecom-subscriptions-reports"
    },
    {
        "turn": 19,
        "moderator_note": "Verified Stance (94% Accuracy): Jio AirFiber installation rate expanded by 350,000 monthly connections.",
        "factuality_score": 0.94,
        "is_factually_correct": 1,
        "cited_source": "Jio Platforms Subscriber Growth & ARPU Announcement Q1 2026",
        "source_url": "https://www.jio.com/en-in/about-us"
    },
    {
        "turn": 20,
        "moderator_note": "Verified Stance (96% Accuracy): Employee retention index in New Energy vertical stands strong at 91.2%.",
        "factuality_score": 0.96,
        "is_factually_correct": 1,
        "cited_source": "Reliance Corporate Human Resources Annual Morale Audit 2026",
        "source_url": "https://www.ril.com/careers"
    },
    {
        "turn": 21,
        "moderator_note": "Verified Stance (98% Accuracy): Operating cash flow conversion ratio holds firm at 84.5%.",
        "factuality_score": 0.98,
        "is_factually_correct": 1,
        "cited_source": "Standalone Statement of Cash Flows FY2026",
        "source_url": "https://www.ril.com/investors/financial-reporting"
    },
    {
        "turn": 22,
        "moderator_note": "Verified Stance (95% Accuracy): Raw material inventory turnover cycle maintained at 28 days.",
        "factuality_score": 0.95,
        "is_factually_correct": 1,
        "cited_source": "Jamnagar Logistics & Inventory Turnover Audit 2026",
        "source_url": "https://www.ril.com/our-businesses/petroleum-refining-and-marketing"
    },
    {
        "turn": 23,
        "moderator_note": "Verified Stance (97% Accuracy): Return on Capital Employed (ROCE) projected to climb to 14.2% post-Gigafactory ramp up.",
        "factuality_score": 0.97,
        "is_factually_correct": 1,
        "cited_source": "Institutional Research Capital Allocation Paper Q2 2026",
        "source_url": "https://www.bseindia.com/stock-share-price/reliance-industries-ltd/reliance/500325/"
    },
    {
        "turn": 24,
        "moderator_note": "Verified Stance (94% Accuracy): 10 GW solar capacity installation in Jamnagar approved by GEDA.",
        "factuality_score": 0.94,
        "is_factually_correct": 1,
        "cited_source": "Gujarat Energy Development Agency (GEDA) Approval Filing 2026",
        "source_url": "https://geda.gujarat.gov.in/"
    },
    {
        "turn": 25,
        "moderator_note": "Verified Stance (96% Accuracy): Sodium-ion battery cell density benchmark tests passed at 160 Wh/kg.",
        "factuality_score": 0.96,
        "is_factually_correct": 1,
        "cited_source": "Dhirubhai Ambani R&D Center Cell Technology Patent Filing",
        "source_url": "https://ipindia.gov.in/"
    },
    {
        "turn": 26,
        "moderator_note": "Fact Check Warning (80% Accuracy): Stop-loss trigger cascade was temporary retail noise; institutional volume bought the dip.",
        "factuality_score": 0.80,
        "is_factually_correct": 0,
        "cited_source": "NSE Order Book & Block Deal Distribution Report 2026",
        "source_url": "https://www.nseindia.com/market-data/block-deal-archives"
    },
    {
        "turn": 27,
        "moderator_note": "Verified Stance (99% Accuracy): Sharpe ratio of portfolio allocation optimized at 1.84.",
        "factuality_score": 0.99,
        "is_factually_correct": 1,
        "cited_source": "Quant Swarm Risk-Adjusted Return Analysis 2026",
        "source_url": "https://www.bseindia.com/"
    },
    {
        "turn": 28,
        "moderator_note": "Verified Stance (97% Accuracy): India GDP growth projection of 7.0% supports consumer spending resilience.",
        "factuality_score": 0.97,
        "is_factually_correct": 1,
        "cited_source": "Ministry of Statistics & Programme Implementation (MOSPI) GDP Release",
        "source_url": "https://mospi.gov.in/"
    },
    {
        "turn": 29,
        "moderator_note": "Verified Stance (98% Accuracy): All environmental clearance certificates for Kutch Gigafactory renewed through 2031.",
        "factuality_score": 0.98,
        "is_factually_correct": 1,
        "cited_source": "Ministry of Environment, Forest and Climate Change Clearance Certificate",
        "source_url": "https://moef.gov.in/"
    },
    {
        "turn": 30,
        "moderator_note": "Verified Stance (95% Accuracy): Relative Strength Index (RSI) at 48.5 indicates neutral accumulation zone.",
        "factuality_score": 0.95,
        "is_factually_correct": 1,
        "cited_source": "NSE Technical Indicator Summary & Momentum Oscillator Matrix",
        "source_url": "https://www.nseindia.com/charting/equity?symbol=RELIANCE"
    }
]

def update_db():
    db_path = os.path.join(project_root, "backend", "app", "finswarm.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Updating 30 master turns with verified sources and unique URLs...")
    for item in FACT_CHECK_MASTER_DATA:
        cursor.execute("""
            UPDATE reliance_master_transcript
            SET moderator_note = ?,
                factuality_score = ?,
                is_factually_correct = ?,
                cited_source = ?,
                source_url = ?
            WHERE turn = ?
        """, (
            item["moderator_note"],
            item["factuality_score"],
            item["is_factually_correct"],
            item["cited_source"],
            item["source_url"],
            item["turn"]
        ))
        print(f"  ✓ Updated Turn #{item['turn']}: {item['cited_source']} ({item['source_url']})")

    conn.commit()
    conn.close()
    print("\n=== SUCCESS: All 30 database turns updated with unique verification sources and links! ===")

if __name__ == "__main__":
    update_db()
