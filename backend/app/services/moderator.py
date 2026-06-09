import re
from typing import Dict, Any, List, Optional
from .personas import CompanyProfile

class ModeratorAgent:
    """
    ModeratorAgent (The Truth Guard & Turn Director)
    Responsible for scoring news, deciding which agents speak based on reactivity, 
    and fact-checking arguments using Room A's Ground Truth Company Profile.
    Now maintains a dynamic priority queue of speakers based on interest thresholds.
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
        """
        Runs the standard news assessment.
        """
        if self.room_c and self.room_c.llm_client:
            try:
                return await self.room_c.assess_news(news_content)
            except Exception:
                pass  # Fallback to rules-based logic

        # Fallback Rules-based analysis
        sentiment = 0.0
        impact = 0.3
        summary = news_content[:100] + "..." if len(news_content) > 100 else news_content

        # Simple negative/positive keywords count
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

        # Boost impact if major legal/governance keywords appear
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
        Evaluates the interest of all listening agents. If the effective impact of the
        argument exceeds their interest threshold, they are added to the priority queue.
        """
        # Determine the speaker's conviction and credibility to calculate effective impact
        speaker_conviction = 1.0
        speaker_credibility = 1.0
        if speaker_name != "SYSTEM_NEWS":
            try:
                state = room_d.get_agent_state(speaker_name)
                speaker_conviction = state["conviction"]
                speaker_credibility = state.get("credibility", 1.0)
            except Exception:
                pass

        effective_impact = argument_impact * (0.5 + 0.5 * speaker_conviction) * speaker_credibility

        # Only prevent immediate speaker ping-pong if we have more than 2 agents in the room
        skip_previous = len(agents_list) > 2

        for agent in agents_list:
            # Skip the agent who just spoke to prevent monologue loops
            if agent.persona.name == speaker_name:
                continue
            # Skip the previous speaker to prevent immediate back-to-back ping-pong loops
            if skip_previous and agent.persona.name == self.previous_speaker_name:
                continue

            try:
                # Fetch dynamic interest threshold (reactivity)
                state = room_d.get_agent_state(agent.persona.name)
                reactivity_threshold = state["reactivity_threshold"]
            except Exception:
                reactivity_threshold = agent.reactivity_threshold

            interest_delta = effective_impact - reactivity_threshold

            # Frequency/cooldown penalty: check speaker history and penalize active agents
            if agent.persona.name in self.speaker_history:
                # Count position from the end of history
                history_rev = list(reversed(self.speaker_history))
                try:
                    pos = history_rev.index(agent.persona.name)
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

            if interest_delta >= 0:
                # Add to queue or update priority if already present
                existing = next((item for item in self.speaker_queue if item["agent"].persona.name == agent.persona.name), None)
                if existing:
                    existing["priority"] = max(existing["priority"], interest_delta)
                else:
                    self.speaker_queue.append({"agent": agent, "priority": interest_delta})

    def pop_next_speaker(self) -> Optional[Any]:
        """
        Pops the agent who is most interested/provoked by the topic.
        Orders queue by priority descending.
        """
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

    def seed_initial_speakers(self, agents_list: List[Any], count: int = 3):
        """
        Fallback when queue is empty:
        Seeds the queue with the most reactive agents (lowest baseline interest thresholds).
        """
        sorted_agents = sorted(agents_list, key=lambda a: a.reactivity_threshold)
        for i in range(min(count, len(sorted_agents))):
            agent = sorted_agents[i]
            # Verify if already in queue
            if not any(item["agent"].persona.name == agent.persona.name for item in self.speaker_queue):
                self.speaker_queue.append({"agent": agent, "priority": 0.1 * (count - i)})

    def select_wrap_up_agents(self, agents_list: List[Any]) -> List[Any]:
        """
        Selects up to 2 unique agents with the highest priority/interest from the queue.
        If queue is empty, seeds it first using reactive fallback agents.
        """
        if not self.speaker_queue:
            self.seed_initial_speakers(agents_list, count=3)
            
        # Sort queue by priority descending (which is the calculated interest_delta)
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
        Evaluates the stopping conditions:
        Consensus: If the sentiments of all agents in the room have converged close
        to each other (standard deviation < 0.15), the debate stops.
        """
        if room_d.agent_states and turn_count >= 2:
            sentiments = [state.sentiment for state in room_d.agent_states.values()]
            if len(sentiments) > 1:
                mean_sent = sum(sentiments) / len(sentiments)
                variance = sum((s - mean_sent) ** 2 for s in sentiments) / len(sentiments)
                std_dev = variance ** 0.5
                
                # If standard deviation is less than 0.15, the sentiments are sufficiently
                # close to each other, indicating convergence.
                if std_dev < 0.15:
                    print(f"--- [Moderator] Stopping debate early at turn {turn_count}: sentiments have converged (std_dev = {std_dev:.3f} < 0.15) ---")
                    return True
                
        return False

    async def fact_check_argument(self, speaker_name: str, argument_text: str) -> Dict[str, Any]:
        """
        Scans an agent's argument for factual numbers or metrics, and compares them 
        against the company profile context.
        Returns a verification dictionary indicating if any discrepancies were found.
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

        # Basic fallback local validation
        return {"is_valid": True, "correction": None, "penalty": 1.0, "cited_source": None}
