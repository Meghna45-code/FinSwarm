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
        debate_history: List[Dict[str, str]],
        is_wrap_up: bool = False,
        cached_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the agent's turn. 
        Fetches stats from StateManager, calls LlmOrchestrator to prompt the LLM, and returns the response.
        """
        # Fetch dynamic state from StateManager (the single source of truth)
        state = self.room_d.get_agent_state(self.persona.name)
        current_sentiment = state["sentiment"]
        current_conviction = state["conviction"]
        current_reactivity = state["reactivity_threshold"]

        # Dynamically compile the system prompt based on their current active StateManager parameters
        active_system_prompt = self.room_c.get_primed_agent_prompt(
            company_profile=self.company_profile,
            agent_name=self.persona.name,
            personas=self.personas,
            current_sentiment=current_sentiment,
            current_conviction=current_conviction,
            current_reactivity=current_reactivity
        )

        if self.room_c and self.room_c.llm_client:
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
                    "updated_sentiment": float(response.get("updated_sentiment") if response.get("updated_sentiment") is not None else current_sentiment),
                    "updated_conviction": float(response.get("updated_conviction") if response.get("updated_conviction") is not None else current_conviction)
                }
            except Exception:
                pass  # Fallback to local mock generation
                
        return self._generate_fallback_response(news_content, news_sentiment, current_sentiment, current_conviction, is_wrap_up=is_wrap_up)

    def _generate_fallback_response(self, news_content: str, news_sentiment: float, current_sentiment: float, current_conviction: float, is_wrap_up: bool = False) -> Dict[str, Any]:
        """Local mock response for verification when LLM is offline."""
        if is_wrap_up:
            spoken = f"In conclusion, as a {self.persona.name}, my final stance is clear. "
            if current_sentiment > 0.3:
                spoken += "Despite the arguments, I still believe the underlying valuation is solid and we will see long-term gains."
            elif current_sentiment < -0.3:
                spoken += "The debate has not addressed the fundamental downside risks, and I maintain my cautious outlook."
            else:
                spoken += "We must watch key metrics closely, but we remain neutral until the next earnings report."
            return {
                "speaker": self.persona.name,
                "internal_monologue": "Offline mock wrap-up reaction.",
                "spoken_argument": spoken,
                "updated_sentiment": current_sentiment,
                "updated_conviction": current_conviction
            }

        spoken = f"Looking at this news, as a {self.persona.name}, my view is that we need to monitor the situation. "
        if current_sentiment > 0.3:
            spoken += "I remain optimistic about the long-term potential of the brand."
        elif current_sentiment < -0.3:
            spoken += "This highlights the structural risks that have been ignored."
        else:
            spoken += "We need more data before jumping to conclusions."

        return {
            "speaker": self.persona.name,
            "internal_monologue": f"Offline mock reaction.",
            "spoken_argument": spoken,
            "updated_sentiment": current_sentiment,
            "updated_conviction": current_conviction
        }


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
            # Get the initial starting/contextualized stats from StateManager
            state = self.room_d.get_agent_state(name)
            current_sentiment = state["sentiment"]
            current_conviction = state["conviction"]
            current_reactivity = state["reactivity_threshold"]

            # Compile the initial system prompt with starting parameters
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
                # Update the matching turn in transcript
                turn_num = event["data"]["turn"]
                for t in transcript:
                    if t["turn"] == turn_num:
                        t["moderator_note"] = event["data"]["moderator_note"]
                        t["is_factually_correct"] = event["data"]["is_factually_correct"]
                        t["factuality_score"] = event["data"]["factuality_score"]
                        t["cited_source"] = event["data"].get("cited_source")
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
        Incorporates concurrent background fact checking and speech generation.
        """
        # 1. Reset and assess news
        self.moderator.clear_queue()
        news_assessment = await self.moderator.assess_news(news_content)
        news_sentiment = news_assessment["sentiment"]
        news_impact = news_assessment["impact"]

        yield {"type": "news_analysis", "data": news_assessment}

        debate_history: List[Dict[str, Any]] = []
        state_history: List[Dict[str, Any]] = []

        if existing_transcript and existing_state_history:
            # Resuming an existing debate
            debate_history = list(existing_transcript)
            state_history = list(existing_state_history)
            turn_count = len(debate_history)
            
            # Restore StateManager states from the last turn in state history
            if state_history:
                last_state_entry = state_history[-1]
                last_states = last_state_entry.get("states", {})
                for agent_name, saved_state in last_states.items():
                    state_obj = self.room_d.agent_states.get(agent_name)
                    if not state_obj:
                        for k, val in self.room_d.agent_states.items():
                            if val.name == agent_name:
                                state_obj = val
                                break
                    if state_obj:
                        state_obj.sentiment = saved_state.get("sentiment", state_obj.sentiment)
                        state_obj.conviction = saved_state.get("conviction", state_obj.conviction)
                        state_obj.reactivity_threshold = saved_state.get("reactivity_threshold", state_obj.reactivity_threshold)
                        state_obj.credibility = saved_state.get("credibility", state_obj.credibility)
                        state_obj.update_persuasion_threshold()

            # Find the last speaker
            last_speaker = None
            if debate_history:
                for turn in reversed(debate_history):
                    if turn["speaker"] != "Moderator":
                        last_speaker = turn["speaker"]
                        break
            
            self.moderator.last_speaker_name = last_speaker
            
            # Queue speakers based on the last spoken argument
            if debate_history:
                last_turn = debate_history[-1]
                # If the last turn was Moderator, find the last agent turn before it
                last_agent_turn = None
                for turn in reversed(debate_history):
                    if turn["speaker"] != "Moderator":
                        last_agent_turn = turn
                        break
                
                ref_turn = last_agent_turn if last_agent_turn else last_turn
                ref_sentiment = ref_turn.get("sentiment_after", news_sentiment)
                
                self.moderator.evaluate_and_queue_speakers(
                    speaker_name=ref_turn["speaker"],
                    argument_sentiment=ref_sentiment,
                    argument_impact=news_impact,
                    agents_list=self.agents,
                    room_d=self.room_d
                )
        else:
            # Start fresh
            # Record initial states from StateManager
            initial_states = {name: self.room_d.get_agent_state(name) for name in self.personas.keys()}
            state_history.append({"turn": 0, "states": initial_states})
            yield {"type": "state_update", "data": {"turn": 0, "states": initial_states}}

            # Queue initial speakers triggered by news
            self.moderator.evaluate_and_queue_speakers(
                speaker_name="SYSTEM_NEWS",
                argument_sentiment=news_sentiment,
                argument_impact=news_impact,
                agents_list=self.agents,
                room_d=self.room_d
            )
            
            # If queue is empty (news is low impact), seed fallback speakers
            if not self.moderator.speaker_queue:
                self.moderator.seed_initial_speakers(self.agents, count=3)
            
            turn_count = 0

        max_turns = max_rounds * 10

        # Pop first speaker to initialize pipeline
        agent = self.moderator.pop_next_speaker()
        if not agent:
            self.moderator.seed_initial_speakers(self.agents, count=2)
            agent = self.moderator.pop_next_speaker()

        if agent:
            turn_count += 1
            speaker_state = self.room_d.get_agent_state(agent.persona.name)
            speaker_sentiment = speaker_state["sentiment"]
            speaker_conviction = speaker_state["conviction"]

            # Generate first agent speech
            turn_result = await agent.react_and_speak(
                news_content=news_content,
                news_sentiment=news_sentiment,
                news_impact=news_impact,
                debate_history=debate_history,
                cached_content=cached_content
            )

            # Update first agent's own state in StateManager
            speaker_state_obj = self.room_d.agent_states.get(agent.persona.name)
            if speaker_state_obj:
                speaker_state_obj.sentiment = turn_result["updated_sentiment"]
                speaker_state_obj.conviction = turn_result["updated_conviction"]
                speaker_state_obj.update_persuasion_threshold()

            # Record and yield first turn immediately
            updated_state = self.room_d.get_agent_state(agent.persona.name)
            history_entry = {
                "turn": turn_count,
                "speaker": agent.persona.name,
                "speech": turn_result["spoken_argument"],
                "internal_monologue": turn_result["internal_monologue"],
                "sentiment_after": updated_state["sentiment"],
                "conviction_after": updated_state["conviction"],
                "moderator_note": None,
                "is_factually_correct": True,
                "cited_source": None,
                "factuality_score": 1.0
            }
            debate_history.append(history_entry)
            
            turn_states = {name: self.room_d.get_agent_state(name) for name in self.personas.keys()}
            state_history.append({"turn": turn_count, "states": turn_states})
            yield {"type": "state_update", "data": {"turn": turn_count, "states": turn_states}}
            yield {"type": "turn", "data": history_entry}

            # Loop for subsequent turns using pipeline concurrency
            while turn_count < max_turns:
                # Check stopping conditions via moderator
                if self.moderator.should_stop_debate(self.room_d, turn_count):
                    break

                # Queue speakers based on current agent's argument (using news_impact as proxy impact)
                self.moderator.evaluate_and_queue_speakers(
                    speaker_name=agent.persona.name,
                    argument_sentiment=turn_result["updated_sentiment"],
                    argument_impact=news_impact,
                    agents_list=self.agents,
                    room_d=self.room_d
                )

                next_agent = self.moderator.pop_next_speaker()
                if not next_agent:
                    self.moderator.seed_initial_speakers(self.agents, count=2)
                    next_agent = self.moderator.pop_next_speaker()
                    if not next_agent:
                        break

                # Define background fact checking & state updating task for current agent
                async def run_background_fact_check_and_update(cur_agent, cur_turn_result, history_idx):
                    check = await self.moderator.fact_check_argument(
                        speaker_name=cur_agent.persona.name,
                        argument_text=cur_turn_result["spoken_argument"]
                    )
                    
                    # Apply penalty
                    cur_state_obj = self.room_d.agent_states.get(cur_agent.persona.name)
                    if not check["is_valid"] and cur_state_obj:
                        cur_state_obj.credibility = round(max(0.1, cur_state_obj.credibility * check["penalty"]), 2)

                    veracity_score = check["penalty"]
                    scaled_impact = news_impact * veracity_score

                    # Global update
                    self.room_d.global_update_state(
                        speaker_name=cur_agent.persona.name,
                        argument_sentiment=cur_turn_result["updated_sentiment"],
                        argument_impact=scaled_impact
                    )

                    # Update history list
                    debate_history[history_idx]["moderator_note"] = check["correction"]
                    debate_history[history_idx]["is_factually_correct"] = check["is_valid"]
                    debate_history[history_idx]["cited_source"] = check.get("cited_source")
                    debate_history[history_idx]["factuality_score"] = float(veracity_score)

                    # Return updated states
                    updated_states = {name: self.room_d.get_agent_state(name) for name in self.personas.keys()}
                    return check, updated_states

                history_entry_idx = len(debate_history) - 1

                # Launch tasks concurrently
                fact_check_task = run_background_fact_check_and_update(agent, turn_result, history_entry_idx)
                speech_task = next_agent.react_and_speak(
                    news_content=news_content,
                    news_sentiment=news_sentiment,
                    news_impact=news_impact,
                    debate_history=debate_history,
                    cached_content=cached_content
                )

                # Await both
                (check_res, updated_states_after_fc), next_turn_result = await asyncio.gather(fact_check_task, speech_task)

                # Yield fact check event and state updates from the finished fact check task
                yield {
                    "type": "fact_check",
                    "data": {
                        "turn": debate_history[history_entry_idx]["turn"],
                        "speaker": agent.persona.name,
                        "moderator_note": check_res["correction"],
                        "is_factually_correct": check_res["is_valid"],
                        "cited_source": check_res.get("cited_source"),
                        "factuality_score": float(check_res["penalty"]),
                        "states": updated_states_after_fc
                    }
                }

                # Update active agent reference and run next sequence
                agent = next_agent
                turn_result = next_turn_result
                turn_count += 1

                # Update next agent's own state
                speaker_state_obj = self.room_d.agent_states.get(agent.persona.name)
                if speaker_state_obj:
                    speaker_state_obj.sentiment = turn_result["updated_sentiment"]
                    speaker_state_obj.conviction = turn_result["updated_conviction"]
                    speaker_state_obj.update_persuasion_threshold()

                # Record and yield next speaker's turn immediately
                updated_state = self.room_d.get_agent_state(agent.persona.name)
                history_entry = {
                    "turn": turn_count,
                    "speaker": agent.persona.name,
                    "speech": turn_result["spoken_argument"],
                    "internal_monologue": turn_result["internal_monologue"],
                    "sentiment_after": updated_state["sentiment"],
                    "conviction_after": updated_state["conviction"],
                    "moderator_note": None,
                    "is_factually_correct": True,
                    "cited_source": None,
                    "factuality_score": 1.0
                }
                debate_history.append(history_entry)
                
                turn_states = {name: self.room_d.get_agent_state(name) for name in self.personas.keys()}
                state_history.append({"turn": turn_count, "states": turn_states})
                yield {"type": "state_update", "data": {"turn": turn_count, "states": turn_states}}
                yield {"type": "turn", "data": history_entry}

            # Fact check the final speaker of the loop since we exited the loop
            if debate_history:
                last_idx = len(debate_history) - 1
                if debate_history[last_idx]["moderator_note"] is None and debate_history[last_idx]["speaker"] != "Moderator":
                    check = await self.moderator.fact_check_argument(
                        speaker_name=agent.persona.name,
                        argument_text=turn_result["spoken_argument"]
                    )
                    cur_state_obj = self.room_d.agent_states.get(agent.persona.name)
                    if not check["is_valid"] and cur_state_obj:
                        cur_state_obj.credibility = round(max(0.1, cur_state_obj.credibility * check["penalty"]), 2)

                    veracity_score = check["penalty"]
                    scaled_impact = news_impact * veracity_score

                    self.room_d.global_update_state(
                        speaker_name=agent.persona.name,
                        argument_sentiment=turn_result["updated_sentiment"],
                        argument_impact=scaled_impact
                    )

                    debate_history[last_idx]["moderator_note"] = check["correction"]
                    debate_history[last_idx]["is_factually_correct"] = check["is_valid"]
                    debate_history[last_idx]["cited_source"] = check.get("cited_source")
                    debate_history[last_idx]["factuality_score"] = float(veracity_score)

                    updated_states = {name: self.room_d.get_agent_state(name) for name in self.personas.keys()}
                    yield {
                        "type": "fact_check",
                        "data": {
                            "turn": debate_history[last_idx]["turn"],
                            "speaker": agent.persona.name,
                            "moderator_note": check["correction"],
                            "is_factually_correct": check["is_valid"],
                            "cited_source": check.get("cited_source"),
                            "factuality_score": float(veracity_score),
                            "states": updated_states
                        }
                    }

        # 7. Moderator Wrap-up Round
        if turn_count >= max_turns:
            wrap_up_agents = self.moderator.select_wrap_up_agents(self.agents)
            if wrap_up_agents:
                agent_names = [a.persona.name for a in wrap_up_agents]
                if len(agent_names) == 2:
                    mod_speech = f"We have reached the maximum debate rounds without a unanimous consensus. Before compiling the final valuation, I invite our major dissenting voices—{agent_names[0]} and {agent_names[1]}—to present their final wrap-up statements. {agent_names[0]}, please state your final case."
                else:
                    mod_speech = f"We have reached the maximum debate rounds. Before compiling the final valuation, I invite our dissenting voice, {agent_names[0]}, to present a final wrap-up statement. Please state your final case."
                
                turn_count += 1
                mod_entry = {
                    "turn": turn_count,
                    "speaker": "Moderator",
                    "speech": mod_speech,
                    "internal_monologue": "Initiating wrap-up sequence to hear remaining dissenting/active viewpoints.",
                    "sentiment_after": 0.0,
                    "conviction_after": 1.0,
                    "moderator_note": None,
                    "is_factually_correct": True
                }
                debate_history.append(mod_entry)
                turn_states = {name: self.room_d.get_agent_state(name) for name in self.personas.keys()}
                state_history.append({"turn": turn_count, "states": turn_states})
                
                yield {"type": "state_update", "data": {"turn": turn_count, "states": turn_states}}
                yield {"type": "turn", "data": mod_entry}

                for idx, agent in enumerate(wrap_up_agents):
                    if idx > 0:
                        turn_count += 1
                        mod_speech_next = f"Thank you, {agent_names[0]}. Now, {agent_names[1]}, let's hear your final wrap-up statement."
                        mod_entry_next = {
                            "turn": turn_count,
                            "speaker": "Moderator",
                            "speech": mod_speech_next,
                            "internal_monologue": f"Calling next wrap-up speaker: {agent_names[1]}.",
                            "sentiment_after": 0.0,
                            "conviction_after": 1.0,
                            "moderator_note": None,
                            "is_factually_correct": True
                        }
                        debate_history.append(mod_entry_next)
                        turn_states = {name: self.room_d.get_agent_state(name) for name in self.personas.keys()}
                        state_history.append({"turn": turn_count, "states": turn_states})
                        
                        yield {"type": "state_update", "data": {"turn": turn_count, "states": turn_states}}
                        yield {"type": "turn", "data": mod_entry_next}

                    turn_count += 1
                    turn_result = await agent.react_and_speak(
                        news_content=news_content,
                        news_sentiment=news_sentiment,
                        news_impact=news_impact,
                        debate_history=debate_history,
                        is_wrap_up=True,
                        cached_content=cached_content
                    )

                    state_obj = self.room_d.agent_states.get(agent.persona.name)
                    if state_obj:
                        state_obj.sentiment = turn_result["updated_sentiment"]
                        state_obj.conviction = turn_result["updated_conviction"]
                        state_obj.update_persuasion_threshold()

                    updated_state = self.room_d.get_agent_state(agent.persona.name)
                    wrap_up_entry = {
                        "turn": turn_count,
                        "speaker": agent.persona.name,
                        "speech": turn_result["spoken_argument"],
                        "internal_monologue": turn_result["internal_monologue"],
                        "sentiment_after": updated_state["sentiment"],
                        "conviction_after": updated_state["conviction"],
                        "moderator_note": None,
                        "is_factually_correct": True
                    }
                    debate_history.append(wrap_up_entry)
                    turn_states = {name: self.room_d.get_agent_state(name) for name in self.personas.keys()}
                    state_history.append({"turn": turn_count, "states": turn_states})

                    yield {"type": "state_update", "data": {"turn": turn_count, "states": turn_states}}
                    yield {"type": "turn", "data": wrap_up_entry}

        # 8. Generate final consensus summary
        final_states = {name: self.room_d.get_agent_state(name) for name in self.personas.keys()}
        summary_paragraph = await self.room_c.generate_debate_summary(
            self.company_profile, 
            debate_history,
            final_states
          )

        # 9. Valuation Model
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
