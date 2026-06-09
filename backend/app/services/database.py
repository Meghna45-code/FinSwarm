import os
import json
import sqlite3
import logging
from typing import Dict, Any, List

logger = logging.getLogger("finswarm.database")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "finswarm.db")

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes database tables if they do not exist, and applies schema updates."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 1. Create Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                display_name TEXT,
                password_hash TEXT,
                salt TEXT,
                reset_pin TEXT,
                reset_pin_expires TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Create Debates Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS debates (
                id TEXT PRIMARY KEY,
                news_content TEXT,
                news_sentiment REAL,
                news_impact REAL,
                company_name TEXT,
                company_ticker TEXT,
                company_profile TEXT,
                debate_summary TEXT,
                valuation_results TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Alter debates schema to add user_email column if missing (auto-migration)
        try:
            cursor.execute("SELECT user_email FROM debates LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE debates ADD COLUMN user_email TEXT")
            cursor.execute("UPDATE debates SET user_email = 'guest@finswarm.local' WHERE user_email IS NULL")
            logger.info("Migrated debates table: Added user_email field.")
        
        # 3. Create Turns Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                debate_id TEXT,
                turn_num INTEGER,
                speaker TEXT,
                speech TEXT,
                internal_monologue TEXT,
                sentiment_after REAL,
                conviction_after REAL,
                moderator_note TEXT,
                factuality_score REAL,
                cited_source TEXT,
                is_factually_correct INTEGER,
                FOREIGN KEY(debate_id) REFERENCES debates(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        logger.info(f"Database initialized successfully at: {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    finally:
        conn.close()

# --- USER HANDLERS ---

def create_user(email: str, display_name: str, password_hash: str, salt: str) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, display_name, password_hash, salt) VALUES (?, ?, ?, ?)",
            (email.lower().strip(), display_name, password_hash, salt)
        )
        conn.commit()
        logger.info(f"Created user: {email}")
        return True
    except Exception as e:
        logger.exception(f"Failed to create user {email}: {e}")
        return False
    finally:
        conn.close()

def get_user(email: str) -> Dict[str, Any]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
        row = cursor.fetchone()
        return dict(row) if row else {}
    except Exception as e:
        logger.exception(f"Failed to fetch user {email}: {e}")
        return {}
    finally:
        conn.close()

def set_reset_pin(email: str, pin: str, expires_seconds: int) -> bool:
    import datetime
    from backend.app.main import hash_password
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Get user's salt
        cursor.execute("SELECT salt FROM users WHERE email = ?", (email.lower().strip(),))
        row = cursor.fetchone()
        salt = row["salt"] if row else None
        if not salt:
            return False
            
        # Hash the reset pin using user's salt
        hashed_pin, _ = hash_password(pin, salt)
        
        expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_seconds)
        cursor.execute(
            "UPDATE users SET reset_pin = ?, reset_pin_expires = ? WHERE email = ?",
            (hashed_pin, expires.strftime("%Y-%m-%d %H:%M:%S"), email.lower().strip())
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.exception(f"Failed to set reset pin for {email}: {e}")
        return False
    finally:
        conn.close()


def update_user_password(email: str, password_hash: str, salt: str) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = ?, salt = ?, reset_pin = NULL, reset_pin_expires = NULL WHERE email = ?",
            (password_hash, salt, email.lower().strip())
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.exception(f"Failed to update password for {email}: {e}")
        return False
    finally:
        conn.close()

# --- DEBATE HANDLERS ---

def save_debate(
    debate_id: str,
    news_content: str,
    news_sentiment: float,
    news_impact: float,
    company_name: str,
    company_ticker: str,
    company_profile: Dict[str, Any],
    debate_summary: str,
    valuation_results: Dict[str, Any],
    turns: List[Dict[str, Any]],
    user_email: str = "guest@finswarm.local"
) -> bool:
    """Saves a full debate run including all individual turns to the database, owned by user_email."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Insert or replace debate
        cursor.execute("""
            INSERT OR REPLACE INTO debates (
                id, news_content, news_sentiment, news_impact, 
                company_name, company_ticker, company_profile, 
                debate_summary, valuation_results, user_email
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            debate_id,
            news_content,
            news_sentiment,
            news_impact,
            company_name,
            company_ticker,
            json.dumps(company_profile),
            debate_summary,
            json.dumps(valuation_results),
            user_email.lower().strip()
        ))
        
        # Delete existing turns for this debate_id first to prevent duplicates
        cursor.execute("DELETE FROM turns WHERE debate_id = ?", (debate_id,))
        
        # Insert turns
        for turn in turns:
            cursor.execute("""
                INSERT INTO turns (
                    debate_id, turn_num, speaker, speech, internal_monologue,
                    sentiment_after, conviction_after, moderator_note,
                    factuality_score, cited_source, is_factually_correct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                debate_id,
                turn.get("turn", 0),
                turn.get("speaker", ""),
                turn.get("speech", ""),
                turn.get("internal_monologue", ""),
                turn.get("sentiment_after", 0.0),
                turn.get("conviction_after", 0.5),
                turn.get("moderator_note"),
                turn.get("factuality_score", 1.0),
                turn.get("cited_source"),
                1 if turn.get("is_factually_correct", True) else 0
            ))
            
        conn.commit()
        logger.info(f"Successfully saved debate session {debate_id} for user {user_email}")
        return True
    except Exception as e:
        logger.exception(f"Failed to save debate session: {e}")
        return False
    finally:
        conn.close()

def get_all_debates(user_email: str = "guest@finswarm.local") -> List[Dict[str, Any]]:
    """Retrieves all debates summaries from history belonging to a specific user."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, news_content, company_name, company_ticker, created_at
            FROM debates
            WHERE user_email = ?
            ORDER BY created_at DESC
        """, (user_email.lower().strip(),))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.exception(f"Failed to retrieve debates: {e}")
        return []
    finally:
        conn.close()

def get_debate_details(debate_id: str, user_email: str = None) -> Dict[str, Any]:
    """Retrieves full details of a specific debate run including historical turns, matching user_email if provided."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Retrieve debate row
        if user_email:
            cursor.execute("SELECT * FROM debates WHERE id = ? AND user_email = ?", (debate_id, user_email.lower().strip()))
        else:
            cursor.execute("SELECT * FROM debates WHERE id = ?", (debate_id,))
            
        debate_row = cursor.fetchone()
        if not debate_row:
            return {}
            
        debate = dict(debate_row)
        
        # Retrieve turns rows
        cursor.execute("SELECT * FROM turns WHERE debate_id = ? ORDER BY turn_num ASC", (debate_id,))
        turns_rows = cursor.fetchall()
        
        turns = []
        for row in turns_rows:
            turn_dict = dict(row)
            # Re-map database fields to UI keys
            turns.append({
                "turn": turn_dict["turn_num"],
                "speaker": turn_dict["speaker"],
                "speech": turn_dict["speech"],
                "internal_monologue": turn_dict["internal_monologue"],
                "sentiment_after": turn_dict["sentiment_after"],
                "conviction_after": turn_dict["conviction_after"],
                "moderator_note": turn_dict["moderator_note"],
                "is_factually_correct": bool(turn_dict["is_factually_correct"]),
                "cited_source": turn_dict["cited_source"],
                "factuality_score": turn_dict["factuality_score"]
            })
            
        return {
            "id": debate["id"],
            "news_content": debate["news_content"],
            "news_analysis": {
                "sentiment": debate["news_sentiment"],
                "impact": debate["news_impact"],
                "summary": debate["news_content"][:100]
            },
            "company_profile": json.loads(debate["company_profile"]),
            "debate_summary": debate["debate_summary"],
            "valuation": json.loads(debate["valuation_results"]),
            "transcript": turns
        }
    except Exception as e:
        logger.exception(f"Failed to load debate details: {e}")
        return {}
    finally:
        conn.close()

# Auto-initialize database on import
init_db()
