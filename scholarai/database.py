"""
database.py — SQLite session & review tracking for ScholarAI admin dashboard.
All data is anonymous — no PII stored.
"""

import sqlite3
import os
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/scholarai.db")


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist and ensure schema is up to date."""
    with get_conn() as conn:
        # Create tables
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                username          TEXT UNIQUE,
                email             TEXT UNIQUE,
                password_hash     TEXT,
                is_verified       INTEGER DEFAULT 0,
                verification_code TEXT,
                reset_token       TEXT,
                tier              TEXT DEFAULT 'free',
                credits_used      INTEGER DEFAULT 0,
                remember_token    TEXT,
                created_at        TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS sessions (
                session_id   TEXT PRIMARY KEY,
                created_at   TEXT DEFAULT (datetime('now')),
                last_active  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id     TEXT,
                topic          TEXT,
                article_count  INTEGER,
                citation_style TEXT,
                word_count     INTEGER,
                created_at     TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            );

            CREATE TABLE IF NOT EXISTS downloads (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                review_id  INTEGER,
                format     TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (review_id) REFERENCES reviews(id)
            );
        """)
        
        # Migrations: Add columns if they are missing in older DB versions
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "email" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        if "is_verified" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0")
        if "verification_code" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN verification_code TEXT")
        if "reset_token" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
        if "tier" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN tier TEXT DEFAULT 'free'")
        if "credits_used" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN credits_used INTEGER DEFAULT 0")
        if "remember_token" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN remember_token TEXT")

import hashlib

def hash_password(password: str) -> str:
    """Hash password with SHA-256 for basic security."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, email: str, password: str, verification_code: str) -> tuple[bool, str]:
    """Create a new user. Returns (success, message)."""
    with get_conn() as conn:
        try:
            conn.execute("""
                INSERT INTO users (username, email, password_hash, verification_code)
                VALUES (?, ?, ?, ?)
            """, (username, email, hash_password(password), verification_code))
            return True, "Account created successfully."
        except sqlite3.IntegrityError as e:
            if "username" in str(e).lower():
                return False, "Username already exists."
            elif "email" in str(e).lower():
                return False, "Email already exists."
            return False, "An error occurred."

def verify_user(username: str, password: str) -> dict | None:
    """Verify user credentials and return user row if verified."""
    with get_conn() as conn:
        row = conn.execute("""
            SELECT id, username, email, is_verified FROM users 
            WHERE (username = ? OR email = ?) AND password_hash = ?
        """, (username, username, hash_password(password))).fetchone()
        return dict(row) if row else None

def get_user_by_email(email: str) -> dict | None:
    """Retrieve user data by email."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None

def update_user_verification(username: str, is_verified: bool = True) -> None:
    """Update user verification status."""
    with get_conn() as conn:
        conn.execute("UPDATE users SET is_verified = ? WHERE username = ?", (1 if is_verified else 0, username))

def update_reset_token(email: str, token: str | None) -> None:
    """Set or clear a password reset token for a user."""
    with get_conn() as conn:
        conn.execute("UPDATE users SET reset_token = ? WHERE email = ?", (token, email))

def get_user_by_reset_token(token: str) -> dict | None:
    """Find a user by their reset token."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE reset_token = ?", (token,)).fetchone()
        return dict(row) if row else None

def update_password(email: str, new_password: str) -> None:
    """Update a user's password."""
    with get_conn() as conn:
        conn.execute("UPDATE users SET password_hash = ?, reset_token = NULL WHERE email = ?", (hash_password(new_password), email))

def update_remember_token(username: str, token: str | None) -> None:
    """Set or clear a persistent login token."""
    with get_conn() as conn:
        conn.execute("UPDATE users SET remember_token = ? WHERE username = ? OR email = ?", (token, username, username))

def get_user_by_remember_token(token: str) -> dict | None:
    """Retrieve user by their persistent token."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE remember_token = ?", (token,)).fetchone()
        return dict(row) if row else None

# ── Subscription Logic ───────────────────────────────────────────

def get_user_status(username: str) -> dict:
    """Get the subscription tier and credits used for a user."""
    with get_conn() as conn:
        row = conn.execute("SELECT tier, credits_used FROM users WHERE username = ? OR email = ?", (username, username)).fetchone()
        return dict(row) if row else {"tier": "free", "credits_used": 0}

def increment_user_credits(username: str) -> None:
    """Increment the credit count after a successful generation."""
    with get_conn() as conn:
        conn.execute("UPDATE users SET credits_used = credits_used + 1 WHERE username = ? OR email = ?", (username, username))

def update_user_tier(username: str, tier: str) -> None:
    """Upgrade or downgrade a user tier."""
    with get_conn() as conn:
        conn.execute("UPDATE users SET tier = ? WHERE username = ? OR email = ?", (tier, username, username))

def upsert_session(session_id: str) -> None:
    with get_conn() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO sessions (session_id) VALUES (?)
        """, (session_id,))
        conn.execute("""
            UPDATE sessions SET last_active = datetime('now') WHERE session_id = ?
        """, (session_id,))


def log_review(session_id: str, topic: str, article_count: int,
               citation_style: str, word_count: int) -> int:
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO reviews (session_id, topic, article_count, citation_style, word_count)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, topic[:200], article_count, citation_style, word_count))
        return cur.lastrowid


def log_download(review_id: int, fmt: str) -> None:
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO downloads (review_id, format) VALUES (?, ?)
        """, (review_id, fmt))


# ── Admin analytics queries ──────────────────────────────────────

def get_stats() -> dict:
    with get_conn() as conn:
        total_sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        total_reviews  = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        today_reviews  = conn.execute(
            "SELECT COUNT(*) FROM reviews WHERE date(created_at) = date('now')"
        ).fetchone()[0]
        week_reviews   = conn.execute(
            "SELECT COUNT(*) FROM reviews WHERE created_at >= datetime('now', '-7 days')"
        ).fetchone()[0]
        total_downloads= conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
        total_premium  = conn.execute("SELECT COUNT(*) FROM users WHERE tier = 'premium'").fetchone()[0]
        avg_articles   = conn.execute("SELECT AVG(article_count) FROM reviews").fetchone()[0] or 0
        avg_words      = conn.execute("SELECT AVG(word_count) FROM reviews").fetchone()[0] or 0

    return {
        "total_sessions":  total_sessions,
        "total_reviews":   total_reviews,
        "today_reviews":   today_reviews,
        "week_reviews":    week_reviews,
        "total_downloads": total_downloads,
        "total_premium":   total_premium,
        "avg_articles":    round(avg_articles, 1),
        "avg_words":       int(avg_words),
    }


def get_reviews_per_day(days: int = 14) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT date(created_at) as day, COUNT(*) as count
            FROM reviews
            WHERE created_at >= datetime('now', ? || ' days')
            GROUP BY day ORDER BY day
        """, (f"-{days}",)).fetchall()
    return [dict(r) for r in rows]


def get_citation_style_dist() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT citation_style, COUNT(*) as count
            FROM reviews GROUP BY citation_style ORDER BY count DESC
        """).fetchall()
    return [dict(r) for r in rows]


def get_download_format_dist() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT format, COUNT(*) as count
            FROM downloads GROUP BY format ORDER BY count DESC
        """).fetchall()
    return [dict(r) for r in rows]


def get_recent_reviews(limit: int = 20) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT r.id, r.topic, r.article_count, r.citation_style,
                   r.word_count, r.created_at,
                   (SELECT COUNT(*) FROM downloads d WHERE d.review_id = r.id) as downloads
            FROM reviews r ORDER BY r.created_at DESC LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_active_sessions_today() -> int:
    with get_conn() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE date(last_active) = date('now')"
        ).fetchone()[0]
