from typing import Dict, Any, List
from .personas import AgentPersona

class AgentState:
    """
    Tracks the active state of a single agent.
    Includes the 4 dynamic variables: sentiment, conviction, interest (reactivity), and persuasion thresholds.
    Along with a credibility factor.
    """
    def __init__(self, name: str, initial_sentiment: float, initial_conviction: float, initial_reactivity: float, swarm_type: str):
        self.name = name
        self.sentiment = initial_sentiment
        self.conviction = initial_conviction
        # Threshold 1: Interest/Reactivity Threshold (starts at initial baseline)
        self.reactivity_threshold = initial_reactivity
        self.swarm_type = swarm_type
        self.credibility = 1.0
        
        # Threshold 2: Persuasion Threshold (initialized dynamically from starting conviction)
        self.bias_factor = self._determine_bias_factor(swarm_type)
        self.update_persuasion_threshold()

    def _determine_bias_factor(self, swarm_type: str) -> float:
        if "Retail" in swarm_type:
            return 0.4  # High susceptibility, lower persuasion threshold
        elif "Trading & Analytical" in swarm_type:
            return 0.7  # Rigid/skeptical, higher persuasion threshold
        else:
            return 0.5  # Medium susceptibility

    def update_persuasion_threshold(self):
        """Updates the persuasion threshold based on current conviction and bias."""
        self.persuasion_threshold = round(max(0.05, min(0.9, self.conviction * self.bias_factor)), 3)


class StateManager:
    """
    StateManager (Live Agent State Database / Slider Registry)
    Maintains the live sentiment, conviction, interest, and persuasion thresholds.
    Updates states locally and deterministically using mathematical modeling.
    """
    def __init__(self, personas: Dict[str, AgentPersona]):
        self.agent_states: Dict[str, AgentState] = {}
        self.initialize_states(personas)

    def initialize_states(self, personas: Dict[str, AgentPersona]):
        """Initializes the live sliders using baseline values."""
        for name, persona in personas.items():
            self.agent_states[name] = AgentState(
                name=persona.name,
                initial_sentiment=persona.initial_sentiment,
                initial_conviction=persona.initial_conviction,
                initial_reactivity=persona.reactivity_threshold,
                swarm_type=persona.swarm_type
            )

    def get_agent_state(self, name: str) -> Dict[str, float]:
        """Returns the current dynamic variables for a specific agent."""
        state = self.agent_states.get(name)
        if not state:
            # Fallback: search by persona.name (e.g. "Brand Loyalist / Fanboy")
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
            "persuasion_threshold": state.persuasion_threshold,
            "credibility": state.credibility
        }

    def get_average_sentiment(self) -> float:
        """Calculates the mean sentiment score of all agents in the registry."""
        if not self.agent_states:
            return 0.0
        return sum(state.sentiment for state in self.agent_states.values()) / len(self.agent_states)

    def global_update_state(self, speaker_name: str, argument_sentiment: float, argument_impact: float):
        """
        Applies local mathematical updates to all 14 agents based on the spoken argument.
        - Calculates effective impact of the argument.
        - Checks persuasion threshold to apply changes.
        - Updates interest thresholds based on consensus and alienation effects.
        """
        speaker_state = None
        for key, val in self.agent_states.items():
            if val.name == speaker_name or key == speaker_name:
                speaker_state = val
                break
                
        speaker_conviction = speaker_state.conviction if speaker_state else 0.5
        speaker_credibility = speaker_state.credibility if speaker_state else 1.0
        effective_impact = argument_impact * (0.5 + 0.5 * speaker_conviction) * speaker_credibility

        room_avg_sentiment = self.get_average_sentiment()

        for key, state in self.agent_states.items():
            # 1. The speaker doesn't update their own state in response to their own argument
            if state.name == speaker_name or key == speaker_name:
                continue

            # 2. Persuasion Check:
            is_conforming = (state.sentiment * argument_sentiment >= 0)

            # Determine susceptibility rates based on swarm type
            if "Retail" in state.swarm_type:
                susceptibility = 0.25
                conviction_gain = 0.15
                conviction_loss = 0.20
            elif "Trading & Analytical" in state.swarm_type:
                susceptibility = 0.10
                conviction_gain = 0.05
                conviction_loss = 0.10
            else:  # Internal / Structural / ESG
                susceptibility = 0.15
                conviction_gain = 0.08
                conviction_loss = 0.12

            # Only shift fully if effective impact exceeds persuasion threshold;
            # otherwise, apply a background trickle influence (10% susceptibility) to prevent total deadlock.
            if effective_impact >= state.persuasion_threshold:
                actual_susceptibility = susceptibility
                actual_conviction_gain = conviction_gain
                actual_conviction_loss = conviction_loss
            else:
                actual_susceptibility = susceptibility * 0.1
                actual_conviction_gain = conviction_gain * 0.1
                actual_conviction_loss = conviction_loss * 0.1

            if is_conforming:
                # Shift sentiment closer to the argument
                sentiment_diff = argument_sentiment - state.sentiment
                state.sentiment = round(max(-1.0, min(1.0, state.sentiment + (sentiment_diff * actual_susceptibility))), 3)
                # Increase conviction
                state.conviction = round(min(1.0, state.conviction + actual_conviction_gain), 3)
            else:
                # Decrease conviction
                state.conviction = round(max(0.0, state.conviction - actual_conviction_loss), 3)
                
                # If conviction is completely shaken (close to 0), sentiment flips
                if state.conviction <= 0.1:
                    state.sentiment = round(-state.sentiment * 0.5, 3)  # weak flip
                    state.conviction = 0.2  # reset to low conviction
                
            # Update persuasion threshold dynamically based on the new conviction level
            state.update_persuasion_threshold()

            # 3. Dynamic Interest (Reactivity) Threshold Update
            # Consensus Effect vs. Alienation Effect
            alignment_distance = abs(state.sentiment - room_avg_sentiment)
            
            # If the agent is aligned with the room consensus (low distance), they satisfy and stay quiet (threshold increases)
            # If they are alienated (high distance), they get defensive and want to fight back (threshold decreases)
            if alignment_distance < 0.5:
                state.reactivity_threshold = round(min(0.9, state.reactivity_threshold + 0.03), 3)
            else:
                state.reactivity_threshold = round(max(0.02, state.reactivity_threshold - 0.03), 3)
