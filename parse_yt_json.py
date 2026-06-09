#!/usr/bin/env python3
"""Parse ytInitialData JSON from YouTube HTML to extract video details."""
import re
import json

def parse_yt_data(html, channel_name):
    """Parse YouTube's embedded JSON data."""
    videos = []
    
    # Find the ytInitialData JSON blob
    match = re.search(r'var ytInitialData = (\{.*?\});', html, re.DOTALL)
    if not match:
        return videos
    
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        # Try to extract with a more lenient approach
        return videos
    
    # Navigate to video contents
    try:
        contents = (data.get('contents', {})
                    .get('twoColumnSearchResultsRenderer', {})
                    .get('primaryContents', {})
                    .get('sectionListRenderer', {})
                    .get('contents', []))
        
        for section in contents:
            item_section = section.get('itemSectionRenderer', {})
            items = item_section.get('contents', [])
            
            for item in items:
                video_renderer = item.get('videoRenderer')
                if not video_renderer:
                    continue
                
                video_id = video_renderer.get('videoId', '')
                title_runs = video_renderer.get('title', {}).get('runs', [])
                title = ''.join(r.get('text', '') for r in title_runs)
                
                # View count
                view_count_text = ''
                view_obj = video_renderer.get('viewCountText', {})
                if 'simpleText' in view_obj:
                    view_count_text = view_obj['simpleText']
                elif 'runs' in view_obj:
                    view_count_text = ''.join(r.get('text', '') for r in view_obj['runs'])
                
                # Published time
                published_text = ''
                pub_obj = video_renderer.get('publishedTimeText', {})
                if 'simpleText' in pub_obj:
                    published_text = pub_obj['simpleText']
                
                # Thumbnail for length estimate
                length_text = ''
                length_obj = video_renderer.get('lengthText', {})
                if 'simpleText' in length_obj:
                    length_text = length_obj['simpleText']
                
                if title and video_id:
                    videos.append({
                        'video_id': video_id,
                        'title': title,
                        'views': view_count_text,
                        'published': published_text,
                        'length': length_text,
                        'url': f'https://www.youtube.com/watch?v={video_id}',
                        'channel': channel_name
                    })
    except (KeyError, TypeError, AttributeError):
        pass
    
    return videos

# Process saved HTML files
html_files = {
    'Claire Whitmore': '/tmp/yt_Claire_Whitmore.html',
    'Dr. Waterling': '/tmp/yt_Dr_Waterling.html',
    'Dr. Michael Kent': '/tmp/yt_Dr_Michael_Kent.html',
    'Dr. Franklin': '/tmp/yt_Dr_Franklin.html',
    'Dr. Adewale': '/tmp/yt_Dr_Adewale.html',
    'Senior Health Blog': '/tmp/yt_Senior_Health_Blog.html',
    'Dr. James Cross': '/tmp/yt_Dr_James_Cross.html',
}

all_videos = {}

for name, filepath in html_files.items():
    print(f"\n{'='*60}")
    print(f"[{name}]")
    
    try:
        with open(filepath) as f:
            html = f.read()
    except FileNotFoundError:
        print(f"  FILE NOT FOUND: {filepath}")
        continue
    
    videos = parse_yt_data(html, name)
    print(f"  Found {len(videos)} videos with structured data")
    
    for v in videos[:10]:
        print(f"    - {v['title'][:75]}")
        print(f"      Views: {v['views']} | Published: {v['published']} | Length: {v['length']}")
    
    all_videos[name] = videos

# Save
with open('/tmp/yt_parsed.json', 'w') as f:
    json.dump(all_videos, f, indent=2, default=str)

total = sum(len(v) for v in all_videos.values())
print(f"\n\nTotal videos parsed: {total}")
print("Saved to /tmp/yt_parsed.json")

# Also try Doctor Becker with a different search
print(f"\n{'='*60}")
print("[Doctor Becker - retry with different search]")
becker_files = ['/tmp/yt_Doctor_Becker.html']
for fp in becker_files:
    try:
        with open(fp) as f:
            html = f.read()
        videos = parse_yt_data(html, 'Doctor Becker')
        print(f"  Found {len(videos)} videos")
        for v in videos[:10]:
            print(f"    - {v['title'][:75]}")
            print(f"      Views: {v['views']} | Published: {v['published']}")
        all_videos['Doctor Becker'] = videos
    except FileNotFoundError:
        print(f"  FILE NOT FOUND: {fp}")
