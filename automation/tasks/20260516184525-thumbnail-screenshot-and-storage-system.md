---
id: 20260516184525-thumbnail-screenshot-and-storage-system
created_at: "2026-05-16 18:45:25"
owner_agent: thumbnail-analyst
priority: high
status: open
---

# Thumbnail Screenshot and Storage System

## Source Files

  - data/thumbnails/thumbnail_memory_template.csv
  - schemas/thumbnail_record.schema.json

## Expected Output

A Python script at scripts/capture_thumbnails.py that takes a CSV of video URLs and downloads the maxresdefault thumbnail image for each video. Uses the YouTube thumbnail URL pattern: https://img.youtube.com/vi/{video_id}/maxresdefault.jpg (falls back to hqdefault.jpg if maxres unavailable). Saves images to data/thumbnails/competitor/ with naming {date}_{channel}_{video_id}.jpg. Produces/updates a CSV at data/thumbnails/competitor_thumbnails_log.csv with columns: date_found, channel, video_id, video_url, thumbnail_path, file_size_bytes, download_status. Optionally uses yt-dlp --write-thumbnail as a fallback for age-restricted videos. No API key needed.

## Done Criteria

Script downloads thumbnails for at least 5 competitor videos, saves images to disk, produces a valid CSV log, and handles missing thumbnails gracefully (falls back to hqdefault, marks failures in log).

## Notes

This is the simplest subsystem - pure HTTP downloads, no API quota used. The real value is building the visual swipe file for thumbnail-analyst to review. Later, thumbnail-analyst can manually or semi-automatically tag these with the thumbnail_memory_template.csv fields (layout, colors, text, doctor_position, prop).
