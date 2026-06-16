from typing import Dict, Any, List
from .personas import AgentPersona

class AgentState:
    """
    Tracks the active state of a single agent.
    Includes sentiment, conviction, reactivity threshold, and persuasion logic.
    Completely dynamic, utilizing the agent's unique social influence susceptibility.
    """
    def __init__(self, name: str, initial_sentiment: float, initial_conviction: float, initial_reactivity: float, social_influence_susceptibility: float):
        self.name = name
        self.sentiment = initial_sentiment
        self.conviction = initial_conviction
        self.reactivity_threshold = initial_reactivity
        self.social_influence_susceptibility = social_influence_susceptibility
        
        # Initialize persuasion threshold dynamically
        self.persuasion_threshold = 0.5
        self.update_persuasion_threshold()

    def update_persuasion_threshold(self):
        """
        Updates how stubborn the agent is.
        High Conviction + Low Susceptibility = High Persuasion Threshold (Stubborn)
        Low Conviction + High Susceptibility = Low Persuasion Threshold (Gullible)
        """
        stubbornness = 1.0 - self.social_influence_susceptibility
        # Threshold scales with conviction and stubbornness
        self.persuasion_threshold = round(max(0.05, min(0.9, self.conviction * stubbornness)), 3)


class StateManager:
    """
    StateManager (Live Agent State Database / Slider Registry)
    Maintains the live sentiment, conviction, interest, and persuasion thresholds.
    Updates states locally and deterministically using proportional mathematical modeling.
    """
    def __init__(self, personas: Dict[str, AgentPersona]):
        self.agent_states: Dict[str, AgentState] = {}
        self.initialize_states(personas)

    def initialize_states(self, personas: Dict[str, AgentPersona]):
        """Initializes the live sliders using baseline values."""
        for name, persona in personas.items():
            susceptibility = getattr(persona, 'social_influence_susceptibility', 0.5)
            self.agent_states[name] = AgentState(
                name=persona.name,
                initial_sentiment=persona.initial_sentiment,
                initial_conviction=persona.initial_conviction,
                initial_reactivity=persona.reactivity_threshold,
                social_influence_susceptibility=susceptibility
            )

    def get_agent_state(self, name: str) -> Dict[str, float]:
        """Returns the current dynamic variables for a specific agent."""
        state = self.agent_states.get(name)
        if not state:
            # Fallback search
            for k, val in self.agent_states.items():
                if val.name == name:
                    state = val
                    break
        if not state:
            raise ValueError(f"Agent {name} not found in StateManager.")
            
        return {
            "sentiment": state.sentiment,
            "conviction": state.conviction,
            "reactivity_threshold": state.reactivity_threshold,
            "persuasion_threshold": state.persuasion_threshold
        }

    def get_average_sentiment(self) -> float:
        """Calculates the mean sentiment score of all agents in the registry."""
        if not self.agent_states:
            return 0.0
        return sum(state.sentiment for state in self.agent_states.values()) / len(self.agent_states)

    def global_update_state(self, speaker_name: str, argument_sentiment: float, argument_impact: float):
        """
        Applies local mathematical updates to all agents based on the spoken argument.
        Uses proportional shifting based on Impact Ratios rather than binary thresholds.
        """
        # Find the speaker's state to get their conviction
        speaker_state = next((val for key, val in self.agent_states.items() if val.name == speaker_name or key == speaker_name), None)
        speaker_conviction = speaker_state.conviction if speaker_state else 0.5
        
        # Effective Impact is the raw argument impact (which includes fact-check penalties) multiplied by speaker confidence.
        effective_impact = argument_impact * speaker_conviction
        room_avg_sentiment = self.get_average_sentiment()

        for key, state in self.agent_states.items():
            # 1. The speaker doesn't update their own state in response to their own argument
            if state.name == speaker_name or key == speaker_name:
                continue

            # 2. Calculate Proportional Impact Ratio
            # How hard does this argument hit relative to their stubbornness? (Capped at 3.0x to prevent wild swings)
            impact_ratio = min(effective_impact / max(state.persuasion_threshold, 0.05), 3.0)

            # 3. Determine if the listener agrees (conforming) or disagrees (dissenting) with the argument direction
            # Both positive or both negative = conforming
            is_conforming = (state.sentiment >= 0 and argument_sentiment >= 0) or (state.sentiment <= 0 and argument_sentiment <= 0)

            if is_conforming:
                # AGREEMENT: Validate and strengthen
                # Shift sentiment closer to the argument proportionally
                sentiment_diff = argument_sentiment - state.sentiment
                shift_amount = sentiment_diff * state.social_influence_susceptibility * impact_ratio * 0.5
                state.sentiment = round(max(-1.0, min(1.0, state.sentiment + shift_amount)), 3)
                
                # Increase conviction proportionally
                conviction_gain = 0.1 * impact_ratio * state.social_influence_susceptibility
                state.conviction = round(min(1.0, state.conviction + conviction_gain), 3)
                
            else:
                # DISAGREEMENT: Shake conviction
                # Conviction loss scales with effective impact, their susceptibility, and the impact ratio
                conviction_loss = effective_impact * state.social_influence_susceptibility * impact_ratio * 0.5
                state.conviction = round(max(0.0, state.conviction - conviction_loss), 3)
                
                # The Flip: If conviction is completely crushed, they surrender and flip sides
                if state.conviction <= 0.1:
                    state.sentiment = round(-state.sentiment * 0.5, 3)  # Flip sentiment, but weaken it
                    state.conviction = 0.2  # Reset to low conviction on the new side
                
            # Update their stubbornness based on their new conviction
            state.update_persuasion_threshold()

            # 4. Dynamic Interest (Reactivity) Threshold Update
            # Consensus Effect vs. Alienation Effect
            alignment_distance = abs(state.sentiment - room_avg_sentiment)
            
            if alignment_distance < 0.5:
                # Aligned with room consensus: feel safe, get quieter (threshold increases)
                state.reactivity_threshold = round(min(0.9, state.reactivity_threshold + 0.03), 3)
            else:
                # Alienated from room consensus: get defensive, want to speak up (threshold decreases)
                state.reactivity_threshold = round(max(0.02, state.reactivity_threshold - 0.03), 3)