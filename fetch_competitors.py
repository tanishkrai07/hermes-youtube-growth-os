#!/usr/bin/env python3
"""Fetch competitor data from YouTube and Glasp."""
import urllib.request
import re
import json
import time

def fetch_url(url, user_agent=None):
    """Fetch URL content."""
    ua = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    req = urllib.request.Request(url, headers={
        'User-Agent': ua,
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode('utf-8', errors='replace'), resp.status
    except Exception as e:
        return None, str(e)

def extract_youtube_data(html, channel_name):
    """Extract video titles and metadata from YouTube search/channel pages."""
    videos = []
    
    # Pattern for video titles in search results
    title_patterns = [
        re.compile(r'"title":\{"runs":\[\{"text":"([^"]+)"\}\]'),
        re.compile(r'"title":"([^"]+)"'),
        re.compile(r'aria-label="([^"]+?)(?:\s+by\s+)'),
    ]
    
    view_patterns = [
        re.compile(r'"viewCountText":\{"simpleText":"([^"]+)"\}'),
        re.compile(r'"viewCount":"([^"]+)"'),
    ]
    
    url_patterns = [
        re.compile(r'"videoId":"([^"]{11})"'),
        re.compile(r'href="/watch\?v=([^"]{11})"'),
    ]
    
    for p in title_patterns:
        for m in p.finditer(html):
            # Filter out navigation/menu items
            title = m.group(1)
            if len(title) > 10 and len(title) < 200:
                if any(kw in title.lower() for kw in ['health', 'senior', 'blood', 'heart', 'stroke', 'leg', 'vitamin', 'doctor', 'over', 'warning', 'never', 'best', 'worst', 'food', 'medic', 'brain', 'kidney', 'eye', 'nail', 'cancer', 'diabet', 'sleep', 'pain', 'swollen', 'breath', 'nerve', 'muscle', 'bone']):
                    videos.append({'title': title, 'channel': channel_name})
    
    return videos[:15]

# Main searches to perform
print("=" * 60)
print("COMPETITOR INTELLIGENCE GATHERING - June 8, 2026")
print("=" * 60)

# 1. Try fetching YouTube search results for each competitor
competitor_searches = [
    ("Claire Whitmore", "https://www.youtube.com/results?search_query=%22Claire+Whitmore%22+senior+health+2026&sp=CAI%253D"),
    ("Dr. Waterling", "https://www.youtube.com/results?search_query=%22Dr.+Waterling%22+stroke+seniors+2026&sp=CAI%253D"),
    ("Dr. Michael Kent", "https://www.youtube.com/results?search_query=%22Dr.+Michael+Kent%22+senior+health+2026&sp=CAI%253D"),
    ("Doctor Becker", "https://www.youtube.com/results?search_query=%22Doctor+Becker%22+stem+cell+seniors+2026&sp=CAI%253D"),
    ("Dr. Franklin", "https://www.youtube.com/results?search_query=%22Dr.+Franklin%22+senior+health+2026&sp=CAI%253D"),
]

all_videos = {}

for name, url in competitor_searches:
    print(f"\n[{name}]")
    print(f"  URL: {url[:80]}...")
    
    html, status = fetch_url(url)
    
    if html is None:
        print(f"  ERROR: {status}")
        continue
    
    print(f"  Fetched {len(html)} bytes (status: {status})")
    
    videos = extract_youtube_data(html, name)
    print(f"  Found {len(videos)} relevant videos")
    
    for v in videos[:5]:
        print(f"    - {v['title'][:80]}")
    
    all_videos[name] = videos
    time.sleep(2)

# 2. Try Glasp for Claire Whitmore summary
print(f"\n[Glasp - Claire Whitmore Summary]")
glasp_url = "https://glasp.co/youtube/channel/UCODPc2YXjPVCrQpp3FBhSyw"
html, status = fetch_url(glasp_url)
if html:
    print(f"  Fetched {len(html)} bytes")
    # Extract video titles
    titles = re.findall(r'<a[^>]*class="[^"]*video[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
    if not titles:
        titles = re.findall(r'"title":"([^"]{10,100})"', html)
    for t in titles[:10]:
        clean = re.sub(r'<[^>]+>', '', t).strip()
        if clean:
            print(f"    - {clean[:80]}")
else:
    print(f"  ERROR: {status}")

# 3. Try fetching YouTube channel pages directly
print(f"\n[YouTube Channel Pages]")
channel_urls = [
    ("Claire Whitmore", "https://www.youtube.com/@ClaireWhitmoreSeniorsHealth/videos"),
    ("Dr. Waterling", "https://www.youtube.com/results?search_query=%22Dr.+Waterling%22&sp=CAI%253D"),
]

for name, url in channel_urls:
    print(f"\n  [{name}]")
    html, status = fetch_url(url)
    if html:
        print(f"    Fetched {len(html)} bytes")
        # Look for video titles
        titles = re.findall(r'"title":\{"runs":\[\{"text":"([^"]{5,150})"\}\]', html)
        for t in titles[:8]:
            print(f"      - {t[:80]}")
    else:
        print(f"    ERROR: {status}")
    time.sleep(2)

# Save results
with open('/tmp/competitor_raw.json', 'w') as f:
    json.dump(all_videos, f, indent=2, default=str)

print(f"\n\nRaw data saved to /tmp/competitor_raw.json")
