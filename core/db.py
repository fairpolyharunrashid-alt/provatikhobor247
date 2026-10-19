"""
SQLite database layer for Bangladesh News Portal.
Tracks scraped stories, published articles, and category distribution.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import DATA_DIR

DB_PATH = DATA_DIR / "news_portal.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scraped_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                source_url TEXT,
                source_name TEXT,
                summary TEXT,
                published_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS published_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blogger_post_id TEXT UNIQUE,
                title TEXT,
                category TEXT,
                url TEXT,
                source_title TEXT,
                published_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def is_news_scraped(title: str) -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT 1 FROM scraped_news WHERE title = ?", (title.strip(),)).fetchone()
        return row is not None


def record_scraped_news(title: str, source_url: str, source_name: str, summary: str = "", published_at: str = ""):
    with get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO scraped_news (title, source_url, source_name, summary, published_at)
            VALUES (?, ?, ?, ?, ?)
        """, (title.strip(), source_url, source_name, summary, published_at))
        conn.commit()


def record_published_article(blogger_post_id: str, title: str, category: str, url: str, source_title: str):
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO published_articles (blogger_post_id, title, category, url, source_title)
            VALUES (?, ?, ?, ?, ?)
        """, (blogger_post_id, title, category, url, source_title))
        conn.commit()


def get_recent_published_titles(limit: int = 50) -> List[str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT title FROM published_articles ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [r["title"] for r in rows]
