#!/usr/bin/env python3
"""Fetch latest videos from competitor YouTube channels via RSS and Invidious."""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import time
import re

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Channel IDs gathered from previous scans
CHANNELS = {
    "Claire Whitmore": "UCODPc2YXjPVCrQpp3FBhSyw",
    "Dr. Michael Kent": "UCF3kiJHw9D6yVGl4l5KqlGQ",
}

# Invidious instances to try
INSTANCES = [
    "https://vid.puffyan.us",
    "https://invidious.fdn.fr",
    "https://y.com.sb",
    "https://invidious.nerdvpn.de",
    "https://inv.nadeko.net",
]

def fetch_url(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")

def try_invidious_channel(channel_id, instance):
    """Try to get channel videos via Invidious API."""
    url = f"{instance}/api/v1/channels/{channel_id}/videos?page=1"
    try:
        data = json.loads(fetch_url(url))
        videos = data.get("videos", [])
        results = []
        for v in videos[:5]:
            results.append({
                "title": v.get("title", ""),
                "videoId": v.get("videoId", ""),
                "viewCount": v.get("viewCount", 0),
                "published": v.get("published", 0),
                "url": f"https://www.youtube.com/watch?v={v.get('videoId', '')}"
            })
        return results
    except Exception as e:
        return None

def try_rss_feed(channel_id):
    """Try to get channel videos via YouTube RSS feed."""
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        xml = fetch_url(url)
        root = ET.fromstring(xml)
        ns = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "media": "http://search.yahoo.com/mrss/"}
        results = []
        for entry in root.findall("atom:entry", ns)[:5]:
            title = entry.find("atom:title", ns).text if entry.find("atom:title", ns) is not None else ""
            link = entry.find("atom:link", ns).get("href", "") if entry.find("atom:link", ns) is not None else ""
            video_id_elem = entry.find("yt:videoId", ns)
            video_id = video_id_elem.text if video_id_elem is not None else ""
            published = entry.find("atom:published", ns).text if entry.find("atom:published", ns) is not None else ""
            
            # Get view count from media:group
            media_group = entry.find("media:group", ns)
            view_count = 0
            if media_group is not None:
                community = media_group.find("media:community", ns)
                if community is not None:
                    stats = community.find("media:statistics", ns)
                    if stats is not None:
                        view_count = int(stats.get("views", 0))
            
            # Get description
            desc = ""
            if media_group is not None:
                desc_elem = media_group.find("media:description", ns)
                if desc_elem is not None:
                    desc = desc_elem.text or ""
            
            results.append({
                "title": title,
                "videoId": video_id,
                "url": link or f"https://www.youtube.com/watch?v={video_id}",
                "published": published,
                "viewCount": view_count,
                "description": desc[:200] if desc else ""
            })
        return results
    except Exception as e:
        return None

all_results = {}

for channel_name, channel_id in CHANNELS.items():
    print(f"\n=== {channel_name} (ID: {channel_id}) ===")
    
    # Try RSS first (most reliable)
    rss_results = try_rss_feed(channel_id)
    if rss_results:
        print(f"  RSS: Found {len(rss_results)} videos")
        for v in rss_results:
            print(f"  [{v['viewCount']:,} views] {v['title'][:80]}")
            print(f"    Published: {v['published']}")
            print(f"    {v['url']}")
            print()
        all_results[channel_name] = {"source": "rss", "videos": rss_results}
    else:
        print("  RSS failed, trying Invidious...")
        # Try Invidious instances
        found = False
        for instance in INSTANCES:
            inv_results = try_invidious_channel(channel_id, instance)
            if inv_results:
                print(f"  Invidious ({instance}): Found {len(inv_results)} videos")
                for v in inv_results:
                    print(f"  [{v['viewCount']:,} views] {v['title'][:80]}")
                    print(f"    {v['url']}")
                    print()
                all_results[channel_name] = {"source": f"invidious:{instance}", "videos": inv_results}
                found = True
                break
            time.sleep(0.5)
        if not found:
            print("  All sources failed")
            all_results[channel_name] = {"source": "failed", "videos": []}

# Also try to get more channels via web scraping
print("\n\n=== Attempting broad elder health searches ===")

SEARCH_QUERIES = [
    "elder health YouTube channel 2026 viral",
    "senior health warning video YouTube 2026",
    "blood pressure medication video YouTube elder 2026",
]

for query in SEARCH_QUERIES:
    try:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)
        urls = re.findall(r'class="result__a"[^>]*href="([^"]+)"', html)
        
        print(f"\nQuery: {query}")
        clean = []
        for t in titles[:5]:
            ct = re.sub(r'<[^>]+>', '', t).strip()
            if ct and len(ct) > 10:
                clean.append(ct)
        
        clean_urls = []
        for u in urls[:5]:
            if u.startswith("//duckduckgo.com/l/"):
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(f"https:{u}").query)
                if "uddg" in parsed:
                    clean_urls.append(urllib.parse.unquote(parsed["uddg"][0]))
            elif u.startswith("http"):
                clean_urls.append(u)
        
        for t, u in zip(clean[:3], clean_urls[:3]):
            if "youtube" in u.lower():
                print(f"  {t[:80]}")
                print(f"    {u[:100]}")
        
        time.sleep(1)
    except Exception as e:
        print(f"  Error: {e}")

# Save all results
with open("/home/ec2-user/workspaces/hermes-youtube-growth-os/outputs/search_results.json", "w") as f:
    json.dump(all_results, f, indent=2)

print("\n\nSaved to outputs/search_results.json")
