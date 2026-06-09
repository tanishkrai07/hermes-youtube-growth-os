#!/usr/bin/env python3
"""Fetch latest videos from competitor YouTube channels via RSS and Invidious."""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import time
import re
import os

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
OUTPUT_DIR = "/home/ec2-user/workspaces/hermes-youtube-growth-os/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Channel IDs gathered from previous scans and known channels
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
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        xml = fetch_url(url)
        root = ET.fromstring(xml)
        ns = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "media": "http://search.yahoo.com/mrss/"}
        results = []
        for entry in root.findall("atom:entry", ns)[:5]:
            title_el = entry.find("atom:title", ns)
            title = title_el.text if title_el is not None else ""
            link_el = entry.find("atom:link", ns)
            link = link_el.get("href", "") if link_el is not None else ""
            video_id_elem = entry.find("yt:videoId", ns)
            video_id = video_id_elem.text if video_id_elem is not None else ""
            pub_el = entry.find("atom:published", ns)
            published = pub_el.text if pub_el is not None else ""
            
            view_count = 0
            desc_text = ""
            media_group = entry.find("media:group", ns)
            if media_group is not None:
                community = media_group.find("media:community", ns)
                if community is not None:
                    stats = community.find("media:statistics", ns)
                    if stats is not None:
                        view_count = int(stats.get("views", 0))
                desc_el = media_group.find("media:description", ns)
                if desc_el is not None and desc_el.text:
                    desc_text = desc_el.text[:200]
            
            results.append({
                "title": title or "",
                "videoId": video_id or "",
                "url": link or f"https://www.youtube.com/watch?v={video_id}",
                "published": published or "",
                "viewCount": view_count,
                "description": desc_text
            })
        return results
    except Exception as e:
        return None

all_results = {}

for channel_name, channel_id in CHANNELS.items():
    print(f"\n=== {channel_name} (ID: {channel_id}) ===")
    rss_results = try_rss_feed(channel_id)
    if rss_results:
        print(f"  RSS: Found {len(rss_results)} videos")
        for v in rss_results:
            vcount = v['viewCount']
            print(f"  [{vcount:,} views] {v['title'][:80]}")
            print(f"    Published: {v['published']}")
            print(f"    {v['url']}")
            print()
        all_results[channel_name] = {"source": "rss", "videos": rss_results}
    else:
        print("  RSS failed, trying Invidious...")
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

# DuckDuckGo searches for newer competitors
print("\n=== Broad elder health searches ===")
SEARCH_QUERIES = [
    "elder health YouTube channel 2026 new viral",
    "senior health warning video YouTube 2026 medication",
    "blood pressure food warning YouTube senior 2026",
    "microplastics health YouTube senior elder 2026",
    "stem cell therapy YouTube elder health 2026",
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
        
        yt_results = []
        for t, u in zip(titles, urls):
            ct = re.sub(r'<[^>]+>', '', t).strip()
            cu = u
            if u.startswith("//duckduckgo.com/l/"):
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(f"https:{u}").query)
                if "uddg" in parsed:
                    cu = urllib.parse.unquote(parsed["uddg"][0])
            if "youtube" in cu.lower() and ct and len(ct) > 10:
                yt_results.append({"title": ct, "url": cu})
        
        if yt_results:
            print(f"\n  Query: {query}")
            for r in yt_results[:3]:
                print(f"    {r['title'][:80]}")
                print(f"    {r['url'][:100]}")
        
        time.sleep(1.5)
    except Exception as e:
        print(f"  Error for '{query}': {e}")

with open(os.path.join(OUTPUT_DIR, "search_results.json"), "w") as f:
    json.dump(all_results, f, indent=2)

print("\nSaved to outputs/search_results.json")
