#!/usr/bin/env python3
"""Fetch video metadata using noembed.com (no auth required)."""
import urllib.request
import json
import time
import os

OUTPUT_DIR = "/home/ec2-user/workspaces/hermes-youtube-growth-os/outputs"

# Key videos to check
VIDEOS = [
    # Claire Whitmore latest
    ("UrCnGoHBj5E", "Claire Whitmore", "Amlodipine Dose Getting Stronger"),
    ("WuEQDCkZ0LA", "Claire Whitmore", "Anxiety And High Blood Pressure Missing Mineral"),
    ("CRMH6PL2W6k", "Claire Whitmore", "Amlodipine Losartan Lisinopril trio"),
    ("_43ErjAKJWU", "Claire Whitmore", "Lisinopril Poisoning Kidneys"),
    ("kq-L3ZWpE8c", "Claire Whitmore", "Only Magnesium Type Lowers BP"),
    ("msrvRuWgr8c", "Claire Whitmore", "Vitamin D Deficiency Destroying Leg Muscles"),
    ("-mLykdTuZbA", "Claire Whitmore", "Forgotten Morning Habit Destroys Hypertension"),
    
    # Dr. Michael Kent latest
    ("F3phhk_savo", "Dr. Michael Kent", "Amlodipine After 5 Years"),
    ("efE27656DnI", "Dr. Michael Kent", "Healthy People High BP Hidden Cause"),
    ("gsCFaEIkDdc", "Dr. Michael Kent", "Drink water avoid getting up at night"),
    ("lvm89a32lHc", "Dr. Michael Kent", "Eat Eggs Correctly Diabetic"),
    ("Y_3k00KY-44", "Dr. Michael Kent", "Best Blood Sugar for Older Adults"),
    
    # Dr. Waterling
    ("7fBA7AtzEPU", "Dr. Waterling", "BE-FAST Test Detect Stroke 30 Seconds"),
    ("TH95KRLlXXo", "Dr. Waterling", "7 Days Before Stroke 5 Warnings"),
    
    # Dr. Franklin
    ("IkmdX23vNdg", "Dr. Franklin", "NAILS Look Like THIS After 60"),
    
    # Dr. James Hargrove
    ("rEC-3yyL5QQ", "Dr. James Hargrove", "4 Vitamins SILENTLY Causing Stroke"),
    ("mer4cQJp-s4", "Dr. James Hargrove", "Legs Tingle Burn Numb After 60"),
    ("z8bU01_ynbo", "Dr. James Hargrove", "NEVER Take B12 With THESE 2 Medications"),
    
    # Doctor Christopher Carter
    ("KZNLGMwshXU", "Doctor Christopher Carter", "5 Pills Could Trigger Heart Attack"),
    ("Qvo63LmUmH0", "Doctor Christopher Carter", "6 Medicines Skyrocket Heart Attack Risk"),
    
    # Dr. James Cross
    ("3WfRQrZXVKI", "Dr. James Cross", "Simple Movement Drains Swollen Legs"),
    ("P5QQzv7vct8", "Dr. James Cross", "Swollen Ankles Not Your Heart Its Your Lymph"),
    
    # Doctor Becker microplastics
    ("Tjkb8oKHCjE", "Doctor Becker", "Plastic Found INSIDE Body Cells"),
    
    # New competitors
    ("P1I8rnTi-U8", "Dr. Michael Carter (NEW)", "5 Common Medications DAMAGE Heart"),
    ("0Tk7yZpY2Wo", "Dr. Sarah Mitchell (NEW)", "Common Pill Silently Damaging Heart"),
    ("5t9X6in63-E", "Dr. Paul Bennett (NEW)", "Common Pill May Be TOXIC for Seniors"),
    ("3sUIhGSjHF0", "Dr. Paul Bennett 2 (NEW)", "Stop Chasing 120/80 BP Targets"),
    ("NAtDo5uiBiY", "Dr. Olivia Parker (NEW)", "5 Common Medications Raise Heart Attack Stroke Risk"),
    
    # Senior Health Blog
    ("HxnsPhTIXQs", "Dr. Michael Kent", "8 Signs of Mini Strokes in Elderly"),
]

def get_noembed(video_id):
    """Use noembed.com to get video metadata."""
    url = f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return {
                "title": data.get("title", ""),
                "author": data.get("author_name", ""),
                "author_url": data.get("author_url", ""),
            }
    except Exception as e:
        return None

# noembed doesn't give view counts. Let's try a different approach.
# Use the YouTube oembed endpoint + scrape view counts from the page

def get_yt_page_info(video_id):
    """Scrape basic info from YouTube video page."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        
        # Extract view count from initial data
        import re
        
        # Try to find viewCount in ytInitialPlayerResponse
        match = re.search(r'"viewCount":"(\d+)"', html)
        view_count = int(match.group(1)) if match else 0
        
        # Try to find title
        title_match = re.search(r'"title":"([^"]+)"', html)
        title = title_match.group(1) if title_match else ""
        # Unescape
        title = title.replace("\\u0026", "&").replace("\\\"", '"')
        
        # Try to find channel name
        channel_match = re.search(r'"author":"([^"]+)"', html)
        channel = channel_match.group(1) if channel_match else ""
        
        # Try to find upload date
        date_match = re.search(r'"uploadDate":"([^"]+)"', html)
        upload_date = date_match.group(1) if date_match else ""
        
        # Try to find duration
        dur_match = re.search(r'"lengthSeconds":"(\d+)"', html)
        duration = int(dur_match.group(1)) if dur_match else 0
        
        # Check if video exists / is available
        if "Video unavailable" in html or "This video is not available" in html:
            return {"error": "Video unavailable"}
        
        return {
            "view_count": view_count,
            "title": title[:100],
            "channel": channel[:50],
            "upload_date": upload_date,
            "duration": duration,
        }
    except Exception as e:
        return {"error": str(e)[:100]}

results = []
for video_id, expected_channel, title_hint in VIDEOS:
    info = get_yt_page_info(video_id)
    if "error" not in info and info.get("view_count", 0) > 0:
        results.append({
            "video_id": video_id,
            "expected_channel": expected_channel,
            "channel": info.get("channel", ""),
            "title": info.get("title", title_hint)[:100],
            "views": info.get("view_count", 0),
            "upload_date": info.get("upload_date", ""),
            "duration": info.get("duration", 0),
            "url": f"https://www.youtube.com/watch?v={video_id}"
        })
        dur_min = info.get("duration", 0) // 60
        dur_sec = info.get("duration", 0) % 60
        print(f"[{info['view_count']:>10,} views] {info['title'][:70]}")
        print(f"           Ch: {info.get('channel', '?')[:35]} | {info.get('upload_date', '?')} | {dur_min}:{dur_sec:02d}")
        print()
    elif "error" in info:
        print(f"[ERROR] {video_id} ({expected_channel}): {info['error']}")
        print()
    else:
        print(f"[NO DATA] {video_id} ({expected_channel}): {title_hint}")
        print()
    time.sleep(1.5)

with open(os.path.join(OUTPUT_DIR, "video_counts.json"), "w") as f:
    json.dump(results, f, indent=2)

print(f"\nTotal videos with view counts: {len(results)}")
print("Saved to outputs/video_counts.json")
