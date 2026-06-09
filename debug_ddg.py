#!/usr/bin/env python3
"""Debug: fetch raw DDG response."""
import urllib.request
import urllib.parse

query = '"Doctor Becker" YouTube "stem cell" seniors 2026'
encoded = urllib.parse.quote(query)
url = f"https://html.duckduckgo.com/html/?q={encoded}"

req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
})

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='replace')
    
    print(f"Status: {resp.status}")
    print(f"Size: {len(html)} bytes")
    
    # Check for bot/captcha
    if 'botnet' in html.lower() or 'captcha' in html.lower():
        print("BOT DETECTION/CAPTCHA PAGE")
    
    # Save to file
    with open('/tmp/ddg_debug.html', 'w') as f:
        f.write(html)
    
    # Print first 1000 chars
    print("\nFirst 1000 chars:")
    print(html[:1000])
    
    # Check for results
    import re
    results = re.findall(r'class="result__a"', html)
    print(f"\nresult__a elements found: {len(results)}")
    
    # Check for result divs
    result_divs = re.findall(r'class="result[\s"]', html)
    print(f"result divs found: {len(result_divs)}")
    
except Exception as e:
    print(f"Error: {e}")
