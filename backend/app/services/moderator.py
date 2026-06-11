import re
from typing import Dict, Any, List, Optional
from .personas import CompanyProfile

class ModeratorAgent:
    """
    ModeratorAgent (The Truth Guard & Turn Director)
    Responsible for scoring news, deciding which agents speak based on reactivity, 
    provocation, and absolute sentiment, and fact-checking arguments using Room A's 
    Ground Truth Company Profile.
    """
    def __init__(self, company_profile: CompanyProfile, room_c=None):
        self.company_profile = company_profile
        self.room_c = room_c
        
        # Priority queue structure: list of dicts {"agent": DebateAgentInstance, "priority": float}
        self.speaker_queue: List[Dict[str, Any]] = []
        self.last_speaker_name: Optional[str] = None
        self.previous_speaker_name: Optional[str] = None
        self.speaker_history: List[str] = []

    async def assess_news(self, news_content: str) -> Dict[str, float]:
        """Runs the standard news assessment via the LLM Orchestrator."""
        if self.room_c and self.room_c.llm_client:
            try:
                return await self.room_c.assess_news(news_content)
            except Exception:
                pass  # Fallback to rules-based logic

        # Fallback Rules-based analysis
        sentiment = 0.0
        impact = 0.3
        summary = news_content[:100] + "..." if len(news_content) > 100 else news_content

        neg_words = ["investigation", "sue", "fraud", "recall", "drop", "loss", "bankrupt", "miss", "subpoena", "deficit"]
        pos_words = ["launch", "growth", "profit", "beat", "partnership", "success", "innovate", "upgrade", "surplus"]

        content_lower = news_content.lower()
        neg_count = sum(1 for w in neg_words if w in content_lower)
        pos_count = sum(1 for w in pos_words if w in content_lower)

        if neg_count > pos_count:
            sentiment = -0.5 if neg_count > 2 else -0.2
            impact = min(0.3 + (neg_count * 0.15), 0.9)
        elif pos_count > neg_count:
            sentiment = 0.5 if pos_count > 2 else 0.2
            impact = min(0.3 + (pos_count * 0.1), 0.8)

        if "sec" in content_lower or "fraud" in content_lower or "bankrupt" in content_lower:
            impact = max(impact, 0.8)

        return {"sentiment": sentiment, "impact": impact, "summary": summary}

    def clear_queue(self):
        """Resets the priority queue and speaker tracking."""
        self.speaker_queue.clear()
        self.last_speaker_name = None
        self.previous_speaker_name = None
        self.speaker_history.clear()

    def evaluate_and_queue_speakers(self, speaker_name: str, argument_sentiment: float, argument_impact: float, agents_list: List[Any], room_d):
        """
        Broadcasting step:
        Evaluates the interest of all listening agents based on Effective Impact, 
        Provocation (Sentiment Friction), and Frequency Penalties.
        """
        # 1. Calculate Effective Impact (Argument Impact * Speaker Conviction)
        speaker_conviction = 1.0
        if speaker_name != "SYSTEM_NEWS":
            try:
                state = room_d.get_agent_state(speaker_name)
                speaker_conviction = state.get("conviction", 1.0)
            except Exception:
                pass

        effective_impact = argument_impact * speaker_conviction

        # Anti-ping-pong skip logic (needs at least 3 agents to function)
        skip_previous = len(agents_list) > 2

        for agent in agents_list:
            # Skip the current speaker to prevent monologue loops
            if agent.persona.name == speaker_name:
                continue
            # Skip the previous speaker to prevent instant A-B-A-B ping-pong
            if skip_previous and agent.persona.name == self.previous_speaker_name:
                continue

            try:
                state = room_d.get_agent_state(agent.persona.name)
                listener_reactivity = state.get("reactivity_threshold", agent.reactivity_threshold)
                listener_sentiment = state.get("sentiment", agent.initial_sentiment)
            except Exception:
                listener_reactivity = agent.reactivity_threshold
                listener_sentiment = agent.initial_sentiment

            # 2. Provocation Bonus (absolute difference between argument sentiment and listener sentiment)
            provocation_bonus = abs(argument_sentiment - listener_sentiment)

            # 3. Base Priority Calculation
            interest_delta = (effective_impact + provocation_bonus) - listener_reactivity

            # 4. Frequency Penalty: Penalize agents who have spoken recently
            if agent.persona.name in self.speaker_history:
                history_rev = list(reversed(self.speaker_history))
                try:
                    pos = history_rev.index(agent.persona.name)
                    # Pos 0 & 1 are usually caught by Anti-Ping-Pong, but we keep this as a safe fallback
                    if pos == 0:
                        interest_delta -= 0.5
                    elif pos == 1:
                        interest_delta -= 0.3
                    elif pos == 2:
                        interest_delta -= 0.15
                    else:
                        interest_delta -= 0.05
                except ValueError:
                    pass

            # Queue the agent if they break their threshold
            if interest_delta >= 0:
                existing = next((item for item in self.speaker_queue if item["agent"].persona.name == agent.persona.name), None)
                if existing:
                    existing["priority"] = max(existing["priority"], interest_delta)
                else:
                    self.speaker_queue.append({"agent": agent, "priority": interest_delta})

    def pop_next_speaker(self) -> Optional[Any]:
        """Pops the agent who is most interested/provoked by the topic."""
        if not self.speaker_queue:
            return None
        
        # Sort queue by priority descending
        self.speaker_queue.sort(key=lambda x: x["priority"], reverse=True)
        top_item = self.speaker_queue.pop(0)
        
        popped_agent = top_item["agent"]
        self.previous_speaker_name = self.last_speaker_name
        self.last_speaker_name = popped_agent.persona.name
        
        # Track history (keeping last 4 speakers)
        self.speaker_history.append(popped_agent.persona.name)
        if len(self.speaker_history) > 4:
            self.speaker_history.pop(0)
            
        return popped_agent

    def silence_breaker_fallback(self, agents_list: List[Any], room_d, count: int = 3):
        """
        Fallback when queue is empty:
        Seeds the queue with the most PASSIONATE agents by finding the highest Absolute Sentiment.
        """
        def get_abs_sentiment(agent):
            try:
                state = room_d.get_agent_state(agent.persona.name)
                return abs(state.get("sentiment", agent.initial_sentiment))
            except Exception:
                return abs(agent.initial_sentiment)

        # Sort agents by highest absolute sentiment (closest to -1.0 or 1.0)
        sorted_agents = sorted(agents_list, key=get_abs_sentiment, reverse=True)
        
        for i in range(min(count, len(sorted_agents))):
            agent = sorted_agents[i]
            if not any(item["agent"].persona.name == agent.persona.name for item in self.speaker_queue):
                self.speaker_queue.append({"agent": agent, "priority": 0.1 * (count - i)})

    def select_wrap_up_agents(self, agents_list: List[Any], room_d) -> List[Any]:
        """
        Selects up to 2 unique agents with the highest priority/interest from the queue.
        If queue is empty, seeds it first using the absolute sentiment silence breaker.
        """
        if not self.speaker_queue:
            self.silence_breaker_fallback(agents_list, room_d, count=3)
            
        # Sort queue by priority descending
        self.speaker_queue.sort(key=lambda x: x["priority"], reverse=True)
        
        selected_agents = []
        for item in self.speaker_queue:
            agent = item["agent"]
            if agent not in selected_agents:
                selected_agents.append(agent)
            if len(selected_agents) >= 2:
                break
                
        return selected_agents

    def should_stop_debate(self, room_d, turn_count: int) -> bool:
        """
        Evaluates stopping conditions:
        Consensus: If the sentiments of all agents in the room have converged close
        to each other (standard deviation < 0.15), the debate stops.
        """
        if room_d.agent_states and turn_count >= 2:
            sentiments = [state["sentiment"] for state in room_d.agent_states.values()]
            if len(sentiments) > 1:
                mean_sent = sum(sentiments) / len(sentiments)
                variance = sum((s - mean_sent) ** 2 for s in sentiments) / len(sentiments)
                std_dev = variance ** 0.5
                
                # If standard deviation is less than 0.15, sentiments indicate convergence.
                if std_dev < 0.15:
                    print(f"--- [Moderator] Stopping debate early at turn {turn_count}: sentiments have converged (std_dev = {std_dev:.3f} < 0.15) ---")
                    return True
                
        return False

    async def fact_check_argument(self, speaker_name: str, argument_text: str) -> Dict[str, Any]:
        """
        Scans an agent's argument for factual numbers or metrics, compares them 
        against the company profile context, AND scores the argument for sentiment and impact.
        """
        if self.room_c and self.room_c.llm_client:
            try:
                return await self.room_c.fact_check_argument(
                    company_profile=self.company_profile,
                    speaker_name=speaker_name,
                    argument_text=argument_text
                )
            except Exception:
                pass

        # Basic fallback local validation & scoring if LLM fails
        sentiment = 0.0
        impact = 0.3
        
        pos_words = ["growth", "increase", "up", "bullish", "profit", "buy", "strong"]
        neg_words = ["drop", "decrease", "down", "bearish", "loss", "sell", "risk", "weak"]
        
        text_lower = argument_text.lower()
        pos_count = sum(1 for w in pos_words if w in text_lower)
        neg_count = sum(1 for w in neg_words if w in text_lower)
        
        if pos_count > neg_count:
            sentiment = min(0.2 * (pos_count - neg_count), 1.0)
        elif neg_count > pos_count:
            sentiment = max(-0.2 * (neg_count - pos_count), -1.0)
            
        impact = min(0.3 + ((pos_count + neg_count) * 0.1), 0.9)

        return {
            "is_valid": True, 
            "correction": None, 
            "penalty": 1.0, 
            "cited_source": None,
            "argument_sentiment": round(sentiment, 2),
            "argument_impact": round(impact, 2)
        }