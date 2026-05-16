#!/usr/bin/env python3
"""
Hermes YouTube Growth OS — Database Builder
Creates SQLite database + ChromaDB vector store for competitor intelligence.
"""

import sqlite3
import json
import os
import csv
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(REPO_ROOT, "data", "hermes_intelligence.db")
CHROMA_PATH = os.path.join(REPO_ROOT, "data", "chroma_db")

def create_sqlite_db():
    """Create the SQLite database with all tables."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Competitors table
    c.execute("""
        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_name TEXT NOT NULL,
            channel_id TEXT UNIQUE,
            channel_url TEXT,
            priority TEXT DEFAULT 'Medium',
            notes TEXT,
            subscriber_count INTEGER,
            total_videos INTEGER,
            total_views INTEGER,
            first_seen DATE DEFAULT CURRENT_DATE,
            last_scanned DATE DEFAULT CURRENT_DATE,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # Videos table
    c.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT UNIQUE NOT NULL,
            channel_id TEXT,
            channel_name TEXT,
            title TEXT,
            description TEXT,
            published_date TEXT,
            view_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            duration_seconds INTEGER,
            pillar TEXT,
            hook_type TEXT,
            title_formula TEXT,
            thumbnail_url TEXT,
            thumbnail_text TEXT,
            thumbnail_layout TEXT,
            view_velocity REAL DEFAULT 0,
            engagement_rate REAL DEFAULT 0,
            captured_date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (channel_id) REFERENCES competitors(channel_id)
        )
    """)
    
    # Title patterns table
    c.execute("""
        CREATE TABLE IF NOT EXISTS title_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id TEXT UNIQUE,
            pattern_name TEXT,
            pattern_formula TEXT,
            example TEXT,
            source_channel TEXT,
            score INTEGER,
            times_seen INTEGER DEFAULT 1,
            first_seen DATE DEFAULT CURRENT_DATE,
            last_seen DATE DEFAULT CURRENT_DATE
        )
    """)
    
    # Trend scores table
    c.execute("""
        CREATE TABLE IF NOT EXISTS trend_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trend_id TEXT UNIQUE,
            trend_name TEXT,
            score INTEGER,
            status TEXT DEFAULT 'ACTIVE',
            competitor_evidence TEXT,
            date_detected DATE DEFAULT CURRENT_DATE,
            notes TEXT
        )
    """)
    
    # Video ideas table
    c.execute("""
        CREATE TABLE IF NOT EXISTS video_ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idea_id TEXT UNIQUE,
            title TEXT,
            pillar TEXT,
            persona TEXT,
            score INTEGER,
            hook_type TEXT,
            emotional_driver TEXT,
            urgency TEXT,
            competitor_evidence TEXT,
            thumbnail_angle TEXT,
            audience_pain_point TEXT,
            retention_mechanism TEXT,
            status TEXT DEFAULT 'PENDING_APPROVAL',
            date_generated DATE DEFAULT CURRENT_DATE,
            date_approved DATE,
            date_produced DATE
        )
    """)
    
    # Comments table
    c.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            channel_name TEXT,
            comment_text TEXT,
            like_count INTEGER DEFAULT 0,
            sentiment TEXT,
            pain_point TEXT,
            is_question INTEGER DEFAULT 0,
            captured_date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (video_id) REFERENCES videos(video_id)
        )
    """)
    
    # Transcripts table
    c.execute("""
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            channel_name TEXT,
            full_text TEXT,
            hook_text TEXT,
            cta_text TEXT,
            word_count INTEGER,
            language TEXT DEFAULT 'en',
            captured_date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (video_id) REFERENCES videos(video_id)
        )
    """)
    
    # Daily scan log
    c.execute("""
        CREATE TABLE IF NOT EXISTS scan_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_date DATE DEFAULT CURRENT_DATE,
            channels_scanned INTEGER DEFAULT 0,
            videos_found INTEGER DEFAULT 0,
            new_ideas_generated INTEGER DEFAULT 0,
            trends_detected INTEGER DEFAULT 0,
            report_path TEXT,
            status TEXT DEFAULT 'COMPLETED'
        )
    """)
    
    # Create indexes for fast queries
    c.execute("CREATE INDEX IF NOT EXISTS idx_videos_channel ON videos(channel_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_videos_pillar ON videos(pillar)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_videos_velocity ON videos(view_velocity DESC)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ideas_score ON video_ideas(score DESC)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_trends_score ON trend_scores(score DESC)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_comments_pain ON comments(pain_point)")
    
    conn.commit()
    conn.close()
    print(f"✅ SQLite database created at {DB_PATH}")


def create_chroma_db():
    """Create ChromaDB vector store for semantic search."""
    import chromadb
    from chromadb.config import Settings
    
    os.makedirs(CHROMA_PATH, exist_ok=True)
    
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    # Collection for transcript hooks
    try:
        client.delete_collection("transcript_hooks")
    except:
        pass
    hooks_collection = client.create_collection(
        name="transcript_hooks",
        metadata={"description": "Video transcript hooks and opening patterns"}
    )
    
    # Collection for title patterns
    try:
        client.delete_collection("title_patterns")
    except:
        pass
    titles_collection = client.create_collection(
        name="title_patterns",
        metadata={"description": "Title formulas and patterns"}
    )
    
    # Collection for pain points
    try:
        client.delete_collection("pain_points")
    except:
        pass
    pain_collection = client.create_collection(
        name="pain_points",
        metadata={"description": "Audience pain points and emotional triggers"}
    )
    
    # Collection for video ideas
    try:
        client.delete_collection("video_ideas")
    except:
        pass
    ideas_collection = client.create_collection(
        name="video_ideas",
        metadata={"description": "Dr. Victor Kane video ideas"}
    )
    
    print(f"✅ ChromaDB created at {CHROMA_PATH}")
    print(f"   Collections: transcript_hooks, title_patterns, pain_points, video_ideas")


def seed_from_csv():
    """Seed the database from existing CSV files."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Seed competitors from watchlist
    watchlist_path = os.path.join(REPO_ROOT, "memory", "competitor_watchlist.csv")
    if os.path.exists(watchlist_path):
        with open(watchlist_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    c.execute("""
                        INSERT OR IGNORE INTO competitors 
                        (channel_name, channel_url, priority, notes, last_scanned)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        row.get("channel_name", ""),
                        row.get("channel_url", ""),
                        row.get("priority", "Medium"),
                        row.get("notes", ""),
                        datetime.now().strftime("%Y-%m-%d")
                    ))
                except Exception as e:
                    print(f"  Warning: Could not seed competitor {row.get('channel_name')}: {e}")
    
    # Seed title patterns
    patterns_path = os.path.join(REPO_ROOT, "memory", "title_patterns.csv")
    if os.path.exists(patterns_path):
        with open(patterns_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    c.execute("""
                        INSERT OR IGNORE INTO title_patterns
                        (pattern_id, pattern_name, pattern_formula, example, source_channel, score, first_seen)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get("pattern_id", ""),
                        row.get("pattern_name", ""),
                        row.get("pattern_formula", ""),
                        row.get("example", ""),
                        row.get("source_channel", ""),
                        int(row.get("score", 0)),
                        row.get("date_discovered", datetime.now().strftime("%Y-%m-%d"))
                    ))
                except Exception as e:
                    print(f"  Warning: Could not seed pattern {row.get('pattern_id')}: {e}")
    
    # Seed trend scores
    trends_path = os.path.join(REPO_ROOT, "memory", "trend_scores.csv")
    if os.path.exists(trends_path):
        with open(trends_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    c.execute("""
                        INSERT OR IGNORE INTO trend_scores
                        (trend_id, trend_name, score, status, competitor_evidence, date_detected, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get("trend_id", ""),
                        row.get("trend_name", ""),
                        int(row.get("score", 0)),
                        row.get("status", "ACTIVE"),
                        row.get("competitor_evidence", ""),
                        row.get("date_detected", datetime.now().strftime("%Y-%m-%d")),
                        row.get("notes", "")
                    ))
                except Exception as e:
                    print(f"  Warning: Could not seed trend {row.get('trend_id')}: {e}")
    
    # Seed video ideas
    ideas_path = os.path.join(REPO_ROOT, "memory", "video_idea_bank.csv")
    if os.path.exists(ideas_path):
        with open(ideas_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    c.execute("""
                        INSERT OR IGNORE INTO video_ideas
                        (idea_id, title, pillar, persona, score, hook_type, emotional_driver,
                         urgency, competitor_evidence, thumbnail_angle, audience_pain_point,
                         retention_mechanism, status, date_generated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get("idea_id", ""),
                        row.get("title", ""),
                        row.get("pillar", ""),
                        row.get("persona", ""),
                        int(row.get("score", 0)),
                        row.get("hook_type", ""),
                        row.get("emotional_driver", ""),
                        row.get("urgency", ""),
                        row.get("competitor_evidence", ""),
                        row.get("thumbnail_angle", ""),
                        row.get("audience_pain_point", ""),
                        row.get("retention_mechanism", ""),
                        row.get("status", "PENDING_APPROVAL"),
                        row.get("date_generated", datetime.now().strftime("%Y-%m-%d"))
                    ))
                except Exception as e:
                    print(f"  Warning: Could not seed idea {row.get('idea_id')}: {e}")
    
    conn.commit()
    
    # Print summary
    for table in ["competitors", "title_patterns", "trend_scores", "video_ideas"]:
        c.execute(f"SELECT COUNT(*) FROM {table}")
        count = c.fetchone()[0]
        print(f"  📊 {table}: {count} rows")
    
    conn.close()


def main():
    print("🔧 Building Hermes Intelligence Database...")
    print()
    
    create_sqlite_db()
    print()
    
    create_chroma_db()
    print()
    
    print("🌱 Seeding database from CSV files...")
    seed_from_csv()
    print()
    
    print("✅ Database infrastructure ready!")
    print(f"   SQLite: {DB_PATH}")
    print(f"   ChromaDB: {CHROMA_PATH}")


if __name__ == "__main__":
    main()
