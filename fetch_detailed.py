#!/usr/bin/env python3
"""Extract detailed video data from YouTube search HTML."""
import urllib.request
import re
import json

def extract_video_details(html, channel_name):
    """Extract structured video data from YouTube search results."""
    videos = []
    
    # YouTube stores data in ytInitialData JSON blob
    data_match = re.search(r'var ytInitialData = ({.*?});', html, re.DOTALL)
    if not data_match:
        # Try alternative pattern
        data_match = re.search(r'"contents":\{"twoColumnSearchResultsRenderer"', html, re.DOTALL)
        if not data_match:
            return videos
    
    # Extract video renderers - each contains videoId, title, viewCount, publishedTime
    # Pattern 1: Full video renderer extraction
    video_patterns = re.findall(
        r'\{"videoRenderer":\{"videoId":"([^"]+)".*?"title":\{"runs":\[\{"text":"([^"]+)"\}\].*?'
        r'(?:'r'"viewCountText":\{"simpleText":"([^"]+)"\}'
        r'.*?"publishedTimeText":\{"simpleText":"([^"]+)"\})?',
        html
    )
    
    for match in video_patterns[:15]:
        video_id = match[0]
        title = match[1].replace('\\u0026', '&').replace('\\"', '"')
        views = match[2] if match[2] else 'N/A'
        published = match[3] if match[3] else 'N/A'
        
        # Filter: only include videos that look like senior health content
        health_keywords = ['health', 'senior', 'blood', 'heart', 'stroke', 'leg', 'vitamin', 
                          'doctor', 'over', 'warning', 'never', 'best', 'worst', 'food', 'medic',
                          'brain', 'kidney', 'eye', 'nail', 'cancer', 'diabet', 'sleep', 'pain',
                          'swollen', 'breath', 'nerve', 'muscle', 'bone', 'sugar', 'pressure',
                          'artery', 'cell', 'stem', 'dementia', 'alzheimer', 'magnesium', 'water',
                          'urine', 'blankle', 'feet', 'hand', 'body', 'weight', 'lose', 'diet',
                          'eat', 'drink', 'fruit', 'vegetable', 'protein', 'exercise', 'walk']
        
        title_lower = title.lower()
        if any(kw in title_lower for kw in health_keywords) and len(title) > 15:
            videos.append({
                'video_id': video_id,
                'title': title,
                'views': views,
                'published': published,
                'url': f'https://www.youtube.com/watch?v={video_id}',
                'channel': channel_name
            })
    
    return videos

# Process the saved HTML files
import os

html_files = {
    'Claire Whitmore': '/tmp/ddg_claire.html',  # This is DDG, not YouTube
}

# We need to re-fetch and save YouTube HTML
def fetch_and_save(url, filename):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode('utf-8', errors='replace')
        with open(filename, 'w') as f:
            f.write(html)
        return html
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

print("Fetching YouTube search results for detailed extraction...")
print("=" * 60)

all_detailed_videos = {}

# Define detailed searches
detailed_searches = {
    'Claire Whitmore': 'https://www.youtube.com/results?search_query=%22Claire+Whitmore%22+senior+health&sp=CAI%253D',
    'Dr. Waterling': 'https://www.youtube.com/results?search_query=%22Dr.+Waterling%22+stroke+seniors&sp=CAI%253D',
    'Dr. Michael Kent': 'https://www.youtube.com/results?search_query=%22Dr.+Michael+Kent%22+senior+health&sp=CAI%253D',
    'Doctor Becker': 'https://www.youtube.com/results?search_query=%22Doctor+Becker%22+stem+cell+microplastics+seniors&sp=CAI%253D',
    'Dr. Franklin': 'https://www.youtube.com/results?search_query=%22Dr.+Franklin%22+senior+health+nail&sp=CAI%253D',
    'Dr. Adewale': 'https://www.youtube.com/results?search_query=%22Dr.+Adewale%22+blood+pressure+kitchen+seniors&sp=CAI%253D',
    'Senior Health Blog': 'https://www.youtube.com/results?search_query=%22Senior+Health+Blog%22+diabetes+breakfast&sp=CAI%253D',
    'Dr. James Cross': 'https://www.youtube.com/results?search_query=%22Dr.+James+Cross%22+leg+swollen+ankles&sp=CAI%253D',
    'New Competitors': 'https://www.youtube.com/results?search_query=elder+health+seniors+60+new+video+2026&sp=CAISAhAB',
}

for name, url in detailed_searches.items():
    safe_name = name.replace(' ', '_').replace('.', '')
    filename = f'/tmp/yt_{safe_name}.html'
    
    print(f"\n[{name}]")
    html = fetch_and_save(url, filename)
    
    if html:
        videos = extract_video_details(html, name)
        print(f"  Found {len(videos)} structured videos")
        for v in videos[:8]:
            print(f"    - {v['title'][:70]}")
            print(f"      Views: {v['views']} | Published: {v['published']}")
            print(f"      URL: {v['url']}")
        
        all_detailed_videos[name] = videos
    else:
        all_detailed_videos[name] = []

# Save detailed results
with open('/tmp/detailed_videos.json', 'w') as f:
    json.dump(all_detailed_videos, f, indent=2, default=str)

print(f"\n\nAll detailed video data saved to /tmp/detailed_videos.json")
print(f"Total videos found: {sum(len(v) for v in all_detailed_videos.values())}")
