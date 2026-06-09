#!/usr/bin/env python3
"""Comprehensive competitor video fetch using yt-dlp."""
import subprocess
import json
import re
import os
import time

OUTPUT_DIR = "/home/ec2-user/workspaces/hermes-youtube-growth-os/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def yt_dlp_search(query, limit=10):
    """Use yt-dlp to search YouTube and return video info."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--print", 
             "%(channel_id)s | %(channel)s | %(id)s | %(title)s | %(view_count)s | %(upload_date)s | %(duration)s",
             f"ytsearch{limit}:{query}"],
            capture_output=True, text=True, timeout=60
        )
        videos = []
        for line in result.stdout.strip().split("\n"):
            if " | " in line:
                parts = line.split(" | ")
                if len(parts) >= 4:
                    videos.append({
                        "channel_id": parts[0],
                        "channel": parts[1],
                        "video_id": parts[2],
                        "title": parts[3],
                        "view_count": parts[4] if len(parts) > 4 else "NA",
                        "upload_date": parts[5] if len(parts) > 5 else "NA",
                        "duration": parts[6] if len(parts) > 6 else "NA",
                        "url": f"https://www.youtube.com/watch?v={parts[2]}"
                    })
        return videos
    except Exception as e:
        print(f"Error for query '{query}': {e}")
        return []

def yt_dlp_channel(channel_id, limit=10):
    """Fetch videos from a specific channel."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--print",
             "%(channel_id)s | %(channel)s | %(id)s | %(title)s | %(view_count)s | %(upload_date)s | %(duration)s",
             f"https://www.youtube.com/channel/{channel_id}/videos"],
            capture_output=True, text=True, timeout=60
        )
        videos = []
        for line in result.stdout.strip().split("\n"):
            if " | " in line:
                parts = line.split(" | ")
                if len(parts) >= 4:
                    videos.append({
                        "channel_id": parts[0],
                        "channel": parts[1],
                        "video_id": parts[2],
                        "title": parts[3],
                        "view_count": parts[4] if len(parts) > 4 else "NA",
                        "upload_date": parts[5] if len(parts) > 5 else "NA",
                        "duration": parts[6] if len(parts) > 6 else "NA",
                        "url": f"https://www.youtube.com/watch?v={parts[2]}"
                    })
        return videos
    except Exception as e:
        print(f"Error for channel {channel_id}: {e}")
        return []

# Known channel IDs
KNOWN_CHANNELS = {
    "Claire Whitmore": "UCODPc2YXjPVCrQpp3FBhSyw",
    "Dr. Michael Kent": "UCysWUz-N1hK_JfLJ1nOF7EA",
}

all_data = {}

# Fetch known channels
for name, cid in KNOWN_CHANNELS.items():
    print(f"\n=== {name} (channel) ===")
    vids = yt_dlp_channel(cid, 10)
    if vids:
        all_data[name] = vids
        for v in vids[:7]:
            vc = v['view_count']
            ud = v['upload_date']
            print(f"  [{vc} views, {ud}] {v['title'][:80]}")
            print(f"    {v['url']}")
            print()
    else:
        print(f"  Failed, trying search...")
        search_vids = yt_dlp_search(f"{name} elder health", 10)
        all_data[name] = search_vids
        for v in search_vids[:7]:
            vc = v['view_count']
            ud = v['upload_date']
            print(f"  [{vc} views, {ud}] {v['title'][:80]}")

time.sleep(2)

# Search queries for other competitors and new channels
SEARCHES = [
    ("Dr. Waterling stroke elder health", "Dr. Waterling"),
    ("Doctor Becker stem cell microplastics elder", "Doctor Becker"),
    ("Dr. Franklin nail health body shock elder", "Dr. Franklin"),
    ("Senior Health Blog diabetes nutrition elder", "Senior Health Blog"),
    ("Dr. James Cross leg health swollen ankles", "Dr. James Cross"),
    ("Healthy Seniors stroke TIA mini-stroke", "Healthy Seniors"),
    ("Dr. Richard Ben kidney urologist elder", "Dr. Richard Ben"),
    ("Dr. James Hargrove vitamin stroke elder", "Dr. James Hargrove"),
    ("Doctor Christopher Carter heart medication elder", "Doctor Christopher Carter"),
    ("Dr. Favor Adeyemi food warning cancer elder", "Dr. Favor Adeyemi"),
    ("Dr. Adewale blood pressure kitchen elder", "Dr. Adewale"),
    ("Dr.Robert Harrison eye health elder", "Dr.Robert Harrison"),
    ("new elder health YouTube channel 2026 senior warning", "New Competitors"),
    ("microplastics health risks seniors 2026 YouTube", "Microplastics Competitors"),
    ("blood type health longevity elder YouTube 2026", "Blood Type Competitors"),
    ("medication warning seniors YouTube viral 2026", "Medication Warning Competitors"),
    ("leg health circulation seniors YouTube 2026", "Leg Health Competitors"),
    ("stem cell therapy seniors YouTube 2026", "Stem Cell Competitors"),
]

for query, label in SEARCHES:
    print(f"\n=== Search: {label} ===")
    vids = yt_dlp_search(query, 8)
    if vids:
        all_data[label] = vids
        for v in vids[:5]:
            vc = v['view_count']
            ud = v['upload_date']
            ch = v['channel'][:30] if v['channel'] else "?"
            print(f"  [{ch}] [{vc} views, {ud}] {v['title'][:80]}")
    else:
        print("  No results")
    time.sleep(1)

# Save all data
with open(os.path.join(OUTPUT_DIR, "competitor_videos_raw.json"), "w") as f:
    json.dump(all_data, f, indent=2, ensure_ascii=False)

print(f"\n\nTotal channels/searches with data: {len(all_data)}")
print(f"Total videos collected: {sum(len(v) for v in all_data.values())}")
print("Saved to outputs/competitor_videos_raw.json")
