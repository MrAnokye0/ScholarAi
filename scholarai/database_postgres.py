"""
database_postgres.py — PostgreSQL adapter for persistent storage on Streamlit Cloud
Automatically uses PostgreSQL if DATABASE_URL is set, otherwise falls back to SQLite
"""

import os
import hashlib
from datetime import datetime
from pathlib import Path

# Check if we should use PostgreSQL or SQLite
DATABASE_URL = os.getenv("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    print("✅ Using PostgreSQL (persistent storage)")
else:
    import sqlite3
    print("⚠️  Using SQLite (temporary storage - data will be lost on reboot)")
    DB_PATH = Path("data/scholarai.db")


def get_conn():
    """Get database connection - PostgreSQL or SQLite"""
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    else:
        DB_PATH.parent.mkdir(exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn


def init_db():
    """Create tables if they don't exist"""
    with get_conn() as conn:
        cursor = conn.cursor()
        
        if USE_POSTGRES:
            # PostgreSQL schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    is_verified INTEGER DEFAULT 0,
                    verification_code TEXT,
                    verification_code_sent_at DOUBLE PRECISION DEFAULT 0,
                    reset_token TEXT,
                    reset_token_sent_at DOUBLE PRECISION DEFAULT 0,
                    tier TEXT DEFAULT 'free',
                    credits_used INTEGER DEFAULT 0,
                    remember_token TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT,
                    topic TEXT,
                    article_count INTEGER,
                    citation_style TEXT,
                    word_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id SERIAL PRIMARY KEY,
                    review_id INTEGER,
                    format TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            # SQLite schema (original)
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    is_verified INTEGER DEFAULT 0,
                    verification_code TEXT,
                    verification_code_sent_at REAL DEFAULT 0,
                    reset_token TEXT,
                    reset_token_sent_at REAL DEFAULT 0,
                    tier TEXT DEFAULT 'free',
                    credits_used INTEGER DEFAULT 0,
                    remember_token TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT DEFAULT (datetime('now')),
                    last_active TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    topic TEXT,
                    article_count INTEGER,
                    citation_style TEXT,
                    word_count INTEGER,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    review_id INTEGER,
                    format TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );
            """)
        
        conn.commit()

        # ── Migrations: add new columns to existing databases ──────────────
        if not USE_POSTGRES:
            cursor.execute("PRAGMA table_info(users)")
            existing = {row[1] for row in cursor.fetchall()}
            migrations = {
                "verification_code_sent_at": "ALTER TABLE users ADD COLUMN verification_code_sent_at REAL DEFAULT 0",
                "reset_token_sent_at":       "ALTER TABLE users ADD COLUMN reset_token_sent_at REAL DEFAULT 0",
            }
            for col, sql in migrations.items():
                if col not in existing:
                    cursor.execute(sql)
            conn.commit()
        else:
            # PostgreSQL: add columns if missing (idempotent)
            for col, col_type in [
                ("verification_code_sent_at", "DOUBLE PRECISION DEFAULT 0"),
                ("reset_token_sent_at",       "DOUBLE PRECISION DEFAULT 0"),
            ]:
                try:
                    cursor.execute(
                        f"ALTER TABLE users ADD COLUMN {col} {col_type}"
                    )
                    conn.commit()
                except Exception:
                    conn.rollback()  # column already exists — ignore


def hash_password(password: str) -> str:
    """Hash password with SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password_hash(password: str, stored_hash: str) -> bool:
    """Verify password matches stored hash"""
    return hash_password(password) == stored_hash


def create_user(username: str, email: str, password: str, verification_code: str) -> tuple[bool, str]:
    """Create a new user"""
    import time as _time
    now = _time.time()
    with get_conn() as conn:
        cursor = conn.cursor()
        try:
            if USE_POSTGRES:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, verification_code, verification_code_sent_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (username, email, hash_password(password), verification_code, now))
            else:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, verification_code, verification_code_sent_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, email, hash_password(password), verification_code, now))
            conn.commit()
            return True, "Account created successfully."
        except Exception as e:
            error_msg = str(e).lower()
            if "username" in error_msg or "unique" in error_msg:
                return False, "Username already exists."
            elif "email" in error_msg:
                return False, "Email already exists."
            return False, "An error occurred."


def verify_user(username: str, password: str) -> dict | None:
    """Verify user credentials"""
    with get_conn() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute("""
                SELECT id, username, email, is_verified, tier, credits_used
                FROM users 
                WHERE (username = %s OR email = %s) AND password_hash = %s
            """, (username, username, hash_password(password)))
        else:
            cursor.execute("""
                SELECT id, username, email, is_verified, tier, credits_used
                FROM users 
                WHERE (username = ? OR email = ?) AND password_hash = ?
            """, (username, username, hash_password(password)))
        
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str) -> dict | None:
    """Get user by email"""
    with get_conn() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        else:
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        
        row = cursor.fetchone()
        return dict(row) if row else None


def update_user_verification(username: str, is_verified: bool = True):
    """Update user verification status"""
    with get_conn() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute("UPDATE users SET is_verified = %s WHERE username = %s", 
                         (1 if is_verified else 0, username))
        else:
            cursor.execute("UPDATE users SET is_verified = ? WHERE username = ?", 
                         (1 if is_verified else 0, username))
        conn.commit()


def update_verification_code(email: str, code: str):
    """Update verification code and record the time it was issued."""
    import time as _time
    now = _time.time()
    with get_conn() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute(
                "UPDATE users SET verification_code = %s, verification_code_sent_at = %s WHERE email = %s",
                (code, now, email),
            )
        else:
            cursor.execute(
                "UPDATE users SET verification_code = ?, verification_code_sent_at = ? WHERE email = ?",
                (code, now, email),
            )
        conn.commit()


def update_reset_token(email: str, token: str | None):
    """Update password reset token and record the time it was issued."""
    import time as _time
    now = _time.time() if token else 0
    with get_conn() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute(
                "UPDATE users SET reset_token = %s, reset_token_sent_at = %s WHERE email = %s",
                (token, now, email),
            )
        else:
            cursor.execute(
                "UPDATE users SET reset_token = ?, reset_token_sent_at = ? WHERE email = ?",
                (token, now, email),
            )
        conn.commit()


def update_password(email: str, new_password: str):
    """Update user password"""
    with get_conn() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute("UPDATE users SET password_hash = %s, reset_token = NULL WHERE email = %s", 
                         (hash_password(new_password), email))
        else:
            cursor.execute("UPDATE users SET password_hash = ?, reset_token = NULL WHERE email = ?", 
                         (hash_password(new_password), email))
        conn.commit()


def update_remember_token(username: str, token: str | None):
    """Update remember me token"""
    with get_conn() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute("UPDATE users SET remember_token = %s WHERE username = %s OR email = %s", 
                         (token, username, username))
        else:
            cursor.execute("UPDATE users SET remember_token = ? WHERE username = ? OR email = ?", 
                         (token, username, username))
        conn.commit()


def get_user_by_remember_token(token: str) -> dict | None:
    """Get user by remember token"""
    with get_conn() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute("SELECT * FROM users WHERE remember_token = %s", (token,))
        else:
            cursor.execute("SELECT * FROM users WHERE remember_token = ?", (token,))
        
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_status(username: str) -> dict:
    """Get user tier and credits"""
    with get_conn() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute("SELECT tier, credits_used FROM users WHERE username = %s OR email = %s", 
                         (username, username))
        else:
            cursor.execute("SELECT tier, credits_used FROM users WHERE username = ? OR email = ?", 
                         (username, username))
        
        row = cursor.fetchone()
        return dict(row) if row else {"tier": "free", "credits_used": 0}


def increment_user_credits(username: str):
    """Increment user credits"""
    with get_conn() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute("UPDATE users SET credits_used = credits_used + 1 WHERE username = %s OR email = %s", 
                         (username, username))
        else:
            cursor.execute("UPDATE users SET credits_used = credits_used + 1 WHERE username = ? OR email = ?", 
                         (username, username))
        conn.commit()


def update_user_tier(username: str, tier: str):
    """Update user tier"""
    with get_conn() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute("UPDATE users SET tier = %s WHERE username = %s OR email = %s", 
                         (tier, username, username))
        else:
            cursor.execute("UPDATE users SET tier = ? WHERE username = ? OR email = ?", 
                         (tier, username, username))
        conn.commit()


def upsert_session(session_id: str):
    """Create or update session"""
    with get_conn() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO sessions (session_id) VALUES (%s)
                ON CONFLICT (session_id) DO UPDATE SET last_active = CURRENT_TIMESTAMP
            """, (session_id,))
        else:
            cursor.execute("INSERT OR IGNORE INTO sessions (session_id) VALUES (?)", (session_id,))
            cursor.execute("UPDATE sessions SET last_active = datetime('now') WHERE session_id = ?", (session_id,))
        conn.commit()


def log_review(session_id: str, topic: str, article_count: int, citation_style: str, word_count: int) -> int:
    """Log a review"""
    with get_conn() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO reviews (session_id, topic, article_count, citation_style, word_count)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, (session_id, topic[:200], article_count, citation_style, word_count))
            return cursor.fetchone()['id']
        else:
            cursor.execute("""
                INSERT INTO reviews (session_id, topic, article_count, citation_style, word_count)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, topic[:200], article_count, citation_style, word_count))
            conn.commit()
            return cursor.lastrowid


def log_download(review_id: int, fmt: str):
    """Log a download"""
    with get_conn() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute("INSERT INTO downloads (review_id, format) VALUES (%s, %s)", (review_id, fmt))
        else:
            cursor.execute("INSERT INTO downloads (review_id, format) VALUES (?, ?)", (review_id, fmt))
        conn.commit()


# Admin functions
def force_verify_user(email_or_username: str) -> bool:
    """Force verify a user"""
    with get_conn() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute("UPDATE users SET is_verified = 1 WHERE username = %s OR email = %s", 
                         (email_or_username, email_or_username))
        else:
            cursor.execute("UPDATE users SET is_verified = 1 WHERE username = ? OR email = ?", 
                         (email_or_username, email_or_username))
        conn.commit()
        return cursor.rowcount > 0


def get_user_verification_code(email: str) -> str | None:
    """Get verification code"""
    with get_conn() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute("SELECT verification_code FROM users WHERE email = %s", (email,))
        else:
            cursor.execute("SELECT verification_code FROM users WHERE email = ?", (email,))
        
        row = cursor.fetchone()
        return row['verification_code'] if row else None
