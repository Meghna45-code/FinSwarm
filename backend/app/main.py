import os
import sys
import logging
import json
import hashlib
import hmac
import base64
import time
import secrets
import jwt
from typing import Optional, Dict, Any, List
from dataclasses import asdict
import re

# Set up logger
logger = logging.getLogger("finswarm.main")

# Dynamically resolve project root and add to sys.path to allow launching from any directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables from .env file if it exists
env_path = os.path.join(project_root, ".env")
if os.path.exists(env_path):
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip("\"'")
    except Exception as e:
        logger.warning(f"Failed to load .env file: {e}")

from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from backend.app.services.personas import initialize_personas, CompanyProfile, AgentPersona
from backend.app.services.llm_orchestrator import LlmOrchestrator
from backend.app.services.state_manager import StateManager
from backend.app.services.debate_room import DebateRoom
from backend.app.services.moderator import ModeratorAgent
from backend.app.services.llm_client import GeminiLlmClient

app = FastAPI(title="FinSwarm API", version="1.0.0")

# Secure local development CORS configuration
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://[::1]:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://[::1]:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SECURITY UTILITIES & CONFIGURATIONS ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "finswarm-super-secret-key-12345-xyz")
security = HTTPBearer(auto_error=False)

def hash_password(password: str, salt: str = None) -> tuple:
    """Hashes a password using PBKDF2 with SHA-256."""
    if not salt:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return dk.hex(), salt

def generate_token(email: str, expires_in_seconds: int = 604800) -> str:
    """Generates a secure JWT session token."""
    payload = {
        "sub": email,
        "exp": int(time.time()) + expires_in_seconds
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> Optional[str]:
    """Verifies a JWT token and returns the user's email if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """Dependency to retrieve the active authorized user email from Authorization headers."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")
    token = credentials.credentials
    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")
    return email

async def get_token_user_or_guest(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """Returns the authenticated user email, or defaults to guest if token is missing or invalid."""
    if not credentials:
        return "guest@finswarm.local"
    token = credentials.credentials
    email = verify_token(token)
    return email or "guest@finswarm.local"

def sanitize_ticker(ticker: str) -> str:
    """Sanitizes ticker inputs to prevent parameter injection."""
    if not ticker:
        return ""
    cleaned = re.sub(r'[^A-Za-z0-9.-]', '', ticker)
    return cleaned.upper().strip()[:10]

def sanitize_company_query(query: str) -> str:
    """Sanitizes a company name or ticker query. Allows letters, numbers, spaces, dots and hyphens.
    Accepts both ticker symbols (AAPL) and full company names (Google, Goldman Sachs).
    """
    if not query:
        return ""
    # Allow letters, digits, spaces, dots, hyphens — strip anything else
    cleaned = re.sub(r'[^A-Za-z0-9 .\-&]', '', query)
    return cleaned.strip()[:60]

def sanitize_news_content(content: str) -> str:
    """Sanitizes news content inputs to prevent prompt injection."""
    if not content:
        return ""
    injection_patterns = [
        r"(?i)ignore\s+(?:all\s+)?(?:previous\s+)?instructions",
        r"(?i)ignore\s+(?:all\s+)?(?:previous\s+)?guidelines",
        r"(?i)ignore\s+(?:all\s+)?(?:previous\s+)?directives",
        r"(?i)disregard\s+(?:previous\s+)?directives",
        r"(?i)disregard\s+(?:previous\s+)?instructions",
        r"(?i)system\s+override",
        r"(?i)override\s+system",
        r"(?i)bypass\s+constraints",
        r"(?i)bypass\s+safety",
        r"(?i)bypass\s+rules",
        r"(?i)forget\s+(?:all\s+)?rules",
        r"(?i)forget\s+(?:all\s+)?guidelines",
        r"(?i)forget\s+(?:all\s+)?instructions",
        r"(?i)you\s+must\s+now\s+act\s+as",
        r"(?i)you\s+are\s+now\s+a\s+",
        r"(?i)jailbreak",
        r"(?i)jailbroken",
        r"(?i)dan\s+mode",
        r"(?i)developer\s+mode",
        r"(?i)do\s+anything\s+now"
    ]
    cleaned = content
    for pattern in injection_patterns:
        cleaned = re.sub(pattern, "[CLEANED INJECTION ATTEMPT]", cleaned)
    return cleaned.strip()

# --- REQUEST SCHEMAS ---
class RegisterRequest(BaseModel):
    email: str
    display_name: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class VerifyPinRequest(BaseModel):
    email: str
    pin: str

class UpdateProfileRequest(BaseModel):
    display_name: str

class ResetPasswordRequest(BaseModel):
    email: str
    pin: str
    new_password: str

class SimulationRequest(BaseModel):
    news_content: str
    max_rounds: Optional[int] = 2
    custom_agents: Optional[Dict[str, Any]] = None
    environmental_variables: Optional[Dict[str, str]] = None
    existing_transcript: Optional[List[Dict[str, Any]]] = None
    existing_state_history: Optional[List[Dict[str, Any]]] = None
    debate_id: Optional[str] = None

class ContextualizeRequest(BaseModel):
    environmental_variables: Optional[Dict[str, str]] = None
    company_profile: Optional[Dict[str, Any]] = None

class CommandRequest(BaseModel):
    command: str
    current_agents: Dict[str, Any]
    environmental_variables: Optional[Dict[str, str]] = None
    company_profile: Optional[Dict[str, Any]] = None

class UrlRequest(BaseModel):
    url: str

# ==========================================
# MULTIMODAL INGESTION & SCRAPING ENDPOINTS
# ==========================================

@app.post("/api/upload-file")
async def upload_file_endpoint(file: UploadFile = File(...), email: str = Depends(get_current_user)):
    """Universal router that delegates extraction based on file extension."""
    try:
        contents = await file.read()
        filename = file.filename.lower()
        
        # --- DOCUMENT PARSERS ---
        if filename.endswith(".pdf"):
            from backend.app.services.file_parser import extract_pdf_text
            text = extract_pdf_text(contents)
            
        elif filename.endswith(".docx"):
            from backend.app.services.file_parser import extract_docx_text
            text = extract_docx_text(contents)
            
        elif filename.endswith((".xlsx", ".xls")):
            from backend.app.services.file_parser import extract_excel_text
            text = extract_excel_text(contents)
            
        elif filename.endswith((".pptx", ".ppt")):
            from backend.app.services.file_parser import extract_ppt_text
            text = extract_ppt_text(contents)
            
        elif filename.endswith((".txt", ".csv")):
            text = contents.decode("utf-8", errors="ignore")
            
        # --- MEDIA PARSERS ---
        elif filename.endswith((".mp3", ".wav", ".m4a")):
            from backend.app.services.media_parser import transcribe_audio
            text = await transcribe_audio(contents)
            
        elif filename.endswith(".mp4"):
            from backend.app.services.media_parser import transcribe_video
            text = await transcribe_video(contents)
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        return {"text": text}
    except ModuleNotFoundError as e:
        logger.warning(f"Parsing module not yet implemented: {e}")
        raise HTTPException(status_code=501, detail="This file parser is not yet implemented.")
    except Exception as e:
        logger.exception("Error in upload_file_endpoint")
        raise HTTPException(status_code=500, detail=f"Internal server error parsing file: {str(e)}")

@app.post("/api/upload-pdf")
async def upload_pdf_endpoint(file: UploadFile = File(...), email: str = Depends(get_current_user)):
    """Alias for /api/upload-file, specifically for PDF uploads from the frontend."""
    try:
        contents = await file.read()
        filename = file.filename.lower()
        if filename.endswith(".pdf"):
            from backend.app.services.file_parser import extract_pdf_text
            text = extract_pdf_text(contents)
        elif filename.endswith((".txt", ".csv")):
            text = contents.decode("utf-8", errors="ignore")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format for PDF upload endpoint")
        return {"text": text}
    except ModuleNotFoundError as e:
        logger.warning(f"Parsing module not yet implemented: {e}")
        raise HTTPException(status_code=501, detail="PDF parser not yet implemented.")
    except Exception as e:
        logger.exception("Error in upload_pdf_endpoint")
        raise HTTPException(status_code=500, detail=f"Internal server error parsing PDF: {str(e)}")

@app.post("/api/parse-url")
async def parse_url_endpoint(req: UrlRequest, email: str = Depends(get_current_user)):
    """Delegates a web link to the web scraper to extract the site's text content."""
    try:
        from backend.app.services.web_scraper import scrape_url
        text = await scrape_url(req.url)
        return {"text": text}
    except ModuleNotFoundError:
        raise HTTPException(status_code=501, detail="Web scraper module not yet implemented.")
    except Exception as e:
        logger.exception("Error in parse_url_endpoint")
        raise HTTPException(status_code=500, detail=f"Error scraping URL: {str(e)}")

@app.post("/api/dictate")
async def dictate_endpoint(audio: UploadFile = File(...), email: str = Depends(get_current_user)):
    """Dedicated endpoint for live speech-to-text dictation."""
    try:
        contents = await audio.read()
        from backend.app.services.media_parser import transcribe_audio
        text = await transcribe_audio(contents)
        return {"text": text}
    except ModuleNotFoundError:
        raise HTTPException(status_code=501, detail="Audio transcription module not yet implemented.")
    except Exception as e:
        logger.exception("Error in dictate_endpoint")
        raise HTTPException(status_code=500, detail=f"Error transcribing dictation: {str(e)}")

# --- AUTHENTICATION ENDPOINTS ---

@app.post("/api/auth/register")
def register_endpoint(req: RegisterRequest):
    email = req.email.lower().strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    from backend.app.services.database import get_user, create_user
    existing = get_user(email)
    if existing:
        raise HTTPException(status_code=400, detail="User already registered with this email")
    
    hash_val, salt = hash_password(req.password)
    success = create_user(email, req.display_name, hash_val, salt)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create user account")
    
    return {"message": "User registered successfully"}

@app.post("/api/auth/login")
def login_endpoint(req: LoginRequest):
    email = req.email.lower().strip()
    from backend.app.services.database import get_user
    user = get_user(email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    expected_hash, salt = hash_password(req.password, user["salt"])
    if not hmac.compare_digest(user["password_hash"], expected_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = generate_token(email)
    return {
        "access_token": token,
        "display_name": user["display_name"],
        "email": email
    }

@app.post("/api/auth/forgot-password")
def forgot_password_endpoint(req: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    email = req.email.lower().strip()
    from backend.app.services.database import get_user, set_reset_pin
    user = get_user(email)
    if not user:
        return {"message": "If the email exists, a password reset PIN has been sent."}
    
    pin = "".join(secrets.choice("0123456789") for _ in range(6))
    success = set_reset_pin(email, pin, 600)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to generate reset PIN")
    
    if os.getenv("ENV", "development").lower() == "development":
        print(f"\n========================================================")
        print(f"[SECURITY PIN LOG] Password reset request for: {email}")
        print(f"OTP Reset PIN: {pin}")
        print(f"========================================================\n")
    
    from backend.app.services.email_service import send_reset_email
    background_tasks.add_task(send_reset_email, email, pin)
    
    return {"message": "If the email exists, a password reset PIN has been sent."}

@app.post("/api/auth/reset-password")
def reset_password_endpoint(req: ResetPasswordRequest):
    email = req.email.lower().strip()
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    from backend.app.services.database import get_user, update_user_password
    import datetime
    user = get_user(email)
    if not user or not user.get("reset_pin") or not user.get("reset_pin_expires"):
        raise HTTPException(status_code=400, detail="Invalid or expired reset PIN")
    
    expires_str = user["reset_pin_expires"]
    try:
        expires = datetime.datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
        if datetime.datetime.utcnow() > expires:
            raise HTTPException(status_code=400, detail="Invalid or expired reset PIN")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset PIN")
    
    expected_hash, _ = hash_password(req.pin, user["salt"])
    if not hmac.compare_digest(user["reset_pin"], expected_hash):
        raise HTTPException(status_code=400, detail="Invalid or expired reset PIN")
    
    hash_val, salt = hash_password(req.new_password)
    success = update_user_password(email, hash_val, salt)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password")
    
    return {"message": "Password reset successfully"}

@app.post("/api/auth/verify-reset-pin")
def verify_reset_pin_endpoint(req: VerifyPinRequest):
    email = req.email.lower().strip()
    from backend.app.services.database import get_user
    import datetime
    user = get_user(email)
    if not user or not user.get("reset_pin") or not user.get("reset_pin_expires"):
        raise HTTPException(status_code=400, detail="Invalid or expired reset PIN")
    
    expires_str = user["reset_pin_expires"]
    try:
        expires = datetime.datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
        if datetime.datetime.utcnow() > expires:
            raise HTTPException(status_code=400, detail="Invalid or expired reset PIN")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset PIN")
    
    expected_hash, _ = hash_password(req.pin, user["salt"])
    if not hmac.compare_digest(user["reset_pin"], expected_hash):
        raise HTTPException(status_code=400, detail="Invalid or expired reset PIN")
    
    return {"message": "PIN verified successfully"}

@app.post("/api/auth/update-profile")
def update_profile_endpoint(req: UpdateProfileRequest, email: str = Depends(get_current_user)):
    from backend.app.services.database import get_connection
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET display_name = ? WHERE email = ?", (req.display_name, email))
        conn.commit()
        return {"message": "Profile updated successfully", "display_name": req.display_name}
    except Exception as e:
        logger.exception("Error in update_profile_endpoint")
        raise HTTPException(status_code=500, detail="Failed to update profile details")
    finally:
        conn.close()

# --- SYSTEM & SIMULATION ENDPOINTS ---


@app.get("/api/personas")
def get_personas():
    """Returns the baseline agent personas. No authentication required — these are static templates."""
    try:
        personas = initialize_personas()
        return {name: asdict(p) for name, p in personas.items()}
    except Exception as e:
        logger.exception("Error in /api/personas")
        raise HTTPException(status_code=500, detail="Internal server error")


def get_default_company_profile() -> CompanyProfile:
    from backend.app.services.mock_fallbacks import generate_offline_company_profile
    return generate_offline_company_profile("Tesla")


@app.get("/api/company")
async def get_company(ticker: Optional[str] = None, x_gemini_api_key: Optional[str] = Header(None)):
    try:
        if not ticker or ticker.upper().strip() == "TSLA":
            return get_default_company_profile()
        
        # Use broad sanitizer that accepts company names like "Google" or "Goldman Sachs"
        query_cleaned = sanitize_company_query(ticker)
        if not query_cleaned:
            return get_default_company_profile()

        api_key = x_gemini_api_key or os.getenv("GEMINI_API_KEY")
        llm_client = GeminiLlmClient(api_key=api_key) if api_key else None
        room_c = LlmOrchestrator(llm_client=llm_client)
        
        profile = await room_c.generate_profile_for_ticker(query_cleaned)
        return profile
    except Exception as e:
        logger.exception("Error in /api/company")
        raise HTTPException(status_code=500, detail="Internal server error fetching company profile")

@app.post("/api/agents/autofill")
async def autofill_agent_endpoint(req: Dict[str, Any], email: str = Depends(get_token_user_or_guest), x_gemini_api_key: Optional[str] = Header(None)):
    try:
        api_key = x_gemini_api_key or os.getenv("GEMINI_API_KEY")
        llm_client = GeminiLlmClient(api_key=api_key) if api_key else None
        room_c = LlmOrchestrator(llm_client=llm_client)
        
        env_vars = req.get("environmental_variables")
        comp_raw = req.get("company_profile")
        
        company_profile = None
        if comp_raw:
            company_profile = CompanyProfile(
                ticker=comp_raw.get("ticker", "TSLA"),
                name=comp_raw.get("name", "Tesla Inc"),
                sector=comp_raw.get("sector", ""),
                industry=comp_raw.get("industry", ""),
                description=comp_raw.get("description", ""),
                key_metrics=comp_raw.get("key_metrics", {}),
                recent_events=comp_raw.get("recent_events", []),
                historical_news=comp_raw.get("historical_news", [])
            )
        
        agent_details = req.get("agent", req)
        completed_persona = await room_c.autofill_agent_persona(
            partial_persona=agent_details,
            environmental_variables=env_vars,
            company_profile=company_profile
        )
        return completed_persona
    except Exception as e:
        logger.exception("Error in autofill_agent_endpoint")
        raise HTTPException(status_code=500, detail="Internal server error during persona autofill")

@app.post("/api/personas/contextualize")
async def contextualize_personas_endpoint(req: ContextualizeRequest, email: str = Depends(get_token_user_or_guest), x_gemini_api_key: Optional[str] = Header(None)):
    try:
        api_key = x_gemini_api_key or os.getenv("GEMINI_API_KEY")
        llm_client = GeminiLlmClient(api_key=api_key) if api_key else None
        room_c = LlmOrchestrator(llm_client=llm_client)
        
        comp_raw = req.company_profile
        if comp_raw:
            profile = CompanyProfile(
                ticker=comp_raw.get("ticker", "TSLA"),
                name=comp_raw.get("name", "Tesla Inc"),
                sector=comp_raw.get("sector", ""),
                industry=comp_raw.get("industry", ""),
                description=comp_raw.get("description", ""),
                key_metrics=comp_raw.get("key_metrics", {}),
                recent_events=comp_raw.get("recent_events", []),
                historical_news=comp_raw.get("historical_news", [])
            )
        else:
            profile = get_default_company_profile()
        
        default_personas = initialize_personas()
        env_vars = req.environmental_variables or {}
        
        adjusted_personas = await room_c.contextualize_personas(
            company_profile=profile,
            environmental_variables=env_vars,
            default_personas=default_personas
        )
        return adjusted_personas
    except Exception as e:
        logger.exception("Error in contextualize_personas_endpoint")
        raise HTTPException(status_code=500, detail="Internal server error during contextualization")

@app.post("/api/agents/command")
async def process_swarm_command_endpoint(req: CommandRequest, email: str = Depends(get_token_user_or_guest), x_gemini_api_key: Optional[str] = Header(None)):
    try:
        req.command = sanitize_news_content(req.command)
        api_key = x_gemini_api_key or os.getenv("GEMINI_API_KEY")
        llm_client = GeminiLlmClient(api_key=api_key) if api_key else None
        room_c = LlmOrchestrator(llm_client=llm_client)
        
        comp_raw = req.company_profile
        if comp_raw:
            profile = CompanyProfile(
                ticker=comp_raw.get("ticker", "TSLA"),
                name=comp_raw.get("name", "Tesla Inc"),
                sector=comp_raw.get("sector", ""),
                industry=comp_raw.get("industry", ""),
                description=comp_raw.get("description", ""),
                key_metrics=comp_raw.get("key_metrics", {}),
                recent_events=comp_raw.get("recent_events", []),
                historical_news=comp_raw.get("historical_news", [])
            )
        else:
            profile = get_default_company_profile()
        
        env_vars = req.environmental_variables or {}
        updated_personas = await room_c.process_swarm_command(
            command=req.command,
            current_agents=req.current_agents,
            environmental_variables=env_vars,
            company_profile=profile
        )
        return updated_personas
    except Exception as e:
        logger.exception("Error in process_swarm_command_endpoint")
        raise HTTPException(status_code=500, detail="Internal server error processing command")

def safe_float(val, default: float = 0.0) -> float:
    try:
        if val is None or val == "":
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

@app.post("/api/simulate")
async def run_simulation_endpoint(req: SimulationRequest, email: str = Depends(get_token_user_or_guest), x_gemini_api_key: Optional[str] = Header(None)):
    req.news_content = sanitize_news_content(req.news_content)
    print(f"--- [API DEBUG] Received simulate request by {email} for: {req.news_content[:50]}... ---")
    try:
        api_key = x_gemini_api_key or os.getenv("GEMINI_API_KEY")
        llm_client = GeminiLlmClient(api_key=api_key) if api_key else None
        
        if req.custom_agents:
            personas = {}
            for name, details in req.custom_agents.items():
                personas[name] = AgentPersona(
                    name=details.get("name", name),
                    swarm_type=details.get("swarm_type", "Trading & Analytical Swarm"),
                    role_identity=details.get("role_identity", ""),
                    primary_metrics=details.get("primary_metrics", []),
                    cognitive_biases=details.get("cognitive_biases", []),
                    linguistic_style=details.get("linguistic_style", ""),
                    good_news_reaction=details.get("good_news_reaction", ""),
                    bad_news_reaction=details.get("bad_news_reaction", ""),
                    initial_sentiment=safe_float(details.get("initial_sentiment"), 0.0),
                    initial_conviction=safe_float(details.get("initial_conviction"), 0.5),
                    reactivity_threshold=safe_float(details.get("reactivity_threshold"), 0.3)
                )
        else:
            personas = initialize_personas()
            
        room_c = LlmOrchestrator(llm_client=llm_client)
        profile = await room_c.extract_and_generate_profile(req.news_content)
        profile.environmental_variables = req.environmental_variables
        
        room_d = StateManager(personas=personas)
        moderator = ModeratorAgent(profile, room_c)
        room_b = DebateRoom(
            company_profile=profile,
            personas=personas,
            moderator=moderator,
            room_c=room_c,
            room_d=room_d
        )
        
        cache_name = None
        if llm_client:
            try:
                profile_str = room_c._format_company_profile(profile)
                agents_str = "\n".join([
                    f"Agent: {p.name}\nRole: {p.role_identity}\nStyle: {p.linguistic_style}\nMetrics: {p.primary_metrics}\nBiases: {p.cognitive_biases}"
                    for p in personas.values()
                ])
                cache_name = llm_client.create_context_cache(profile_str, agents_str)
            except Exception as e:
                print(f"[API CACHE WARNING] Could not construct context cache payload: {e}")

        async def event_generator():
            import uuid
            debate_id = req.debate_id or f"deb_{uuid.uuid4().hex[:8]}"
            yield f"data: {json.dumps({'type': 'debate_id', 'data': debate_id})}\n\n"
            
            news_sentiment = 0.0
            news_impact = 0.0
            debate_summary = ""
            valuation_results = {}
            turns_dict = {}

            if req.existing_transcript:
                for turn in req.existing_transcript:
                    turn_num = turn.get("turn", 0)
                    turns_dict[turn_num] = {
                        "turn": turn_num,
                        "speaker": turn.get("speaker", ""),
                        "speech": turn.get("speech", ""),
                        "internal_monologue": turn.get("internal_monologue", ""),
                        "sentiment_after": turn.get("sentiment_after", 0.0),
                        "conviction_after": turn.get("conviction_after", 0.5),
                        "moderator_note": turn.get("moderator_note"),
                        "is_factually_correct": turn.get("is_factually_correct", True),
                        "factuality_score": turn.get("factuality_score", 1.0),
                        "cited_source": turn.get("cited_source")
                    }
            try:
                yield f"data: {json.dumps({'type': 'company_profile', 'data': asdict(profile)})}\n\n"
                
                async for event in room_b.run_simulation_generator(
                    req.news_content,
                    max_rounds=req.max_rounds,
                    existing_transcript=req.existing_transcript,
                    existing_state_history=req.existing_state_history,
                    cached_content=cache_name
                ):
                    if event["type"] == "news_analysis":
                        news_sentiment = event["data"].get("sentiment", 0.0)
                        news_impact = event["data"].get("impact", 0.0)
                    elif event["type"] == "turn":
                        turn_data = event["data"]
                        turn_num = turn_data.get("turn", 0)
                        turns_dict[turn_num] = {
                            "turn": turn_num,
                            "speaker": turn_data.get("speaker", ""),
                            "speech": turn_data.get("speech", ""),
                            "internal_monologue": turn_data.get("internal_monologue", ""),
                            "sentiment_after": turn_data.get("sentiment_after", 0.0),
                            "conviction_after": turn_data.get("conviction_after", 0.5),
                            "moderator_note": None,
                            "is_factually_correct": True,
                            "factuality_score": 1.0,
                            "cited_source": None
                        }
                    elif event["type"] == "fact_check":
                        fc_data = event["data"]
                        turn_num = fc_data.get("turn", 0)
                        if turn_num in turns_dict:
                            turns_dict[turn_num]["moderator_note"] = fc_data.get("moderator_note")
                            turns_dict[turn_num]["is_factually_correct"] = fc_data.get("is_factually_correct", True)
                            turns_dict[turn_num]["factuality_score"] = fc_data.get("factuality_score", 1.0)
                            turns_dict[turn_num]["cited_source"] = fc_data.get("cited_source")
                    elif event["type"] == "verdict":
                        debate_summary = event["data"].get("debate_summary", "")
                        valuation_results = event["data"].get("valuation", {})
                        
                    yield f"data: {json.dumps(event)}\n\n"

                turns_list = [turns_dict[k] for k in sorted(turns_dict.keys())]
                from backend.app.services.database import save_debate
                save_debate(
                    debate_id=debate_id,
                    news_content=req.news_content,
                    news_sentiment=news_sentiment,
                    news_impact=news_impact,
                    company_name=profile.name,
                    company_ticker=profile.ticker,
                    company_profile=asdict(profile),
                    debate_summary=debate_summary,
                    valuation_results=valuation_results,
                    turns=turns_list,
                    user_email=email
                )
            except Exception as e:
                import traceback
                print(f"[SSE EVENT GENERATOR ERROR] {e}")
                traceback.print_exc()
                yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        logger.exception("Error in run_simulation_endpoint")
        raise HTTPException(status_code=500, detail="Internal server error initiating simulation")

@app.get("/api/debates")
def get_debates_endpoint(email: str = Depends(get_token_user_or_guest)):
    try:
        from backend.app.services.database import get_all_debates
        return get_all_debates(email)
    except Exception as e:
        logger.exception("Error in get_debates_endpoint")
        raise HTTPException(status_code=500, detail="Internal server error fetching debates")

@app.get("/api/debates/{debate_id}")
def get_debate_details_endpoint(debate_id: str, email: str = Depends(get_token_user_or_guest)):
    try:
        from backend.app.services.database import get_debate_details
        details = get_debate_details(debate_id, email)
        if not details:
            raise HTTPException(status_code=404, detail="Debate not found")
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in get_debate_details_endpoint")
        raise HTTPException(status_code=500, detail="Internal server error fetching debate details")

# --- STATIC FILES MOUNT ---
frontend_dir = os.path.join(project_root, "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")