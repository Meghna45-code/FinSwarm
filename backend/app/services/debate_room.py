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

    def _get_offline_fallback(
        self, 
        news_sentiment: float, 
        news_impact: float, 
        current_sentiment: float, 
        current_conviction: float, 
        current_reactivity: float, 
        reason: str = ""
    ) -> Dict[str, Any]:
        diff = news_sentiment - current_sentiment
        shift = diff * news_impact * (1.0 - current_reactivity)
        updated_sentiment = max(-1.0, min(1.0, current_sentiment + shift))
        
        if (news_sentiment >= 0 and current_sentiment >= 0) or (news_sentiment <= 0 and current_sentiment <= 0):
            updated_conviction = min(1.0, current_conviction + 0.05 * news_impact)
        else:
            updated_conviction = max(0.1, current_conviction - 0.05 * news_impact)

        sentiment_label = "bullish" if updated_sentiment > 0.15 else ("bearish" if updated_sentiment < -0.15 else "neutral")
        
        company = self.company_profile.name
        role = self.persona.role_identity
        good_react = self.persona.good_news_reaction
        bad_react = self.persona.bad_news_reaction
        name = self.persona.name
        
        if name == "Brand Loyalist / Fanboy":
            if sentiment_label == "bullish":
                spoken_argument = f"Oh, this is absolutely huge for {company}! 🚀 {good_react} We are going to the moon, guys! Diamond hands! 💎🙌"
            elif sentiment_label == "bearish":
                spoken_argument = f"Come on, this is just temporary noise for {company}. {bad_react} Don't let the short-sellers scare you. I'm buying the dip! 📈"
            else:
                spoken_argument = f"I'm still holding {company} strong. The news doesn't shake my faith at all. HODL! 🚀"
                
        elif name == "Brand Skeptic":
            if sentiment_label == "bullish":
                spoken_argument = f"Don't fall for the hype. This positive update for {company} is just a PR stunt. {good_react} Fundamentals are still weak."
            elif sentiment_label == "bearish":
                spoken_argument = f"Honestly, I'm not surprised at all. {bad_react} This news about {company} confirms what I've been saying: the business model is built on sand."
            else:
                spoken_argument = f"Let's see if {company} can actually execute for once. The news is out, but I'm highly skeptical of any real change."
                
        elif name == "Institutional Value Investor":
            if sentiment_label == "bullish":
                spoken_argument = f"This development improves the intrinsic value outlook for {company}. {good_react} We see solid long-term stability here."
            elif sentiment_label == "bearish":
                spoken_argument = f"This creates a substantial margin of safety concern for {company}. {bad_react} We are re-evaluating our core position."
            else:
                spoken_argument = f"A measured response is appropriate for {company} right now. We need to stress-test the metrics before adjusting our valuation."
                
        elif name == "Aggressive Short-Seller":
            if sentiment_label == "bullish":
                spoken_argument = f"This positive news for {company} is a classic management distraction. {good_react} The underlying debt/accounting structure is still a red flag."
            elif sentiment_label == "bearish":
                spoken_argument = f"Look at the data: {company} is facing massive headwinds. {bad_react} This is the beginning of the end. Squeezing every bit of downside here."
            else:
                spoken_argument = f"The momentum is stalling for {company}. We are monitoring the short interest and executive actions closely."
                
        elif name == "Technical Day Trader":
            if sentiment_label == "bullish":
                spoken_argument = f"Clean breakout on the chart for {company}! 📈 {good_react} Riding the momentum, next resistance is key. Let's long this!"
            elif sentiment_label == "bearish":
                spoken_argument = f"It's dumping hard! {company} just broke support. {bad_react} Cutting losses immediately. Time to short or sit out."
            else:
                spoken_argument = f"Range-bound trading for {company} today. No clear trend. I'll wait for volume to pick up."
                
        elif name == "Industry Tech Expert":
            if sentiment_label == "bullish":
                spoken_argument = f"Technically speaking, {company}'s new path is highly viable. {good_react} Their engineering architecture looks solid."
            elif sentiment_label == "bearish":
                spoken_argument = f"This highlights a serious architectural bottleneck for {company}. {bad_react} You can't patch over these technical core issues."
            else:
                spoken_argument = f"The tech specs for {company} are interesting, but we need to see actual deployment data before drawing conclusions."
                
        elif name == "Macro Economist":
            if sentiment_label == "bullish":
                spoken_argument = f"At a systemic level, this aligns well with sector tailwinds for {company}. {good_react} The macroeconomic indicators are favorable."
            elif sentiment_label == "bearish":
                spoken_argument = f"This sector-wide pressure will hit {company} severely. {bad_react} Rising inflation and supply chain issues are compounding the risk."
            else:
                spoken_argument = f"Global trade policy and central bank decisions remain the main drivers. {company} will hover here until macro clarity emerges."
                
        elif name == "Company Insider / Employee":
            if sentiment_label == "bullish":
                spoken_argument = f"The team has worked incredibly hard on this at {company}! {good_react} Internally, morale is high and execution is smooth."
            elif sentiment_label == "bearish":
                spoken_argument = f"It's tough on the ground at {company} right now. {bad_react} We're dealing with operational friction and bottlenecks."
            else:
                spoken_argument = f"We are focused on daily operations and shipping product at {company}. Just keeping our heads down."
                
        elif name == "ESG Specialist":
            if sentiment_label == "bullish":
                spoken_argument = f"This governance and environmental update for {company} is a step in the right direction. {good_react} Good corporate citizenship pays off."
            elif sentiment_label == "bearish":
                spoken_argument = f"This represents a severe ethical and environmental risk for {company}. {bad_react} Institutional funds will start disinvesting."
            else:
                spoken_argument = f"We are tracking {company}'s carbon footprint and labor relations. The news is a minor variable in our ESG scorecard."
                
        elif name == "Panic-Prone Retail Trader":
            if sentiment_label == "bullish":
                spoken_argument = f"Oh my god, {company} is going up! 🚀 Is it time to buy?! I don't want to miss the boat! {good_react}"
            elif sentiment_label == "bearish":
                spoken_argument = f"This is terrible! {company} is crashing! 😱 {bad_react} Should I sell everything now? What is happening?!"
            else:
                spoken_argument = f"I don't know what to do with {company} anymore. The market is so volatile, it's making me super anxious!"
                
        elif name == "Dividend Growth Investor":
            if sentiment_label == "bullish":
                spoken_argument = f"This secures {company}'s cash flow and dividend payout safety. {good_react} A very reliable income play."
            elif sentiment_label == "bearish":
                spoken_argument = f"I'm worried about a dividend cut for {company} here. {bad_react} Capital preservation is key; I might rotate to safer yields."
            else:
                spoken_argument = f"The cash flow coverage remains stable for {company}. I will continue holding for the compounding yields."
                
        elif name == "Algorithmic Quantitative Trader":
            if sentiment_label == "bullish":
                spoken_argument = f"Signal generated: BUY {company}. Volatility is expanding. {good_react} Statistical probability favors upward trend."
            elif sentiment_label == "bearish":
                spoken_argument = f"Signal generated: SELL/SHORT {company}. {bad_react} Stop-loss parameters triggered based on standard deviation shift."
            else:
                spoken_argument = f"No trade signal for {company} at this timestamp. Statistical correlations remain within normal variance ranges."
                
        elif name == "Regulatory Compliance Watchdog":
            if sentiment_label == "bullish":
                spoken_argument = f"From a compliance standpoint, {company}'s filing appears standard. {good_react} We see no major regulatory hurdles."
            elif sentiment_label == "bearish":
                spoken_argument = f"This is a major compliance violation for {company}! {bad_react} The SEC and antitrust bodies will likely launch investigations."
            else:
                spoken_argument = f"We are monitoring the legal filings for {company}. The regulatory landscape remains complex."
                
        elif name == "B2B Supply Chain Partner / Vanguard":
            if sentiment_label == "bullish":
                spoken_argument = f"This is positive news. We are expanding our supply capacity for {company}. {good_react} Looking forward to stronger order volumes."
            elif sentiment_label == "bearish":
                spoken_argument = f"This supply disruption or operational headwind for {company} is serious. {bad_react} We are tightening payment credit terms immediately."
            else:
                spoken_argument = f"Operations are continuing as contracted with {company}. We are maintaining regular supply schedules."
                
        else:
            # Fallback for custom added agents
            if sentiment_label == "bullish":
                spoken_argument = f"Given the news, I'm quite optimistic about {company}. {good_react or 'This shows strong upward potential.'} As a {role.lower()}, I believe this will drive positive market sentiment."
            elif sentiment_label == "bearish":
                spoken_argument = f"I have concerns regarding this update for {company}. {bad_react or 'This presents downside risk.'} Looking at it as a {role.lower()}, we should expect near-term headwind."
            else:
                spoken_argument = f"I'm taking a balanced view on {company} right now. The news is notable, but as a {role.lower()}, I think we need to see how the numbers play out."

        internal_monologue = f"Offline mock reaction ({reason}): Analyzing news impact ({news_impact}) and sentiment ({news_sentiment}). Adjusting my sentiment from {current_sentiment:.2f} to {updated_sentiment:.2f} with conviction {updated_conviction:.2f}."

        return {
            "speaker": self.persona.name,
            "internal_monologue": internal_monologue,
            "spoken_argument": spoken_argument,
            "updated_sentiment": float(updated_sentiment),
            "updated_conviction": float(updated_conviction)
        }

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
        """
        # Fetch dynamic state from StateManager (the single source of truth)
        state = self.room_d.get_agent_state(self.persona.name)
        current_sentiment = state.get("sentiment", self.persona.initial_sentiment)
        current_conviction = state.get("conviction", self.persona.initial_conviction)
        current_reactivity = state.get("reactivity_threshold", self.persona.reactivity_threshold)

        # If offline or client not configured, fall back to offline logic
        if not self.room_c or not self.room_c.llm_client:
            return self._get_offline_fallback(news_sentiment, news_impact, current_sentiment, current_conviction, current_reactivity, "Offline Mode")

        # Dynamically compile the system prompt based on their current active StateManager parameters
        active_system_prompt = self.room_c.get_primed_agent_prompt(
            company_profile=self.company_profile,
            agent_name=self.persona.name,
            personas=self.personas,
            current_sentiment=current_sentiment,
            current_conviction=current_conviction,
            current_reactivity=current_reactivity
        )

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
            # Fall back gracefully to offline mock if rate limits or network issues happen
            try:
                print(f"[DEBATE WARNING] Failed to generate speech online for {self.persona.name} ({repr(e)}). Gracefully falling back to rules-based argument.")
            except Exception:
                pass
            return self._get_offline_fallback(news_sentiment, news_impact, current_sentiment, current_conviction, current_reactivity, f"Rate Limit / Error Fallback")


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

        # Ensure max_turns is scaled to allow all agents to meet their turn quotas.
        # For 14 agents with a target average of 7 arguments each, this guarantees at least 98 turns.
        target_avg_turns = 7
        min_turns_needed = len(self.agents) * target_avg_turns
        max_turns = max(max_rounds * 10, min_turns_needed)

        agent = self.moderator.pop_next_speaker()

        # --- THE MAIN DEBATE LOOP ---
        while turn_count < max_turns and agent is not None:
            # A. Check if the room has reached consensus
            if self.moderator.should_stop_debate(self.room_d, turn_count):
                break

            # Pacing delay: add a 6-second delay between turns to respect free-tier rate limits
            if turn_count > 0:
                await asyncio.sleep(6.0)

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
                    # Pacing delay: add a 6-second delay between wrap-up turns
                    await asyncio.sleep(6.0)

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