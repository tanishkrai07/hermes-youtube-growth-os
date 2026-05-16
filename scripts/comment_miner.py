#!/usr/bin/env python3
"""
Hermes YouTube Growth OS — Comment Miner
Extracts and analyzes competitor video comments for pain points and sentiment.
"""

import sqlite3
import json
import os
import csv
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(REPO_ROOT, "data", "hermes_intelligence.db")

# YouTube API key from environment or fallback
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_comments(video_id, api_key, max_results=100):
    """Fetch comments for a video using YouTube Data API v3."""
    import urllib.request
    import urllib.parse
    
    url = f"https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": min(max_results, 100),
        "order": "relevance",
        "key": api_key
    }
    
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(full_url, headers={
            "User-Agent": "Hermes-YouTube-Growth-OS/1.0"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return data.get("items", [])
    except Exception as e:
        print(f"  ⚠️ Error fetching comments for {video_id}: {e}")
        return []


def analyze_sentiment(text):
    """Simple rule-based sentiment analysis."""
    text_lower = text.lower()
    
    fear_words = ["scared", "afraid", "worried", "terrified", "panic", "fear", "danger", "warning"]
    trust_words = ["thank", "thanks", "helpful", "great", "excellent", "amazing", "love", "appreciate"]
    question_words = ["what", "how", "why", "when", "where", "?", "should i", "can i", "is it"]
    pain_words = ["pain", "hurt", "suffering", "struggling", "problem", "issue", "symptom"]
    
    scores = {"fear": 0, "trust": 0, "question": 0, "pain": 0}
    
    for word in fear_words:
        if word in text_lower:
            scores["fear"] += 1
    for word in trust_words:
        if word in text_lower:
            scores["trust"] += 1
    for word in question_words:
        if word in text_lower:
            scores["question"] += 1
    for word in pain_words:
        if word in text_lower:
            scores["pain"] += 1
    
    # Determine dominant sentiment
    if scores["fear"] > 0:
        return "fear"
    elif scores["trust"] > 0:
        return "trust"
    elif scores["question"] > 0:
        return "question"
    elif scores["pain"] > 0:
        return "pain"
    else:
        return "neutral"


def extract_pain_point(text):
    """Extract pain point category from comment text."""
    text_lower = text.lower()
    
    pain_categories = {
        "heart": ["heart", "chest", "cardiac", "pulse", "heartbeat"],
        "brain": ["brain", "memory", "forget", "dementia", "alzheimer", "stroke"],
        "legs": ["leg", "feet", "ankle", "knee", "hip", "walk", "swelling", "edema"],
        "sleep": ["sleep", "insomnia", "night", "wake", "tired", "fatigue", "nocturia"],
        "food": ["food", "eat", "diet", "meal", "drink", "vitamin", "supplement"],
        "medication": ["medication", "pill", "drug", "prescription", "side effect", "doctor"],
        "pain": ["pain", "hurt", "ache", "sore", "joint", "arthritis", "inflammation"],
        "blood_pressure": ["blood pressure", "hypertension", "bp", "systolic", "diastolic"],
        "blood_sugar": ["blood sugar", "diabetes", "glucose", "a1c", "insulin"],
        "vision": ["vision", "eye", "see", "blurry", "cataract", "glaucoma"],
        "hearing": ["hearing", "ear", "deaf", "tinnitus"],
        "digestion": ["stomach", "digestion", "gut", "constipation", "acid", "reflux"]
    }
    
    for category, keywords in pain_categories.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category
    
    return "general"


def mine_comments_for_video(video_id, channel_name, api_key, max_comments=50):
    """Mine comments for a single video and store in database."""
    comments = fetch_comments(video_id, api_key, max_comments)
    
    if not comments:
        return 0
    
    conn = get_db()
    c = conn.cursor()
    
    stored = 0
    for item in comments:
        try:
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            text = snippet.get("textDisplay", "")
            likes = snippet.get("likeCount", 0)
            
            sentiment = analyze_sentiment(text)
            pain_point = extract_pain_point(text)
            is_question = 1 if "?" in text or text.lower().startswith(("what", "how", "why", "when", "where", "should", "can")) else 0
            
            c.execute("""
                INSERT INTO comments (video_id, channel_name, comment_text, like_count, sentiment, pain_point, is_question, captured_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                video_id,
                channel_name,
                text[:500],  # Truncate long comments
                likes,
                sentiment,
                pain_point,
                is_question,
                datetime.now().strftime("%Y-%m-%d")
            ))
            stored += 1
        except Exception as e:
            continue
    
    conn.commit()
    conn.close()
    
    return stored


def mine_all_competitor_comments(api_key, max_videos_per_channel=5, max_comments_per_video=50):
    """Mine comments from all competitor channels."""
    conn = get_db()
    c = conn.cursor()
    
    # Get active competitors
    c.execute("SELECT channel_id, channel_name FROM competitors WHERE is_active = 1")
    channels = c.fetchall()
    
    total_comments = 0
    
    for channel in channels:
        channel_id = channel["channel_id"]
        channel_name = channel["channel_name"]
        
        if not channel_id:
            continue
        
        print(f"\n📺 Scanning {channel_name}...")
        
        # Get latest videos for this channel
        import urllib.request
        import urllib.parse
        
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "id",
            "channelId": channel_id,
            "type": "video",
            "order": "date",
            "maxResults": max_videos_per_channel,
            "key": api_key
        }
        
        try:
            full_url = f"{url}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(full_url, headers={"User-Agent": "Hermes-YouTube-Growth-OS/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            
            videos = data.get("items", [])
            
            for video in videos:
                video_id = video["id"]["videoId"]
                count = mine_comments_for_video(video_id, channel_name, api_key, max_comments_per_video)
                total_comments += count
                print(f"  💬 {video_id}: {count} comments")
        
        except Exception as e:
            print(f"  ⚠️ Error scanning {channel_name}: {e}")
    
    conn.close()
    
    print(f"\n✅ Total comments mined: {total_comments}")
    return total_comments


def get_pain_point_summary():
    """Get summary of pain points across all comments."""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
        SELECT pain_point, COUNT(*) as count, 
               SUM(CASE WHEN is_question = 1 THEN 1 ELSE 0 END) as questions
        FROM comments
        GROUP BY pain_point
        ORDER BY count DESC
    """)
    
    results = c.fetchall()
    conn.close()
    
    return results


if __name__ == "__main__":
    import sys
    
    api_key = YOUTUBE_API_KEY or (sys.argv[1] if len(sys.argv) > 1 else "")
    
    if not api_key:
        print("❌ No YouTube API key provided.")
        print("Usage: python3 scripts/comment_miner.py YOUR_API_KEY")
        print("Or set YOUTUBE_API_KEY environment variable.")
        sys.exit(1)
    
    print("🔧 Hermes Comment Miner — Starting...")
    print(f"   API Key: {api_key[:10]}...")
    
    total = mine_all_competitor_comments(api_key)
    
    print("\n📊 Pain Point Summary:")
    for row in get_pain_point_summary():
        print(f"   {row['pain_point']}: {row['count']} comments ({row['questions']} questions)")
