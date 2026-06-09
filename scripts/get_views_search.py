#!/usr/bin/env python3
"""Get view counts using yt-dlp search with JSON output."""
import subprocess
import json
import time
import os
import re

OUTPUT_DIR = "/home/ec2-user/workspaces/hermes-youtube-growth-os/outputs"

def search_with_views(query, limit=10):
    """Search YouTube and get videos with view counts using yt-dlp."""
    try:
        # Use yt-dlp to search and output JSON
        result = subprocess.run(
            ["yt-dlp", 
             "--flat-playlist",
             "--dump-single-json",
             "--no-download",
             f"ytsearch{limit}:{query}"],
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode != 0:
            return []
        
        data = json.loads(result.stdout)
        entries = data.get("entries", [])
        
        videos = []
        for entry in entries:
            if entry:
                view_count = entry.get("view_count", 0) or 0
                # Try to get view count from viewCount field in description or title
                if view_count == 0:
                    # Some results embed view count in the title field
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
                    "url": f"https://www.youtube.com/watch?v={entry.get('id', '')}"
                })
        return videos
    except Exception as e:
        print(f"Error: {e}")
        return []

# Search for each competitor's latest videos
SEARCHES = [
    ("Claire Whitmore Senior Health Tips latest", "Claire Whitmore"),
    ("Dr. Michael Kent Senior Health latest", "Dr. Michael Kent"),
    ("Dr. Waterling stroke elder health latest", "Dr. Waterling"),
    ("Doctor Becker stem cell microplastics latest", "Doctor Becker"),
    ("Dr. Franklin nail health elder latest", "Dr. Franklin"),
    ("Senior Health Blog diabetes latest", "Senior Health Blog"),
    ("Dr. James Cross leg health swollen ankles latest", "Dr. James Cross"),
    ("Dr. James Hargrove vitamin stroke elder latest", "Dr. James Hargrove"),
    ("Doctor Christopher Carter heart medication elder latest", "Doctor Christopher Carter"),
    ("Dr. Favor Adeyemi food warning cancer latest", "Dr. Favor Adeyemi"),
    ("Dr. Adewale blood pressure kitchen elder latest", "Dr. Adewale"),
    ("Dr.Robert Harrison eye health elder latest", "Dr.Robert Harrison"),
    ("Dr. Richard Ben kidney urologist elder latest", "Dr. Richard Ben"),
    ("Healthy Seniors stroke TIA elder latest", "Healthy Seniors"),
    ("new elder health YouTube 2026 medication warning", "New Competitors"),
    ("microplastics seniors health YouTube 2026", "Microplastics"),
    ("blood type longevity elder YouTube 2026", "Blood Type"),
]

all_results = {}
for query, label in SEARCHES:
    print(f"\n=== {label} ===")
    vids = search_with_views(query, 10)
    if vids:
        all_results[label] = vids
        for v in vids[:5]:
            vc = v['view_count']
            ch = v['channel'][:30] if v['channel'] else "?"
            ud = v['upload_date'] if v['upload_date'] else "?"
            print(f"  [{vc:>10,} views] [{ch}] {v['title'][:70]}")
            print(f"    {v['url']}")
    else:
        print("  No results")
    time.sleep(2)

with open(os.path.join(OUTPUT_DIR, "competitor_views.json"), "w") as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)

total_vids = sum(len(v) for v in all_results.values())
print(f"\n\nTotal: {len(all_results)} searches, {total_vids} videos")
print("Saved to outputs/competitor_views.json")
