#!/usr/bin/env python3
"""
Hermes YouTube Growth OS — Daily Automation Orchestrator
Runs the complete daily cycle: scan → analyze → score → report.
"""

import sqlite3
import json
import os
import csv
import subprocess
import sys
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(REPO_ROOT, "data", "hermes_intelligence.db")
REPORTS_DIR = os.path.join(REPO_ROOT, "outputs", "reports")
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def log_scan(channels_scanned, videos_found, new_ideas, trends_detected, report_path, status="COMPLETED"):
    """Log a scan to the database."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO scan_log (scan_date, channels_scanned, videos_found, new_ideas_generated, trends_detected, report_path, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d"),
        channels_scanned,
        videos_found,
        new_ideas,
        trends_detected,
        report_path,
        status
    ))
    conn.commit()
    conn.close()


def run_morning_scan():
    """Step 1: Morning — Scan competitors for new uploads."""
    print("\n" + "="*60)
    print("🌅 MORNING: Competitor Scan")
    print("="*60)
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT channel_id, channel_name, priority FROM competitors WHERE is_active = 1 ORDER BY priority")
    channels = c.fetchall()
    
    total_videos = 0
    new_videos = 0
    
    import urllib.request
    import urllib.parse
    
    for channel in channels:
        channel_id = channel["channel_id"]
        channel_name = channel["channel_name"]
        priority = channel["priority"]
        
        if not channel_id:
            continue
        
        print(f"\n  📺 {channel_name} ({priority})")
        
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "channelId": channel_id,
            "type": "video",
            "order": "date",
            "maxResults": 10,
            "key": YOUTUBE_API_KEY
        }
        
        try:
            full_url = f"{url}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(full_url, headers={"User-Agent": "Hermes-YouTube-Growth-OS/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            
            for item in data.get("items", []):
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                
                # Check if we already have this video
                c.execute("SELECT id FROM videos WHERE video_id = ?", (video_id,))
                if c.fetchone():
                    continue
                
                # Get video statistics
                stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics,contentDetails&id={video_id}&key={YOUTUBE_API_KEY}"
                try:
                    stats_req = urllib.request.Request(stats_url, headers={"User-Agent": "Hermes-YouTube-Growth-OS/1.0"})
                    with urllib.request.urlopen(stats_req, timeout=15) as stats_resp:
                        stats_data = json.loads(stats_resp.read().decode())
                    
                    if stats_data.get("items"):
                        stats = stats_data["items"][0]["statistics"]
                        details = stats_data["items"][0]["contentDetails"]
                        
                        views = int(stats.get("viewCount", 0))
                        likes = int(stats.get("likeCount", 0))
                        comments = int(stats.get("commentCount", 0))
                        duration = details.get("duration", "PT0S")
                        
                        # Parse duration to seconds
                        import re
                        duration_match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
                        duration_seconds = 0
                        if duration_match:
                            h, m, s = duration_match.groups()
                            duration_seconds = (int(h or 0) * 3600) + (int(m or 0) * 60) + (int(s or 0))
                        
                        # Calculate view velocity (views per day)
                        from datetime import datetime as dt
                        published = snippet.get("publishedAt", "")
                        if published:
                            try:
                                pub_date = dt.fromisoformat(published.replace("Z", "+00:00"))
                                days_since = max(1, (dt.now() - pub_date.replace(tzinfo=None)).days)
                                velocity = views / days_since
                            except:
                                velocity = 0
                        else:
                            velocity = 0
                        
                        # Engagement rate
                        engagement = ((likes + comments) / max(views, 1)) * 100
                        
                        c.execute("""
                            INSERT INTO videos (video_id, channel_id, channel_name, title, description, published_date,
                                              view_count, like_count, comment_count, duration_seconds, thumbnail_url,
                                              view_velocity, engagement_rate, captured_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            video_id,
                            channel_id,
                            channel_name,
                            snippet.get("title", ""),
                            snippet.get("description", "")[:500],
                            published,
                            views,
                            likes,
                            comments,
                            duration_seconds,
                            snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                            velocity,
                            engagement,
                            datetime.now().strftime("%Y-%m-%d")
                        ))
                        new_videos += 1
                except Exception as e:
                    print(f"    ⚠️ Stats error for {video_id}: {e}")
                
                total_videos += 1
            
            conn.commit()
            print(f"    ✅ {len(data.get('items', []))} videos scanned, {new_videos} new")
        
        except Exception as e:
            print(f"    ⚠️ Error: {e}")
    
    conn.close()
    
    print(f"\n📊 Morning scan complete: {total_videos} videos scanned, {new_videos} new")
    return total_videos, new_videos


def run_afternoon_analysis():
    """Step 2: Afternoon — Analyze patterns, score trends, detect hooks."""
    print("\n" + "="*60)
    print("☀️ AFTERNOON: Pattern Analysis & Trend Scoring")
    print("="*60)
    
    conn = get_db()
    c = conn.cursor()
    
    # Get all videos from last 7 days
    c.execute("""
        SELECT * FROM videos 
        WHERE captured_date >= date('now', '-7 days')
        ORDER BY view_velocity DESC
    """)
    recent_videos = c.fetchall()
    
    print(f"\n  📊 Analyzing {len(recent_videos)} recent videos...")
    
    # Detect trending topics
    topic_counts = {}
    hook_types = {}
    title_formulas = {}
    
    for video in recent_videos:
        title = video["title"]
        
        # Detect topics
        topics = {
            "hantavirus": ["hantavirus", "virus", "outbreak"],
            "blood_sugar": ["blood sugar", "diabetes", "glucose", "a1c"],
            "stroke": ["stroke", "brain attack"],
            "heart": ["heart", "cardiac", "chest"],
            "legs": ["leg", "feet", "ankle", "swollen", "circulation"],
            "food": ["food", "eat", "diet", "drink", "reheat"],
            "medication": ["medication", "pill", "drug", "prescription"],
            "sleep": ["sleep", "night", "insomnia", "nocturia"],
            "nails": ["nail", "fingernail"],
            "longevity": ["live", "years", "longevity", "longer"],
            "blood_pressure": ["blood pressure", "hypertension"],
            "pain": ["pain", "ache", "joint", "arthritis"]
        }
        
        title_lower = title.lower()
        for topic, keywords in topics.items():
            for kw in keywords:
                if kw in title_lower:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
                    break
        
        # Detect hook types
        if "warn" in title_lower or "warning" in title_lower:
            hook_types["warning"] = hook_types.get("warning", 0) + 1
        if "never" in title_lower or "stop" in title_lower:
            hook_types["forbidden"] = hook_types.get("forbidden", 0) + 1
        if "?" in title:
            hook_types["question"] = hook_types.get("question", 0) + 1
        if any(x in title_lower for x in ["how to", "fix", "cure", "reverse"]):
            hook_types["solution"] = hook_types.get("solution", 0) + 1
        if any(x in title_lower for x in ["after 60", "after 65", "over 60", "over 65", "senior"]):
            hook_types["age_target"] = hook_types.get("age_target", 0) + 1
    
    # Score trends
    trends_detected = 0
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
        score = min(20, count * 3 + 10)  # Simple scoring formula
        
        if score >= 15:
            trend_id = f"T{datetime.now().strftime('%Y%m%d')}_{topic.upper()}"
            
            # Check if trend already exists
            c.execute("SELECT id FROM trend_scores WHERE trend_id = ?", (trend_id,))
            if not c.fetchone():
                c.execute("""
                    INSERT INTO trend_scores (trend_id, trend_name, score, status, competitor_evidence, date_detected, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    trend_id,
                    topic.replace("_", " ").title(),
                    score,
                    "ACTIVE",
                    f"Detected in {count} videos in last 7 days",
                    datetime.now().strftime("%Y-%m-%d"),
                    f"Auto-detected from {count} competitor videos"
                ))
                trends_detected += 1
                print(f"  📈 New trend: {topic.replace('_', ' ').title()} (Score: {score})")
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Analysis complete: {trends_detected} new trends detected")
    print(f"  Top hook types: {dict(sorted(hook_types.items(), key=lambda x: x[1], reverse=True)[:5])}")
    
    return trends_detected


def run_evening_report():
    """Step 3: Evening — Compress intelligence, update memory, generate report."""
    print("\n" + "="*60)
    print("🌙 EVENING: Intelligence Compression & Report Generation")
    print("="*60)
    
    conn = get_db()
    c = conn.cursor()
    
    # Get top ideas
    c.execute("SELECT * FROM video_ideas WHERE status = 'PENDING_APPROVAL' ORDER BY score DESC LIMIT 10")
    top_ideas = c.fetchall()
    
    # Get top trends
    c.execute("SELECT * FROM trend_scores WHERE status = 'ACTIVE' ORDER BY score DESC LIMIT 8")
    top_trends = c.fetchall()
    
    # Get scan stats
    c.execute("SELECT COUNT(*) as total FROM videos")
    total_videos = c.fetchone()["total"]
    
    c.execute("SELECT COUNT(*) as total FROM competitors WHERE is_active = 1")
    total_competitors = c.fetchone()["total"]
    
    # Generate report
    report_date = datetime.now().strftime("%Y-%m-%d")
    report_path = os.path.join(REPORTS_DIR, f"{report_date}_daily_report.md")
    
    with open(report_path, "w") as f:
        f.write(f"# Hermes Daily Report — {report_date}\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 📊 System Status\n\n")
        f.write(f"- Competitors tracked: {total_competitors}\n")
        f.write(f"- Videos in database: {total_videos}\n")
        f.write(f"- Active trends: {len(top_trends)}\n")
        f.write(f"- Pending ideas: {len(top_ideas)}\n\n")
        
        f.write("## 🔥 Top Trends\n\n")
        f.write("| Trend | Score | Status |\n")
        f.write("|-------|-------|--------|\n")
        for trend in top_trends:
            f.write(f"| {trend['trend_name']} | {trend['score']}/20 | {trend['status']} |\n")
        
        f.write("\n## 💡 Top Video Ideas\n\n")
        for i, idea in enumerate(top_ideas[:5], 1):
            f.write(f"### {i}. {idea['title']}\n")
            f.write(f"- **Score**: {idea['score']}/20\n")
            f.write(f"- **Pillar**: {idea['pillar']}\n")
            f.write(f"- **Hook**: {idea['hook_type']}\n")
            f.write(f"- **Urgency**: {idea['urgency']}\n")
            f.write(f"- **Status**: {idea['status']}\n\n")
        
        f.write("## 📋 Next Actions\n\n")
        f.write("1. Review and approve top video ideas\n")
        f.write("2. Produce full production package for approved ideas\n")
        f.write("3. Update context pack with latest intelligence\n\n")
    
    conn.close()
    
    print(f"\n📄 Report generated: {report_path}")
    return report_path


def main():
    """Run the complete daily automation cycle."""
    print("🚀 Hermes YouTube Growth OS — Daily Automation")
    print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not YOUTUBE_API_KEY:
        print("❌ YOUTUBE_API_KEY not set. Set it in .env or environment.")
        sys.exit(1)
    
    # Morning scan
    total_videos, new_videos = run_morning_scan()
    
    # Afternoon analysis
    trends_detected = run_afternoon_analysis()
    
    # Evening report
    report_path = run_evening_report()
    
    # Log scan
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM video_ideas WHERE status = 'PENDING_APPROVAL'")
    pending_ideas = c.fetchone()["total"]
    conn.close()
    
    log_scan(
        channels_scanned=12,
        videos_found=new_videos,
        new_ideas=pending_ideas,
        trends_detected=trends_detected,
        report_path=report_path
    )
    
    print("\n" + "="*60)
    print("✅ Daily automation cycle complete!")
    print(f"   Videos scanned: {total_videos} ({new_videos} new)")
    print(f"   Trends detected: {trends_detected}")
    print(f"   Pending ideas: {pending_ideas}")
    print(f"   Report: {report_path}")
    print("="*60)


if __name__ == "__main__":
    main()
