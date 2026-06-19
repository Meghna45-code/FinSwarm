from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class NewsAssessmentSchema(BaseModel):
    sentiment: float = Field(description="A score between -1.0 (highly negative/damaging) and 1.0 (highly positive/beneficial).")
    impact: float = Field(description="A score between 0.0 (negligible/minor rumor) and 1.0 (extreme/existential event).")
    summary: str = Field(description="A concise one-sentence summary of the news.")

class FactCheckSchema(BaseModel):
    is_valid: bool = Field(description="true if claims are accurate or no target stats cited, false if they hallucinated/falsified numbers")
    correction: Optional[str] = Field(description="A short note correcting the lie (e.g. 'Moderator Note: ...') or null if valid")
    suggested_penalty: float = Field(description="A multiplier (e.g. 0.1 for falsified statements, 1.0 for valid)")
    cited_source: Optional[str] = Field(description="The specific source/metric/event name from the company profile used as verification reference (e.g., 'Key Metrics: Revenue' or 'Historical News: Earnings Beat') or null if none.")

class AgentArgumentSchema(BaseModel):
    internal_monologue: str = Field(description="Your private thoughts evaluating other arguments and news")
    spoken_argument: str = Field(description="What you say out loud to the debate room")
    updated_sentiment: float = Field(description="Your new sentiment score (-1.0 to 1.0)")
    updated_conviction: float = Field(description="Your new conviction level (0.0 to 1.0)")

class DebateSummarySchema(BaseModel):
    summary: str = Field(description="A single cohesive paragraph summarizing the final consensus of the 14 agents at the end of the debate.")

class HistoricalNewsSchema(BaseModel):
    date: str = Field(description="The date of the historical news item (YYYY-MM-DD format).")
    title: str = Field(description="Title of the news event.")
    summary: str = Field(description="One-sentence summary of the event.")

class CompanyProfileSchema(BaseModel):
    ticker: str = Field(description="Stock ticker symbol in uppercase (e.g. AAPL, TSLA, NVDA). If no specific company is mentioned, default to TSLA.")
    name: str = Field(description="Full official name of the company (e.g. Apple Inc., Tesla Inc., NVIDIA Corporation). If no specific company is mentioned, default to Tesla Inc.")
    sector: str = Field(description="Stock sector (e.g. Technology, Consumer Cyclical, Communication Services).")
    industry: str = Field(description="Stock industry (e.g. Consumer Electronics, Auto Manufacturers, Semiconductors).")
    description: str = Field(description="A concise 1-2 sentence description of the company.")
    key_metrics: Dict[str, str] = Field(description="A dictionary of 4-6 key financial or operational metrics (e.g. {'Revenue': '$96B', 'Stock Price': '$180.00', 'Free Cash Flow': '$4.3B', 'P/E Ratio': '28.5'}). Note: Always include a metric for the current 'Stock Price' or 'Price' or 'Current Price'.")
    recent_events: List[str] = Field(description="A list of 5-8 of the most recent corporate events from the past 1-2 years (e.g. new product launches, regulatory filings, earnings beats, executive changes, partnerships).")
    recent_news: List[HistoricalNewsSchema] = Field(description="A list of 10-15 recent dated news items from the past 2-3 years, sorted newest first. Each item must have a date (YYYY-MM-DD), title, and one-sentence summary.")
    historical_news: List[HistoricalNewsSchema] = Field(description="A list of 2-3 historical milestones or news items over the past few years.")
    historical_milestones: List[HistoricalNewsSchema] = Field(description="A comprehensive list of 15-25 major historical milestones going all the way back to the company founding year. Should span the company's entire history — from IPO, early products, pivotal decisions, crises, turnarounds, and major industry events. Sorted oldest first (chronological order from founding onwards).")
    one_sentence_facts: List[str] = Field(description="A list of at least 20 extremely interesting, unique, and verified 1-sentence facts about the company's products, history, or culture. This will be shown to users while loading.")

class AgentPersonaSchema(BaseModel):
    name: str = Field(description="The display name of the agent (e.g. 'Institutional Value Investor', 'Day Trader').")
    swarm_type: str = Field(description="Swarm category. Must be one of: 'Retail & Consumer Swarm', 'Trading & Analytical Swarm', or 'Internal & Structural Swarm'.")
    role_identity: str = Field(description="A concise 1-2 sentence description of the agent's background, motives, and investment philosophy.")
    primary_metrics: List[str] = Field(description="A list of 3-4 financial or operational metrics this agent cares about.")
    cognitive_biases: List[str] = Field(description="A list of 2-3 cognitive biases this agent exhibits.")
    linguistic_style: str = Field(description="Description of their speech style (e.g. professional, sarcastic, aggressive, emotional).")
    good_news_reaction: str = Field(description="How this agent reacts to positive news about the stock.")
    bad_news_reaction: str = Field(description="How this agent reacts to negative news about the stock.")
    initial_sentiment: float = Field(description="Starting sentiment value from -1.0 (extremely bearish) to 1.0 (extremely bullish).")
    initial_conviction: float = Field(description="Starting conviction value from 0.0 (very weak) to 1.0 (absolute conviction).")
    reactivity_threshold: float = Field(description="Starting news reactivity threshold from 0.0 (highly reactive) to 1.0 (ignores almost all news).")

class ContextualizedPersonasResponse(BaseModel):
    personas: Dict[str, AgentPersonaSchema] = Field(description="A dictionary of agent persona names mapping to their adjusted agent persona details.")
