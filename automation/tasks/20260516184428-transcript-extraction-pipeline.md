---
id: 20260516184428-transcript-extraction-pipeline
created_at: "2026-05-16 18:44:28"
owner_agent: competitor-watcher
priority: high
status: open
---

# Transcript Extraction Pipeline

## Source Files

  - schemas/competitor_daily_snapshot.schema.json
  - knowledge/raw_initial_upload/youtube_transcripts_text_format.txt

## Expected Output

A Python script at scripts/extract_transcripts.py that takes a CSV of video URLs (from fetch_competitor_videos.py output) and extracts transcripts using youtube-transcript-api (or yt-dlp as fallback). For each video, saves a .txt file under data/competitors/transcripts/ with naming pattern {date}_{channel}_{video_id}.txt. Also produces a summary CSV with columns: video_url, transcript_status (found/not_found/auto_generated), word_count, first_100_chars, key_hook_summary. Handles age-restricted, private, and unavailable videos gracefully. No API key needed for transcript extraction.

## Done Criteria

Script successfully extracts transcripts from at least 3 competitor videos, saves .txt files, produces summary CSV, and handles a video with no transcript without crashing.

## Notes

youtube-transcript-api is the primary method (pip install youtube-transcript-api). yt-dlp is the fallback (already likely installed). Do NOT store full transcripts in the daily CSV - only summaries and file paths. Full transcripts go to data/competitors/transcripts/. This keeps the daily CSV lightweight.
