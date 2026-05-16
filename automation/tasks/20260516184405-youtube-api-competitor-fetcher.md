---
id: 20260516184405-youtube-api-competitor-fetcher
created_at: "2026-05-16 18:44:05"
owner_agent: competitor-watcher
priority: urgent
status: open
---

# YouTube API Competitor Fetcher

## Source Files

  - schemas/competitor_daily_snapshot.schema.json
  - memory/competitor_watchlist.csv
  - data/competitors/daily/competitor_daily_template.csv

## Expected Output

A Python script at scripts/fetch_competitor_videos.py that uses the YouTube Data API v3 to fetch latest videos from all channels in competitor_watchlist.csv. For each video it captures: title, URL, published date, view count, like count, comment count, duration, description, and tags. Output is a dated CSV in data/competitors/daily/ matching the competitor_daily_snapshot schema. Script reads YOUTUBE_API_KEY from ~/.hermes/.env. Supports multiple API keys with automatic fallback. Includes rate-limit handling with exponential backoff.

## Done Criteria

Script runs without errors, produces a valid dated CSV for the current day, handles missing/empty channels gracefully, and validates output against the schema.

## Notes

Use google-api-python-client or direct REST calls via requests. YouTube Data API quota is 10,000 units/day. Search:list costs 100 units, videos:list costs 1 unit. With 12 competitors and daily runs, budget ~500 units/day minimum. Fetch only videos published in the last 7 days to stay within quota. Use publishedAfter parameter with RFC 3339 timestamp.
