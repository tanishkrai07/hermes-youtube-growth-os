---
id: 20260516184502-comment-extraction-pipeline
created_at: "2026-05-16 18:45:02"
owner_agent: competitor-watcher
priority: high
status: open
---

# Comment Extraction Pipeline

## Source Files

  - schemas/competitor_daily_snapshot.schema.json
  - data/competitors/daily/competitor_daily_template.csv

## Expected Output

A Python script at scripts/extract_comments.py that uses YouTube Data API v3 commentThreads.list to fetch top-level comments for each video in the daily competitor CSV. Captures: comment text, like count, reply count, published date. Saves up to 100 top comments per video as a .json file under data/competitors/comments/ with naming {date}_{video_id}_comments.json. Produces a summary CSV with columns: video_url, total_comments_fetched, top_themes (extracted via simple keyword clustering), sentiment_hint (positive/negative/mixed based on like ratio), most_liked_comment_snippet. Reads YOUTUBE_API_KEY from ~/.hermes/.env with multi-key fallback.

## Done Criteria

Script fetches comments for at least 2 competitor videos, saves .json files, produces summary CSV with theme extraction, and handles disabled comments and API quota exhaustion gracefully.

## Notes

commentThreads.list costs 1 unit per call, returns up to 100 comments per call. With 12 competitors x ~3 new videos x 100 comments = ~36 API calls = 36 units. Very quota-friendly. For theme extraction, use simple keyword frequency (no LLM needed) - count occurrences of health-related terms from the channel's 8 pillars. Sort by like count to surface top comments first.
