#!/usr/bin/env python3
"""Fetch DDG search results without using curl pipes."""
import urllib.request
import re
import json
import time

def ddg_search(query):
    """Search DuckDuckGo HTML and return results."""
    encoded = urllib.parse.quote(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        return [], str(e)
    
    # Extract results
    results = []
    
    # Pattern 1: result__a links with href
    link_pattern = re.compile(r'<a rel="nofollow" class="result__a" href="([^"]*)">(.*?)</a>', re.DOTALL)
    links = link_pattern.findall(html)
    
    # Pattern 2: snippet text  
    snippet_pattern = re.compile(r'class="result__snippet"[^>]*>(.*?)</a>', re.DOTALL)
    snippets_raw = snippet_pattern.findall(html)
    
    # Clean snippets
    snippets = []
    for s in snippets_raw:
        clean = re.sub(r'<[^>]+>', '', s).strip()
        snippets.append(clean)
    
    for i, (url_raw, title_raw) in enumerate(links[:12]):
        title = re.sub(r'<[^>]+>', '', title_raw).strip()
        title = title.replace('&#x27;', "'").replace('&amp;', '&').replace('&quot;', '"')
        snippet = snippets[i] if i < len(snippets) else ''
        results.append({'title': title, 'url': url_raw, 'snippet': snippet})
    
    return results, None

import urllib.parse

# Define searches - focus on the most important queries
searches = {
    "Claire Whitmore latest videos": '"Claire Whitmore" YouTube "blood pressure" OR "heart" OR "leg" 2026',
    "Doctor Becker stem cell microplastics": '"Doctor Becker" YouTube "stem cell" OR "microplastics" seniors 2026',
    "Dr Waterling stroke 2026": '"Dr. Waterling" YouTube "stroke" OR "mini stroke" 2026',
    "Dr Michael Kent new 2026": '"Dr. Michael Kent" YouTube "intestinal" OR "magnesium" OR "vitamin" 2026',
    "Dr Franklin nail copycat 2026": '"Dr. Franklin" YouTube "nail" OR "neurologist" seniors 2026',
    "Dr Adewale new 2026": '"Dr. Adewale" YouTube "blood pressure" OR "kitchen" 2026',
    "Senior Health Blog new 2026": '"Senior Health Blog" YouTube breakfast diabetes 2026',
    "Dr James Cross legs 2026": '"Dr. James Cross" YouTube "leg" OR "swollen" 2026',
}

all_results = {}

for name, query in searches.items():
    print(f"\n{'='*60}")
    print(f"Searching: [{name}]")
    print(f"Query: {query}")
    
    results, err = ddg_search(query)
    
    if err:
        print(f"ERROR: {err}")
    else:
        print(f"Found {len(results)} results")
        for i, r in enumerate(results[:5]):
            print(f"  [{i+1}] {r['title'][:80]}")
            print(f"      URL: {r['url'][:100]}")
            if r['snippet']:
                print(f"      Snippet: {r['snippet'][:150]}")
    
    all_results[name] = {'query': query, 'results': results, 'error': err}
    time.sleep(1)  # Rate limit

# Save to file
with open('/tmp/ddg_results.json', 'w') as f:
    json.dump(all_results, f, indent=2, default=str)

print(f"\n\nAll results saved to /tmp/ddg_results.json")
