#!/usr/bin/env python3
"""Search for brand new elder health competitors."""
import subprocess
import json
import time
import os

OUTPUT_DIR = "/home/ec2-user/workspaces/hermes-youtube-growth-os/outputs"

def search_with_views(query, limit=10):
    try:
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--dump-single-json", "--no-download",
             f"ytsearch{limit}:{query}"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return []
        data = json.loads(result.stdout)
        entries = data.get("entries", [])
        videos = []
        import re
        for entry in entries:
            if entry:
                view_count = entry.get("view_count", 0) or 0
                if view_count == 0:
                    title = entry.get("title", "")
                    view_match = re.search(r'([\d,]+)\s*views?', title, re.IGNORECASE)
                    if view_match:
                        view_count = int(view_match.group(1).replace(",", ""))
                videos.append({
                    "id": entry.get("id", ""),
                    "title": entry.get("title", "")[:100],
                    "channel": entry.get("channel", "")[:50],
                    "channel_id": entry.get("channel_id", ""),
                    "view_count": view_count,
                    "upload_date": entry.get("upload_date", ""),
                    "duration": entry.get("duration", 0),
                })
        return videos
    except Exception as e:
        print(f"Error: {e}")
        return []

# Search for new/emerging channels
NEW_SEARCHES = [
    ("senior health warning video 2026 YouTube new channel", "New Warning Channels"),
    ("elder health medication danger YouTube 2026 new", "New Med Channels"),
    ("over 60 health tips YouTube new 2026 viral", "New General Health"),
    ("senior wellness YouTube channel 2026 breakout", "New Breakout Channels"),
    ("blood pressure food YouTube senior 2026 new", "New BP Channels"),
    ("diabetes senior YouTube 2026 new channel", "New Diabetes Channels"),
    ("cancer prevention senior YouTube 2026 new", "New Cancer Channels"),
    ("heart health senior YouTube 2026 new viral", "New Heart Channels"),
]

all_new = {}
for query, label in NEW_SEARCHES:
    print(f"\n=== {label} ===")
    vids = search_with_views(query, 10)
    if vids:
        all_new[label] = vids
        for v in vids[:5]:
            vc = v['view_count']
            ch = v['channel'][:30] if v['channel'] else "?"
            ud = v['upload_date'] if v['upload_date'] else "?"
            print(f"  [{vc:>10,} views] [{ch}] ({ud}) {v['title'][:65]}")
    time.sleep(2)

with open(os.path.join(OUTPUT_DIR, "new_competitors.json"), "w") as f:
    json.dump(all_new, f, indent=2, ensure_ascii=False)

print(f"\nSaved to outputs/new_competitors.json")
