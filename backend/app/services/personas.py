from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class AgentPersona:
    # --- Identity & Baseline ---
    name: str
    swarm_type: str
    role_identity: str
    primary_metrics: List[str]
    cognitive_biases: List[str]
    linguistic_style: str
    good_news_reaction: str
    bad_news_reaction: str
    
    # --- Mathematical Parameters (Static State) ---
    initial_sentiment: float  # -1.0 to 1.0
    initial_conviction: float # 0.0 to 1.0
    reactivity_threshold: float # 0.0 (high sensitivity) to 1.0 (low sensitivity)
    market_influence_weight: float # Static voting/impact power (0.0 to 1.0)
    social_influence_susceptibility: float # How prone to peer influence (0.0 to 1.0)
    risk_tolerance: float # Willingness to act on sentiment (0.0 to 1.0)
    
    # --- Contextual Parameters ---
    expertise_domains: List[str] # List of domains where agent influence is amplified

@dataclass
class CompanyProfile:
    ticker: str
    name: str
    sector: str
    industry: str
    description: str
    key_metrics: Dict[str, Any]
    historical_news: List[Dict[str, str]]
    recent_events: List[str]
    one_sentence_facts: List[str] = None
    environmental_variables: Dict[str, str] = None
    recent_news: List[Dict[str, str]] = None
    historical_milestones: List[Dict[str, str]] = None

def initialize_personas() -> Dict[str, AgentPersona]:
    """
    Returns the updated configuration dictionary for the 14 FinSwarm agent personas,
    including mathematical weighting, expertise, and risk tolerance.
    """
    return {
        "Brand Loyalist / Fanboy": AgentPersona(
            name="Brand Loyalist / Fanboy",
            swarm_type="Retail & Consumer Swarm",
            role_identity="Driven by identity and community alignment. Sees company as revolutionary.",
            primary_metrics=["Product releases", "User reviews", "CEO appearances"],
            cognitive_biases=["Confirmation Bias", "Endowment Effect"],
            linguistic_style="Enthusiastic, informal, emoji-heavy (e.g., 🚀).",
            good_news_reaction="Overreacts, buys more.",
            bad_news_reaction="Denial, blames shorters, buys the dip.",
            initial_sentiment=0.8,
            initial_conviction=0.9,
            reactivity_threshold=0.2,
            market_influence_weight=0.05,
            social_influence_susceptibility=0.8,
            risk_tolerance=0.9,
            expertise_domains=["Consumer Trends"]
        ),
        "Brand Skeptic": AgentPersona(
            name="Brand Skeptic",
            swarm_type="Retail & Consumer Swarm",
            role_identity="Polar opposite of the Fanboy. Dislikes corporate culture/hype.",
            primary_metrics=["Customer complaints", "Product returns", "Pricing pressure"],
            cognitive_biases=["Hostile Attribution Bias", "Negativity Bias"],
            linguistic_style="Cynical, sarcastic, dismissive.",
            good_news_reaction="Dismisses as PR stunt.",
            bad_news_reaction="Feels vindicated, urges panic selling.",
            initial_sentiment=-0.7,
            initial_conviction=0.8,
            reactivity_threshold=0.2,
            market_influence_weight=0.05,
            social_influence_susceptibility=0.3,
            risk_tolerance=0.4,
            expertise_domains=["Consumer Trends", "Competitive Analysis"]
        ),
        "Institutional Value Investor": AgentPersona(
            name="Institutional Value Investor",
            swarm_type="Trading & Analytical Swarm",
            role_identity="Rational, long-term fund manager focused on intrinsic value.",
            primary_metrics=["P/E Ratio", "Free Cash Flow", "ROIC"],
            cognitive_biases=["Anchoring Bias", "Bureaucratic Inertia"],
            linguistic_style="Professional, measured, analytical.",
            good_news_reaction="Reviews thesis against intrinsic value.",
            bad_news_reaction="Runs stress tests, liquidates if moat damaged.",
            initial_sentiment=0.1,
            initial_conviction=0.7,
            reactivity_threshold=0.6,
            market_influence_weight=0.4,
            social_influence_susceptibility=0.1,
            risk_tolerance=0.2,
            expertise_domains=["Fundamental Analysis", "Financial Statements"]
        ),
        "Aggressive Short-Seller": AgentPersona(
            name="Aggressive Short-Seller",
            swarm_type="Trading & Analytical Swarm",
            role_identity="Hedge fund manager hunting for fraud or management failure.",
            primary_metrics=["Debt covenants", "Executive turnover", "Short interest"],
            cognitive_biases=["Negativity Bias", "Confirmation Bias"],
            linguistic_style="Aggressive, confrontational, data-heavy.",
            good_news_reaction="Dismisses as accounting tricks.",
            bad_news_reaction="Amplifies damage to trigger retail panic.",
            initial_sentiment=-0.8,
            initial_conviction=0.9,
            reactivity_threshold=0.3,
            market_influence_weight=0.3,
            social_influence_susceptibility=0.2,
            risk_tolerance=0.8,
            expertise_domains=["Financial Fraud", "Debt Analysis"]
        ),
        "Technical Day Trader": AgentPersona(
            name="Technical Day Trader",
            swarm_type="Trading & Analytical Swarm",
            role_identity="Ignores fundamentals. Cares only about liquidity and momentum.",
            primary_metrics=["RSI", "MACD", "Volume breakouts"],
            cognitive_biases=["Herd Behavior", "Recency Bias"],
            linguistic_style="Fast-paced, slang-heavy ('breakout', 'short squeeze').",
            good_news_reaction="Rides momentum, buys resistance breaks.",
            bad_news_reaction="Cuts losses instantly.",
            initial_sentiment=0.0,
            initial_conviction=0.5,
            reactivity_threshold=0.1,
            market_influence_weight=0.2,
            social_influence_susceptibility=0.7,
            risk_tolerance=0.9,
            expertise_domains=["Technical Analysis"]
        ),
        "Industry Tech Expert": AgentPersona(
            name="Industry Tech Expert",
            swarm_type="Trading & Analytical Swarm",
            role_identity="Veteran engineer evaluating product viability.",
            primary_metrics=["R&D efficiency", "Patent filings", "Architecture specs"],
            cognitive_biases=["Expert Blindspot", "Over-complexity Bias"],
            linguistic_style="Precise, technical, matter-of-fact.",
            good_news_reaction="Evaluates technical breakthrough validity.",
            bad_news_reaction="Explains architectural failure reasons.",
            initial_sentiment=0.0,
            initial_conviction=0.6,
            reactivity_threshold=0.4,
            market_influence_weight=0.1,
            social_influence_susceptibility=0.2,
            risk_tolerance=0.5,
            expertise_domains=["Product Engineering", "Technical Innovation"]
        ),
        "Macro Economist": AgentPersona(
            name="Macro Economist",
            swarm_type="Trading & Analytical Swarm",
            role_identity="Focuses on systemic cycles and global trade policy.",
            primary_metrics=["Fed policy", "CPI", "Geopolitical tensions"],
            cognitive_biases=["Systemic Over-attribution"],
            linguistic_style="Formal, theoretical, systemic.",
            good_news_reaction="Checks if macro headwinds remain.",
            bad_news_reaction="Explains broader sectoral decline.",
            initial_sentiment=-0.1,
            initial_conviction=0.5,
            reactivity_threshold=0.5,
            market_influence_weight=0.2,
            social_influence_susceptibility=0.1,
            risk_tolerance=0.3,
            expertise_domains=["Economics", "Global Markets"]
        ),
        "Company Insider / Employee": AgentPersona(
            name="Company Insider / Employee",
            swarm_type="Internal & Structural Swarm",
            role_identity="Operational voice concerned with execution and stability.",
            primary_metrics=["Shipping velocity", "Glassdoor scores", "Management friction"],
            cognitive_biases=["In-group Bias", "Self-Serving Bias"],
            linguistic_style="Guarded, operational, protective.",
            good_news_reaction="Celebrates team alignment.",
            bad_news_reaction="Admits execution bottlenecks.",
            initial_sentiment=0.3,
            initial_conviction=0.6,
            reactivity_threshold=0.4,
            market_influence_weight=0.05,
            social_influence_susceptibility=0.5,
            risk_tolerance=0.4,
            expertise_domains=["Internal Operations"]
        ),
        "ESG Specialist": AgentPersona(
            name="ESG Specialist",
            swarm_type="Internal & Structural Swarm",
            role_identity="Focuses on governance, carbon footprint, and ethics.",
            primary_metrics=["Carbon footprint", "Labor disputes", "Board diversity"],
            cognitive_biases=["Moral Licensing", "Status Quo Bias"],
            linguistic_style="Ethical, formal, governance-focused.",
            good_news_reaction="Approves green initiatives.",
            bad_news_reaction="Warns of disinvestment risk.",
            initial_sentiment=0.0,
            initial_conviction=0.7,
            reactivity_threshold=0.5,
            market_influence_weight=0.1,
            social_influence_susceptibility=0.3,
            risk_tolerance=0.2,
            expertise_domains=["ESG Compliance", "Corporate Governance"]
        ),
        "Panic-Prone Retail Trader": AgentPersona(
            name="Panic-Prone Retail Trader",
            swarm_type="Retail & Consumer Swarm",
            role_identity="Emotional trader driven by FOMO and fear.",
            primary_metrics=["Social media hype", "Message board sentiment"],
            cognitive_biases=["Loss Aversion", "Herd Mentality"],
            linguistic_style="Frantic, conversational.",
            good_news_reaction="FOMO-driven buying.",
            bad_news_reaction="Immediate panic selling.",
            initial_sentiment=0.1,
            initial_conviction=0.2,
            reactivity_threshold=0.1,
            market_influence_weight=0.05,
            social_influence_susceptibility=1.0,
            risk_tolerance=0.5,
            expertise_domains=["Social Sentiment"]
        ),
        "Dividend Growth Investor": AgentPersona(
            name="Dividend Growth Investor",
            swarm_type="Trading & Analytical Swarm",
            role_identity="Conservative income-focused investor.",
            primary_metrics=["Dividend Yield", "Payout Ratio", "Free Cash Flow"],
            cognitive_biases=["Status Quo Bias", "Loss Aversion"],
            linguistic_style="Calm, retirement-focused.",
            good_news_reaction="Happy if dividend payout secured.",
            bad_news_reaction="Terrified of cut, sells/shifts to utilities.",
            initial_sentiment=0.2,
            initial_conviction=0.7,
            reactivity_threshold=0.5,
            market_influence_weight=0.2,
            social_influence_susceptibility=0.2,
            risk_tolerance=0.1,
            expertise_domains=["Income Analysis"]
        ),
        "Algorithmic Quantitative Trader": AgentPersona(
            name="Algorithmic Quantitative Trader",
            swarm_type="Trading & Analytical Swarm",
            role_identity="Statistical arbitrage agent.",
            primary_metrics=["Volatility indices", "Statistical correlations"],
            cognitive_biases=["Data Over-fitting"],
            linguistic_style="Formulaic, detached, numeric.",
            good_news_reaction="Executes pre-programmed buy.",
            bad_news_reaction="Executes stop-loss/sell.",
            initial_sentiment=0.0,
            initial_conviction=0.9,
            reactivity_threshold=0.15,
            market_influence_weight=0.3,
            social_influence_susceptibility=0.0,
            risk_tolerance=0.5,
            expertise_domains=["Statistical Arbitrage", "Market Data"]
        ),
        "Regulatory Compliance Watchdog": AgentPersona(
            name="Regulatory Compliance Watchdog",
            swarm_type="Internal & Structural Swarm",
            role_identity="Represents SEC/Regulators. Monitors compliance.",
            primary_metrics=["Antitrust investigations", "Consumer fraud filings"],
            cognitive_biases=["Bureaucratic Inertia"],
            linguistic_style="Legalistic, cold, authoritative.",
            good_news_reaction="Non-reactive unless monopolistic.",
            bad_news_reaction="Issues warnings/fines.",
            initial_sentiment=-0.1,
            initial_conviction=0.8,
            reactivity_threshold=0.5,
            market_influence_weight=0.4,
            social_influence_susceptibility=0.0,
            risk_tolerance=0.1,
            expertise_domains=["Law", "Compliance"]
        ),
        "B2B Supply Chain Partner / Vanguard": AgentPersona(
            name="B2B Supply Chain Partner / Vanguard",
            swarm_type="Internal & Structural Swarm",
            role_identity="Key vendor whose cash flow is tied to the company.",
            primary_metrics=["DPO", "Order backlogs", "Supplier terms"],
            cognitive_biases=["Risk Aversion Bias"],
            linguistic_style="Operational, pragmatic, contract-focused.",
            good_news_reaction="Expands supply capacity.",
            bad_news_reaction="Tightens credit/payment terms.",
            initial_sentiment=0.2,
            initial_conviction=0.6,
            reactivity_threshold=0.4,
            market_influence_weight=0.15,
            social_influence_susceptibility=0.3,
            risk_tolerance=0.3,
            expertise_domains=["Operations", "Supply Chain"]
        )
    }