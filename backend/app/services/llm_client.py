import os
import json
import re
import asyncio
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
                model='models/gemini-3.5-flash',
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
        cached_content: Optional[str] = None,
        model_name: str = "gemini-2.0-flash-lite"
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
                    model_name=model_name,
                    system_instruction=system_prompt,
                    generation_config=generation_config
                )
        else:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt,
                generation_config=generation_config
            )

        # Call Gemini asynchronously with robust rate-limit backoff retries
        success = False
        attempts = 0
        response = None
        model_pool = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]

        while not success and attempts < 3:
            attempts += 1
            current_model_name = model_pool[(attempts - 1) % len(model_pool)]
            try:
                current_model = genai.GenerativeModel(
                    model_name=current_model_name,
                    system_instruction=system_prompt,
                    generation_config=generation_config
                )
                response = await current_model.generate_content_async(prompt)
                success = True
            except Exception as api_err:
                err_str = str(api_err)
                if "429" in err_str or "Quota" in err_str or "ResourceExhausted" in err_str:
                    logger.warning(f"Rate limit hit for {current_model_name}, attempt #{attempts}/3...")
                    await asyncio.sleep(2.0)
                else:
                    logger.warning(f"Gemini API error using {current_model_name}: {api_err}")
                    if attempts >= 2:
                        raise api_err
                    await asyncio.sleep(1.0)

        if not response or not hasattr(response, "text"):
            raise ValueError("Failed to obtain valid response text from Gemini API after retries.")

        response_text = response.text.strip()

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse raw JSON: {e}. Attempting formatting cleanup and regex extraction.")
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            # Try parsing cleaned text
            try:
                return json.loads(cleaned_text)
            except json.JSONDecodeError:
                pass
                
            # Regex match outer JSON braces { ... }
            match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            
            # Auto-repair missing closing brackets/braces if truncated
            repaired = cleaned_text
            if not repaired.endswith("}"):
                if not repaired.endswith("]"):
                    repaired += "]"
                repaired += "\n}"
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                raise ValueError(f"CRITICAL: Failed to decode response from Gemini as JSON: {response_text}")