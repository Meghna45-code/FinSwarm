import asyncio
from typing import Dict, Any, List, Optional
from .personas import AgentPersona, CompanyProfile
from .llm_orchestrator import LlmOrchestrator
from .state_manager import StateManager
from .moderator import ModeratorAgent
from .valuation_model import ValuationModel

class DebateAgentInstance:
    """
    DebateAgentInstance
    Represents a specific live agent in the debate room.
    Queries StateManager for its live sentiment/conviction and calls LlmOrchestrator to speak.
    """
    def __init__(self, persona: AgentPersona, system_prompt: str, room_c: LlmOrchestrator, room_d: StateManager, company_profile: CompanyProfile, personas: Dict[str, AgentPersona]):
        self.persona = persona
        self.system_prompt = system_prompt
        self.room_c = room_c
        self.room_d = room_d
        self.reactivity_threshold = persona.reactivity_threshold
        self.company_profile = company_profile
        self.personas = personas

    async def react_and_speak(
        self, 
        news_content: str, 
        news_sentiment: float, 
        news_impact: float, 
        debate_history: List[Dict[str, Any]],
        is_wrap_up: bool = False,
        cached_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the agent's turn. 
        Fetches stats from StateManager and calls LlmOrchestrator to prompt the LLM.
        Throws a hard error if the LLM connection fails.
        """
        # Fetch dynamic state from StateManager (the single source of truth)
        state = self.room_d.get_agent_state(self.persona.name)
        current_sentiment = state.get("sentiment", self.persona.initial_sentiment)
        current_conviction = state.get("conviction", self.persona.initial_conviction)
        current_reactivity = state.get("reactivity_threshold", self.persona.reactivity_threshold)

        # Dynamically compile the system prompt based on their current active StateManager parameters
        active_system_prompt = self.room_c.get_primed_agent_prompt(
            company_profile=self.company_profile,
            agent_name=self.persona.name,
            personas=self.personas,
            current_sentiment=current_sentiment,
            current_conviction=current_conviction,
            current_reactivity=current_reactivity
        )

        if not self.room_c or not self.room_c.llm_client:
            raise ConnectionError("CRITICAL: LLM Client is completely disconnected. Cannot generate speech.")

        try:
            response = await self.room_c.generate_agent_argument(
                system_prompt=active_system_prompt,
                news_content=news_content,
                news_sentiment=news_sentiment,
                news_impact=news_impact,
                agent_sentiment=current_sentiment,
                agent_conviction=current_conviction,
                reactivity_threshold=current_reactivity,
                debate_history=debate_history,
                is_wrap_up=is_wrap_up,
                cached_content=cached_content
            )
            
            return {
                "speaker": self.persona.name,
                "internal_monologue": response.get("internal_monologue", ""),
                "spoken_argument": response.get("spoken_argument", "..."),
                "updated_sentiment": float(response.get("updated_sentiment", current_sentiment)),
                "updated_conviction": float(response.get("updated_conviction", current_conviction))
            }
        except Exception as e:
            # STOP SILENCING THE ERROR. Raise it so the frontend knows the simulation broke.
            raise RuntimeError(f"Simulation Halted: Failed to generate speech for {self.persona.name}. Reason: {str(e)}")


class DebateRoom:
    """
    DebateRoom
    Orchestrates the lifecycle of a round table debate.
    """
    def __init__(self, company_profile: CompanyProfile, personas: Dict[str, AgentPersona], moderator: ModeratorAgent, room_c: LlmOrchestrator, room_d: StateManager):
        self.company_profile = company_profile
        self.personas = personas
        self.moderator = moderator
        self.room_c = room_c
        self.room_d = room_d
        self.agents: List[DebateAgentInstance] = []
        self._prime_agents()

    def _prime_agents(self):
        """Creates live DebateAgentInstances using static configuration."""
        for name, persona in self.personas.items():
            state = self.room_d.get_agent_state(name)
            current_sentiment = state.get("sentiment", persona.initial_sentiment)
            current_conviction = state.get("conviction", persona.initial_conviction)
            current_reactivity = state.get("reactivity_threshold", persona.reactivity_threshold)

            system_prompt = self.room_c.get_primed_agent_prompt(
                company_profile=self.company_profile, 
                agent_name=name, 
                personas=self.personas,
                current_sentiment=current_sentiment,
                current_conviction=current_conviction,
                current_reactivity=current_reactivity
            )
            agent_instance = DebateAgentInstance(
                persona=persona, 
                system_prompt=system_prompt, 
                room_c=self.room_c,
                room_d=self.room_d,
                company_profile=self.company_profile,
                personas=self.personas
            )
            self.agents.append(agent_instance)

    async def run_simulation(
        self, 
        news_content: str, 
        max_rounds: int = 2,
        existing_transcript: List[Dict[str, Any]] = None,
        existing_state_history: List[Dict[str, Any]] = None,
        cached_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compatibility wrapper for run_simulation_generator.
        Accumulates the generated events and returns the final result dict.
        """
        news_analysis = None
        transcript = []
        state_tracking = []
        debate_summary = ""
        valuation = None

        async for event in self.run_simulation_generator(
            news_content=news_content,
            max_rounds=max_rounds,
            existing_transcript=existing_transcript,
            existing_state_history=existing_state_history,
            cached_content=cached_content
        ):
            if event["type"] == "news_analysis":
                news_analysis = event["data"]
            elif event["type"] == "turn":
                transcript.append(event["data"])
            elif event["type"] == "fact_check":
                # The fact check event just updates UI in real time, but in this wrapper
                # we just merge it into the existing transcript record
                turn_num = event["data"]["turn"]
                for t in transcript:
                    if t["turn"] == turn_num:
                        t["moderator_note"] = event["data"]["moderator_note"]
                        t["is_factually_correct"] = event["data"]["is_factually_correct"]
                        t["factuality_score"] = event["data"]["factuality_score"]
                        t["cited_source"] = event["data"].get("cited_source")
                        t["impact_score"] = event["data"].get("impact_score")
                        t["sentiment_score"] = event["data"].get("sentiment_score")
                        break
            elif event["type"] == "state_update":
                state_tracking.append(event["data"])
            elif event["type"] == "verdict":
                debate_summary = event["data"]["debate_summary"]
                valuation = event["data"]["valuation"]

        return {
            "news_analysis": news_analysis,
            "transcript": transcript,
            "state_tracking": state_tracking,
            "debate_summary": debate_summary,
            "valuation": valuation
        }

    async def run_simulation_generator(
        self, 
        news_content: str, 
        max_rounds: int = 2,
        existing_transcript: List[Dict[str, Any]] = None,
        existing_state_history: List[Dict[str, Any]] = None,
        cached_content: Optional[str] = None
    ):
        """
        Runs the debate room simulation, yielding events turn-by-turn as they happen.
        Strict Realism Mode: Agent speaks -> Moderator Evaluates -> States Update -> Queue Next.
        """
        self.moderator.clear_queue()
        
        # 1. Assess the original news
        news_assessment = await self.moderator.assess_news(news_content)
        news_sentiment = news_assessment["sentiment"]
        news_impact = news_assessment["impact"]
        yield {"type": "news_analysis", "data": news_assessment}

        debate_history: List[Dict[str, Any]] = []
        state_history: List[Dict[str, Any]] = []
        turn_count = 0

        if existing_transcript and existing_state_history:
            # Resuming an existing debate (State Restoration)
            debate_history = list(existing_transcript)
            state_history = list(existing_state_history)
            turn_count = len(debate_history)
            
            if state_history:
                last_state_entry = state_history[-1]
                last_states = last_state_entry.get("states", {})
                for agent_name, saved_state in last_states.items():
                    state_obj = self.room_d.agent_states.get(agent_name)
                    if state_obj:
                        state_obj.sentiment = saved_state.get("sentiment", state_obj.sentiment)
                        state_obj.conviction = saved_state.get("conviction", state_obj.conviction)
                        state_obj.reactivity_threshold = saved_state.get("reactivity_threshold", state_obj.reactivity_threshold)
                        state_obj.update_persuasion_threshold()

            # Find last speaker and restore queue based on last argument
            last_agent_turn = next((t for t in reversed(debate_history) if t["speaker"] != "Moderator"), None)
            if last_agent_turn:
                self.moderator.last_speaker_name = last_agent_turn["speaker"]
                self.moderator.evaluate_and_queue_speakers(
                    speaker_name=last_agent_turn["speaker"],
                    argument_sentiment=last_agent_turn.get("sentiment_score", news_sentiment),
                    argument_impact=last_agent_turn.get("impact_score", news_impact),
                    agents_list=self.agents,
                    room_d=self.room_d
                )
        else:
            # Brand New Debate
            initial_states = {name: self.room_d.get_agent_state(name) for name in self.personas.keys()}
            state_history.append({"turn": 0, "states": initial_states})
            yield {"type": "state_update", "data": {"turn": 0, "states": initial_states}}

            # Initial queueing based on the raw news impact
            self.moderator.evaluate_and_queue_speakers(
                speaker_name="SYSTEM_NEWS",
                argument_sentiment=news_sentiment,
                argument_impact=news_impact,
                agents_list=self.agents,
                room_d=self.room_d
            )
            
            # If news is too weak to trigger anyone, force the most passionate agent to speak
            if not self.moderator.speaker_queue:
                self.moderator.silence_breaker_fallback(self.agents, self.room_d, count=3)

        max_turns = max_rounds * 10
        agent = self.moderator.pop_next_speaker()

        # --- THE MAIN DEBATE LOOP ---
        while turn_count < max_turns and agent is not None:
            # A. Check if the room has reached consensus
            if self.moderator.should_stop_debate(self.room_d, turn_count):
                break

            turn_count += 1
            speaker_name = agent.persona.name

            # B. The Agent Speaks
            turn_result = await agent.react_and_speak(
                news_content=news_content,
                news_sentiment=news_sentiment,
                news_impact=news_impact,
                debate_history=debate_history,
                cached_content=cached_content
            )

            # C. The Moderator Evaluates the Speech IMMEDIATELY
            check_res = await self.moderator.fact_check_argument(
                speaker_name=speaker_name,
                argument_text=turn_result["spoken_argument"]
            )

            evaluated_impact = check_res.get("argument_impact", 0.5)
            evaluated_sentiment = check_res.get("argument_sentiment", turn_result["updated_sentiment"])
            veracity_score = check_res.get("penalty", 1.0)
            
            # D. Update the State Manager
            cur_state_obj = self.room_d.agent_states.get(speaker_name)
            if cur_state_obj:
                cur_state_obj.sentiment = turn_result["updated_sentiment"]
                cur_state_obj.conviction = turn_result["updated_conviction"]
                cur_state_obj.update_persuasion_threshold()

            # Global impact application (State Manager handles shifting everyone's mood)
            scaled_impact = evaluated_impact * veracity_score
            self.room_d.global_update_state(
                speaker_name=speaker_name,
                argument_sentiment=evaluated_sentiment,
                argument_impact=scaled_impact
            )

            # E. Record History and Yield to Frontend
            history_entry = {
                "turn": turn_count,
                "speaker": speaker_name,
                "speech": turn_result["spoken_argument"],
                "internal_monologue": turn_result["internal_monologue"],
                "sentiment_after": turn_result["updated_sentiment"],
                "conviction_after": turn_result["updated_conviction"],
                "moderator_note": check_res.get("correction"),
                "is_factually_correct": check_res.get("is_valid", True),
                "cited_source": check_res.get("cited_source"),
                "factuality_score": float(veracity_score),
                "impact_score": evaluated_impact,
                "sentiment_score": evaluated_sentiment
            }
            debate_history.append(history_entry)

            turn_states = {name: self.room_d.get_agent_state(name) for name in self.personas.keys()}
            state_history.append({"turn": turn_count, "states": turn_states})

            # Yield in sequence
            yield {"type": "state_update", "data": {"turn": turn_count, "states": turn_states}}
            yield {"type": "turn", "data": history_entry}
            yield {
                "type": "fact_check",
                "data": {
                    "turn": turn_count,
                    "speaker": speaker_name,
                    "moderator_note": check_res.get("correction"),
                    "is_factually_correct": check_res.get("is_valid", True),
                    "cited_source": check_res.get("cited_source"),
                    "factuality_score": float(veracity_score),
                    "impact_score": evaluated_impact,
                    "sentiment_score": evaluated_sentiment,
                    "states": turn_states
                }
            }

            # F. Use the highly accurate evaluations to queue the next speaker
            self.moderator.evaluate_and_queue_speakers(
                speaker_name=speaker_name,
                argument_sentiment=evaluated_sentiment,
                argument_impact=evaluated_impact,
                agents_list=self.agents,
                room_d=self.room_d
            )

            # G. Pick the next speaker
            agent = self.moderator.pop_next_speaker()
            if not agent:
                self.moderator.silence_breaker_fallback(self.agents, self.room_d, count=2)
                agent = self.moderator.pop_next_speaker()

        # --- THE WRAP UP ROUND ---
        if turn_count >= max_turns:
            wrap_up_agents = self.moderator.select_wrap_up_agents(self.agents, self.room_d)
            if wrap_up_agents:
                agent_names = [a.persona.name for a in wrap_up_agents]
                
                # Moderator introduces wrap up
                mod_speech = f"We have reached the maximum debate rounds without a unanimous consensus. Before compiling the final valuation, I invite our major dissenting voices—{', '.join(agent_names)}—to present their final wrap-up statements."
                turn_count += 1
                mod_entry = {
                    "turn": turn_count,
                    "speaker": "Moderator",
                    "speech": mod_speech,
                    "internal_monologue": "Initiating wrap-up sequence.",
                    "sentiment_after": 0.0,
                    "conviction_after": 1.0,
                    "moderator_note": None,
                    "is_factually_correct": True
                }
                debate_history.append(mod_entry)
                turn_states = {name: self.room_d.get_agent_state(name) for name in self.personas.keys()}
                yield {"type": "state_update", "data": {"turn": turn_count, "states": turn_states}}
                yield {"type": "turn", "data": mod_entry}

                # Let wrap up agents speak
                for idx, wu_agent in enumerate(wrap_up_agents):
                    turn_count += 1
                    turn_result = await wu_agent.react_and_speak(
                        news_content=news_content,
                        news_sentiment=news_sentiment,
                        news_impact=news_impact,
                        debate_history=debate_history,
                        is_wrap_up=True,
                        cached_content=cached_content
                    )

                    state_obj = self.room_d.agent_states.get(wu_agent.persona.name)
                    if state_obj:
                        state_obj.sentiment = turn_result["updated_sentiment"]
                        state_obj.conviction = turn_result["updated_conviction"]

                    updated_state = self.room_d.get_agent_state(wu_agent.persona.name)
                    wrap_up_entry = {
                        "turn": turn_count,
                        "speaker": wu_agent.persona.name,
                        "speech": turn_result["spoken_argument"],
                        "internal_monologue": turn_result["internal_monologue"],
                        "sentiment_after": updated_state.get("sentiment", 0.0),
                        "conviction_after": updated_state.get("conviction", 0.0),
                        "moderator_note": None,
                        "is_factually_correct": True
                    }
                    debate_history.append(wrap_up_entry)
                    turn_states = {name: self.room_d.get_agent_state(name) for name in self.personas.keys()}
                    yield {"type": "state_update", "data": {"turn": turn_count, "states": turn_states}}
                    yield {"type": "turn", "data": wrap_up_entry}

        # --- FINAL VALUATION ---
        final_states = {name: self.room_d.get_agent_state(name) for name in self.personas.keys()}
        summary_paragraph = await self.room_c.generate_debate_summary(
            self.company_profile, 
            debate_history,
            final_states
        )

        room_e = ValuationModel()
        valuation_results = await room_e.calculate_valuation(
            self.company_profile, 
            final_states, 
            summary_paragraph
        )

        yield {
            "type": "verdict",
            "data": {
                "debate_summary": summary_paragraph,
                "valuation": valuation_results
            }
        }