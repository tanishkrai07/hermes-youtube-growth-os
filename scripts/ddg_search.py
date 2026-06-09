#!/usr/bin/env python3
"""Search DuckDuckGo HTML for competitor YouTube videos."""
import urllib.request
import urllib.parse
import re
import json
import time

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

QUERIES = [
    ("Claire Whitmore", "Claire Whitmore YouTube latest video 2026 elder health blood pressure"),
    ("Dr. Michael Kent", "Dr. Michael Kent YouTube latest video 2026 blood pressure dementia elder"),
    ("Dr. Waterling", "Dr. Waterling YouTube stroke video 2026 latest"),
    ("Doctor Becker", "Doctor Becker YouTube stem cell microplastics 2026 latest"),
    ("Dr. Franklin", "Dr. Franklin YouTube nail health body shock 2026 latest"),
    ("Senior Health Blog", "Senior Health Blog YouTube latest video 2026 diabetes nutrition"),
    ("Dr. James Cross", "Dr. James Cross YouTube leg health swollen ankles 2026 latest"),
    ("Healthy Seniors", "Healthy Seniors YouTube stroke TIA 2026 latest"),
    ("Dr. Richard Ben", "Dr. Richard Ben YouTube kidney urologist 2026 latest"),
    ("Dr. James Hargrove", "Dr. James Hargrove YouTube vitamin stroke 2026 latest"),
    ("new elder health channels 2026", "new elder health YouTube channels 2026 60+ senior wellness"),
    ("elder health YouTube viral 2026", "elder health senior YouTube viral video 2026 medication warning"),
]

results = {}

for label, query in QUERIES:
    try:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        
        # Extract result titles and URLs
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)
        urls = re.findall(r'class="result__a"[^>]*href="([^"]+)"', html)
        
        clean_titles = []
        for t in titles[:5]:
            clean = re.sub(r'<[^>]+>', '', t).strip()
            if clean:
                clean_titles.append(clean)
        
        clean_urls = []
        for u in urls[:5]:
            # DuckDuckGo redirects: //duckduckgo.com/l/?uddg=...
            if u.startswith("//duckduckgo.com/l/"):
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(f"https:{u}").query)
                if "uddg" in parsed:
                    clean_urls.append(urllib.parse.unquote(parsed["uddg"][0]))
            elif u.startswith("http"):
                clean_urls.append(u)
        
        results[label] = {"titles": clean_titles, "urls": clean_urls[:5]}
        print(f"[{label}] Found {len(clean_titles)} results")
        for i, (t, u) in enumerate(zip(clean_titles[:3], clean_urls[:3])):
            print(f"  {i+1}. {t[:80]}")
            print(f"     {u[:100]}")
        print()
        time.sleep(1)  # Rate limit
    except Exception as e:
        results[label] = {"error": str(e)}
        print(f"[{label}] ERROR: {e}")
        print()

# Save results
with open("/home/ec2-user/workspaces/hermes-youtube-growth-os/outputs/search_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("Results saved to outputs/search_results.json")
