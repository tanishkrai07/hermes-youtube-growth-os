#!/usr/bin/env python3
"""
Hermes YouTube Growth OS — Competitor Video Fetcher
Fetches recent videos from competitor channels using YouTube Data API v3.

Usage:
    python3 scripts/fetch_competitor_videos.py [--days-back 7] [--channel CHANNEL_NAME] [--dry-run]

Output:
    data/competitors/daily/YYYY-MM-DD_competitors.csv
"""

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WATCHLIST_PATH = REPO_ROOT / "memory" / "competitor_watchlist.csv"
OUTPUT_DIR = REPO_ROOT / "data" / "competitors" / "daily"
SCHEMA_PATH = REPO_ROOT / "schemas" / "competitor_daily_snapshot.schema.json"
QUOTA_LOG_PATH = REPO_ROOT / "data" / "youtube_api_quota_log.json"

# YouTube API quota costs
QUOTA_SEARCH = 100
QUOTA_VIDEOS_LIST = 1
QUOTA_PER_CHANNEL = QUOTA_SEARCH + 20 * QUOTA_VIDEOS_LIST  # ~120 units per channel

CSV_HEADERS = [
    "date_found", "channel", "video_title", "url", "published_date",
    "views", "duration", "pillar", "hook_type", "title_formula",
    "thumbnail_text", "thumbnail_layout", "thumbnail_colors",
    "comment_themes", "idea_signal"
]


def log(level, message):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{level}] {ts} {message}", flush=True)


def get_api_keys():
    """Get YouTube API key(s) from environment. Supports comma-separated list."""
    raw = os.environ.get("YOUTUBE_API_KEY", "")
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    if not keys:
        log("ERROR", "YOUTUBE_API_KEY not set. Set it in ~/.hermes/.env or environment.")
        sys.exit(2)
    return keys


def load_watchlist():
    """Load competitor watchlist CSV."""
    if not WATCHLIST_PATH.exists():
        log("ERROR", f"Watchlist not found: {WATCHLIST_PATH}")
        sys.exit(2)
    channels = []
    with open(WATCHLIST_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("channel_url"):
                channels.append(row)
    log("INFO", f"Loaded {len(channels)} channels from watchlist")
    return channels


def extract_channel_id(channel_url, api_key):
    """Extract channel ID from various YouTube URL formats."""
    # Try to extract from URL patterns
    url = channel_url.strip()

    # Pattern: youtube.com/channel/UC...
    if "/channel/" in url:
        return url.split("/channel/")[1].split("/")[0].split("?")[0]

    # Pattern: youtube.com/@handle or youtube.com/c/name or youtube.com/user/name
    # Need to resolve via API
    handle = None
    if "/@" in url:
        handle = url.split("/@")[1].split("/")[0].split("?")[0]
    elif "/c/" in url:
        handle = url.split("/c/")[1].split("/")[0].split("?")[0]
    elif "/user/" in url:
        handle = url.split("/user/")[1].split("/")[0].split("?")[0]

    if handle:
        # Try handle resolution via forUsername first, then search
        try:
            search_url = "https://www.googleapis.com/youtube/v3/channels"
            params = {"part": "id", "forUsername": handle, "key": api_key}
            full_url = f"{search_url}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(full_url, headers={"User-Agent": "Hermes-YouTube-Growth-OS/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                items = data.get("items", [])
                if items:
                    return items[0]["id"]
        except Exception:
            pass

        # Try search API
        try:
            search_url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet", "q": handle, "type": "channel",
                "maxResults": 1, "key": api_key
            }
            full_url = f"{search_url}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(full_url, headers={"User-Agent": "Hermes-YouTube-Growth-OS/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                items = data.get("items", [])
                if items:
                    return items[0]["snippet"]["channelId"]
        except Exception:
            pass

    log("WARN", f"Could not extract channel ID from: {channel_url}")
    return None


def api_request(url, max_retries=5, base_delay=2):
    """Make API request with exponential backoff and key rotation."""
    keys = get_api_keys()
    key_index = 0

    for attempt in range(max_retries):
        key = keys[key_index % len(keys)]
        # Replace key in URL
        url_with_key = url
        if "key=" in url:
            # Replace existing key
            parts = url.split("key=")
            rest = parts[1].split("&", 1)
            url_with_key = parts[0] + "key=" + key + ("&" + rest[1] if len(rest) > 1 else "")

        try:
            req = urllib.request.Request(url_with_key, headers={
                "User-Agent": "Hermes-YouTube-Growth-OS/1.0"
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 403:
                # Quota exhausted or forbidden — try next key
                body = e.read().decode() if e.fp else ""
                if "quotaExceeded" in body or "rateLimitExceeded" in body:
                    log("WARN", f"Quota exhausted for key {key_index + 1}/{len(keys)}, trying next key...")
                    key_index += 1
                    if key_index >= len(keys):
                        log("ERROR", "All API keys exhausted")
                        return None
                    time.sleep(1)
                    continue
            log("WARN", f"HTTP {e.code} on attempt {attempt + 1}: {e.reason}")
        except Exception as e:
            log("WARN", f"Request failed (attempt {attempt + 1}): {e}")

        delay = min(base_delay * (2 ** attempt), 60)
        time.sleep(delay)

    return None


def fetch_channel_videos(channel_id, published_after, api_key):
    """Fetch videos for a channel published after a given date."""
    videos = []

    # Step 1: Search for recent videos
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "id,snippet",
        "channelId": channel_id,
        "publishedAfter": published_after,
        "type": "video",
        "order": "date",
        "maxResults": 50,
        "key": api_key
    }

    full_url = f"{search_url}?{urllib.parse.urlencode(params)}"
    data = api_request(full_url)

    if not data:
        return videos

    video_ids = []
    id_to_snippet = {}
    for item in data.get("items", []):
        vid = item["id"].get("videoId")
        if vid:
            video_ids.append(vid)
            id_to_snippet[vid] = item.get("snippet", {})

    if not video_ids:
        return videos

    # Step 2: Get full metadata in batches of 50
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        ids_str = ",".join(batch)
        videos_url = "https://www.googleapis.com/youtube/v3/videos"
        vparams = {
            "part": "snippet,statistics,contentDetails",
            "id": ids_str,
            "key": api_key
        }
        vfull_url = f"{videos_url}?{urllib.parse.urlencode(vparams)}"
        vdata = api_request(vfull_url)

        if not vdata:
            continue

        for vitem in vdata.get("items", []):
            snippet = vitem.get("snippet", {})
            stats = vitem.get("statistics", {})
            details = vitem.get("contentDetails", {})

            video_id = vitem["id"]
            url = f"https://www.youtube.com/watch?v={video_id}"

            videos.append({
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "url": url,
                "published_at": snippet.get("publishedAt", ""),
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "duration": details.get("duration", ""),
                "channel_name": snippet.get("channelTitle", ""),
                "description": snippet.get("description", "")[:500],
                "tags": snippet.get("tags", [])[:10],
            })

        time.sleep(0.5)  # Rate limiting between batches

    return videos


def duration_to_minutes(iso_duration):
    """Convert ISO 8601 duration to minutes."""
    import re
    if not iso_duration:
        return ""
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
    if not match:
        return ""
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    total_minutes = hours * 60 + minutes + round(seconds / 60, 1)
    return str(total_minutes)


def classify_pillar(title, description):
    """Classify video into a content pillar based on title/description keywords."""
    text = (title + " " + description).lower()

    pillars = {
        "Food + Warning": ["food", "eat", "reheat", "drink", "diet", "nutrition", "vitamin", "mineral", "seed", "spice", "nut", "cheese", "coffee", "tea", "water", "meal", "cook", "kitchen"],
        "Medication Warning": ["medication", "pill", "drug", "prescription", "pharmacy", "supplement", "b12", "statin", "antibiotic", "nsaid", "aspirin", "blood pressure medicine"],
        "Heart Attack / Stroke Warning": ["heart", "stroke", "cardiac", "cardiovascular", "blood pressure", "hypertension", "cholesterol", "artery", "clot"],
        "Sleep / Night Peeing": ["sleep", "insomnia", "night", "bladder", "nocturia", "bed", "wake", "tired", "fatigue", "rest"],
        "Leg / Circulation": ["leg", "feet", "circulation", "varicose", "swelling", "edema", "blood flow", "lymphatic", "vein", "calf", "ankle"],
        "Muscle / Strength": ["muscle", "strength", "sarcopenia", "weak", "exercise", "walk", "movement", "balance", "fall", "chair test"],
        "Pain / Joints": ["pain", "joint", "knee", "hip", "arthritis", "inflammation", "back pain", "shouldelder", "stiff"],
        "Brain / Memory": ["brain", "memory", "dementia", "alzheimer", "cognitive", "forget", "mental", "focus", "concentration", "microplastic"],
        "Stem Cell / Anti-Aging": ["stem cell", "anti-aging", "longevity", "aging", "rejuvenate", "regenerate", "telomere"],
        "Organ Damage": ["kidney", "liver", "lung", "organ", "damage", "destroy", "toxin", "microplastic", "plastic"],
        "Longevity / Genetic Risk": ["blood type", "genetic", "lifespan", "longevity", "dna", "hereditary"],
        "Warning / Night Habits": ["habit", "routine", "night", "warning", "never", "stop", "avoid", "danger", "risk"],
        "Body Shock / Embarrassing Health": ["embarrassing", "shame", "rectum", "stool", "gas", "odor", "private"],
        "Cancer Prevention": ["cancer", "tumor", "oncology", "chemotherapy", "radiation", "malignant"],
    }

    for pillar, keywords in pillars.items():
        if any(kw in text for kw in keywords):
            return pillar
    return "General Health"


def classify_hook_type(title):
    """Classify the hook type based on title patterns."""
    title_lower = title.lower()

    if "never" in title_lower:
        return "NEVER warning"
    if "stop" in title_lower:
        return "STOP warning"
    if "warn" in title_lower:
        return "Authority warning"
    if "?" in title:
        return "Question hook"
    if "forgotten" in title_lower:
        return "Forgotten revelation"
    if "simple" in title_lower:
        return "Simple habit"
    if "does your" in title_lower:
        return "Personalized revelation"
    if "died" in title_lower or "death" in title_lower:
        return "Death fear"
    if "sign" in title_lower:
        return "Warning signs"
    if "destroy" in title_lower or "kill" in title_lower:
        return "Destruction claim"
    if "reveal" in title_lower or "truth" in title_lower:
        return "Revelation"
    if "after 60" in title_lower or "after 50" in title_lower or "over 60" in title_lower:
        return "Age-targeted warning"
    return "Informational"


def extract_title_formula(title):
    """Extract the title formula pattern."""
    import re
    title_clean = title.strip()

    # Check for known patterns
    patterns = [
        (r"never\s+\w+", "NEVER [Verb] [Items] After 60"),
        (r"does your\s+\w+", "Does Your [Trait] Reveal [Outcome]?"),
        (r"this forgotten\s+\w+", "This FORGOTTEN [Food] [Verb] [Claim]"),
        (r"no\.?\s*1\s+\w+", "No.1 [Specialty] Reveals the SIMPLE [Claim]"),
        (r"he died", "He Died [Circumstance] From Doing This"),
        (r"\d+\s+signs", "[X] Signs [Time Period] Before [Disaster]"),
        (r"your body is", "Your Body Is [Verb] [Claim]"),
        (r"this common.*habit", "This Common 'Healthy' Habit Is [Verb] [Claim]"),
        (r"ask your doctor", "Ask Your Doctor About [Topic] After 60"),
        (r"\d+\s+(second|minute|hour)", "[Time] [Action] After 60"),
    ]

    title_lower = title_clean.lower()
    for pattern, formula in patterns:
        if re.search(pattern, title_lower):
            return formula

    return "Custom"


def estimate_idea_signal(video):
    """Estimate whether this video should generate a competitor idea."""
    views = video.get("view_count", 0)
    title = video.get("title", "")

    if views > 100000:
        return "STRONG — High view count, proven demand"
    elif views > 50000:
        return "MEDIUM — Solid performance, worth monitoring"
    elif views > 10000:
        return "MONITOR — Early stage, track velocity"
    else:
        return "LOW — Too early to assess"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch competitor videos from YouTube")
    parser.add_argument("--days-back", type=int, default=7, help="Days to look back (default: 7)")
    parser.add_argument("--channel", type=str, help="Scan only a specific channel name")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without API calls")
    parser.add_argument("--repo-root", type=str, default=str(REPO_ROOT), help="Override repo root path")
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    output_dir = repo_root / "data" / "competitors" / "daily"
    output_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    output_path = output_dir / f"{today}_competitors.csv"

    log("INFO", f"Hermes Competitor Video Fetcher — {today}")
    log("INFO", f"Days back: {args.days_back}")
    log("INFO", f"Output: {output_path}")

    # Load watchlist
    channels = load_watchlist()
    if args.channel:
        channels = [c for c in channels if args.channel.lower() in c["channel_name"].lower()]
        if not channels:
            log("ERROR", f"Channel '{args.channel}' not found in watchlist")
            sys.exit(2)

    if args.dry_run:
        log("INFO", f"DRY RUN: Would scan {len(channels)} channels")
        for ch in channels:
            log("INFO", f"  - {ch['channel_name']} ({ch['channel_url']})")
        return

    # Get API key
    keys = get_api_keys()
    primary_key = keys[0]
    log("INFO", f"Using {len(keys)} API key(s)")

    # Calculate published_after
    published_after = (
        datetime.now(timezone.utc) - timedelta(days=args.days_back)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    log("INFO", f"Fetching videos published after: {published_after}")

    # Fetch videos for each channel
    all_videos = []
    total_quota_used = 0

    for i, channel in enumerate(channels):
        channel_name = channel["channel_name"]
        channel_url = channel["channel_url"]

        log("INFO", f"[{i + 1}/{len(channels)}] Scanning: {channel_name}")

        # Extract channel ID
        channel_id = extract_channel_id(channel_url, primary_key)
        if not channel_id:
            log("WARN", f"  Skipping {channel_name} — could not resolve channel ID")
            continue

        log("INFO", f"  Channel ID: {channel_id}")

        # Fetch videos
        videos = fetch_channel_videos(channel_id, published_after, primary_key)
        total_quota_used += QUOTA_PER_CHANNEL

        log("INFO", f"  Found {len(videos)} videos")

        for v in videos:
            pillar = classify_pillar(v["title"], v["description"])
            hook_type = classify_hook_type(v["title"])
            title_formula = extract_title_formula(v["title"])
            idea_signal = estimate_idea_signal(v)

            all_videos.append({
                "date_found": today,
                "channel": channel_name,
                "video_title": v["title"],
                "url": v["url"],
                "published_date": v["published_at"][:10] if v["published_at"] else "",
                "views": v["view_count"],
                "duration": duration_to_minutes(v["duration"]),
                "pillar": pillar,
                "hook_type": hook_type,
                "title_formula": title_formula,
                "thumbnail_text": "",  # To be filled by thumbnail-analyst
                "thumbnail_layout": "",  # To be filled by thumbnail-analyst
                "thumbnail_colors": "",  # To be filled by thumbnail-analyst
                "comment_themes": "",  # To be filled by comment-miner
                "idea_signal": idea_signal,
            })

        time.sleep(0.5)  # Rate limiting between channels

    # Write output CSV
    file_exists = output_path.exists()
    mode = "a" if file_exists else "w"

    with open(output_path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        for v in all_videos:
            writer.writerow(v)

    log("INFO", f"Wrote {len(all_videos)} videos to {output_path}")
    log("INFO", f"Estimated quota used: {total_quota_used} units")
    log("INFO", f"Scan complete — {len(all_videos)} videos from {len(channels)} channels")

    # Log quota usage
    quota_log = {}
    if QUOTA_LOG_PATH.exists():
        quota_log = json.loads(QUOTA_LOG_PATH.read_text())
    quota_log[today] = quota_log.get(today, 0) + total_quota_used
    QUOTA_LOG_PATH.write_text(json.dumps(quota_log, indent=2))


if __name__ == "__main__":
    main()
