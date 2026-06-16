import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("finswarm.llm_client")

class GeminiLlmClient:
    """
    GeminiLlmClient
    Wrapper around the Google GenAI/GenerativeAI SDK to handle communication
    with Gemini models, retrieve structured JSON responses, and manage context caching.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client_configured = False
        
        self.cache_object = None
        self.cache_created_at = None
        
        if not self.api_key:
            # FATAL ERROR: Stop the app right here instead of faking the connection.
            raise ValueError("CRITICAL: GEMINI_API_KEY environment variable is missing. The simulation cannot run.")
            
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client_configured = True
            logger.info("Gemini LLM Client configured successfully.")
        except ImportError:
            raise ImportError("CRITICAL: google-generativeai library is not installed. Run 'pip install google-generativeai'.")

    def create_context_cache(self, company_profile_str: str, agents_list_str: str) -> Optional[str]:
        """
        Creates a context cache on the Gemini server containing company profile and agents.
        Appends padding to cross the 32,768 token threshold for caching.
        Returns the cache name (e.g. 'cachedContents/xyz') or None if caching fails or is unsupported.
        """
        if not self.client_configured:
            return None
            
        try:
            import google.generativeai as genai
            from google.generativeai import caching
            import datetime
            
            # Check if cache is still valid (within 25 mins, TTL is 30 mins)
            if self.cache_object and self.cache_created_at:
                age = datetime.datetime.now() - self.cache_created_at
                if age < datetime.timedelta(minutes=25):
                    logger.info(f"Reusing existing context cache: {self.cache_object.name}")
                    return self.cache_object.name
            
            # Generate padding (160KB of dummy context to cross the 32,768 token threshold)
            padding_text = "Finswarm Quantitative financial reference data directory. " * 5000
            
            caching_input = f"""=== GROUND TRUTH SYSTEM CACHE ===
=== REFERENCE DIRECTORY ===
{padding_text}

=== GROUND TRUTH COMPANY CONTEXT ===
{company_profile_str}

=== SWARM AGENTS DIRECTORY ===
{agents_list_str}
"""
            
            logger.info("Creating new context cache on Gemini server...")
            # Create CachedContent on Gemini
            cache = caching.CachedContent.create(
                model='models/gemini-1.5-flash-001',
                display_name='finswarm_debate_context_cache',
                contents=[caching_input],
                ttl=datetime.timedelta(minutes=30)
            )
            
            self.cache_object = cache
            self.cache_created_at = datetime.datetime.now()
            logger.info(f"Context cache created successfully: {cache.name}")
            return cache.name
            
        except Exception as e:
            # Note: Caching is a performance optimization. If caching fails (e.g., API limits), 
            # we gracefully fall back to stateless mode rather than breaking the simulation entirely.
            logger.warning(f"Failed to create Gemini context cache ({e}). Gracefully falling back to stateless prompt mode.")
            self.cache_object = None
            self.cache_created_at = None
            return None

    async def generate_json(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        response_schema: Optional[Any] = None,
        cached_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calls Gemini API asynchronously and enforces a JSON response format.
        Supports using a server-side context cache.
        Throws clear exceptions on failure instead of suppressing them.
        """
        if not self.client_configured:
            raise ValueError("Gemini API client is not configured. Set GEMINI_API_KEY environment variable.")

        import google.generativeai as genai

        generation_config = {
            "response_mime_type": "application/json"
        }
        if response_schema:
            generation_config["response_schema"] = response_schema

        # If cache is provided and active, instantiate model from cache
        if cached_content:
            try:
                cache_ref = self.cache_object if self.cache_object and self.cache_object.name == cached_content else cached_content
                model = genai.GenerativeModel.from_cached_content(
                    cached_content=cache_ref,
                    generation_config=generation_config
                )
            except Exception as e:
                logger.warning(f"Error loading model from cached content ({e}). Falling back to standard model.")
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=system_prompt,
                    generation_config=generation_config
                )
        else:
            model_name = "gemini-1.5-flash"
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt,
                generation_config=generation_config
            )

        # Call Gemini asynchronously. Will raise exception if the API is down or rate-limited.
        response = await model.generate_content_async(prompt)
        response_text = response.text.strip()

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            # Fallback parsing in case of markdown formatting markers
            logger.warning(f"Failed to parse raw JSON: {e}. Attempting formatting cleanup.")
            cleaned_text = response_text
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            try:
                return json.loads(cleaned_text.strip())
            except json.JSONDecodeError:
                # Fatal error: AI output cannot be read by the system.
                raise ValueError(f"CRITICAL: Failed to decode response from Gemini as JSON: {response_text}")