---
id: 20260516200000-missing-subsystems-implementation-plan
created_at: "2026-05-16 20:00:00"
owner_agent: hermes-master
priority: urgent
status: open
---

# Missing Production Subsystems — Implementation Plan

## Purpose

This is the master plan that unifies all 7 missing subsystem tasks into a single
build sequence. It defines the architecture, dependencies, data flow, shared
conventions, and build order. Individual task files exist for each subsystem;
this document is the orchestration layer that ensures they work together.

---

## Architecture Overview

```
[YouTube API v3]                          [No API key needed]
      |                                          |
      v                                          v
fetch_competitor_videos.py            capture_thumbnails.py
      |                                          |
      v                                          v
[dated CSV in                            [JPGs in data/thumbnails/
 data/competitors/daily/]                 competitor/]
      |                                          |
      +------------------+                       |
      |                  |                       |
      v                  v                       |
extract_transcripts.py  extract_comments.py     |
      |                  |                       |
      v                  v                       |
[transcripts/        [comments/                 |
 {date}_{video_id}    {date}_{video_id}         |
  _comments.json]      _comments.json]          |
      |                  |                       |
      +------------------+                       |
                         |                       |
                         v                       v
                  trend_scorer.py <--- thumbnail metadata
                         |
                         v
                  [scored ideas CSV]
                         |
                         v
                  generate_daily_report.py
                         |
                         v
                  [report .md + telegram .txt]
                         |
                         v
                  build_dashboard_db.py
                         |
                         v
                  [data/hermes_dashboard.db]
```

---

## Build Order (Dependencies)

Phase 1 — Data Collection (no internal dependencies, can build in parallel)
  1. fetch_competitor_videos.py (Task: 20260516184405)
  2. capture_thumbnails.py (Task: 20260516184525)

Phase 2 — Enrichment (depends on Phase 1 output)
  3. extract_transcripts.py (Task: 20260516184428) — needs video URLs from #1
  4. extract_comments.py (Task: 20260516184502) — needs video URLs from #1

Phase 3 — Analysis (depends on Phase 1 + Phase 2 output)
  5. trend_scorer.py (Task: 20260516184602) — needs CSVs from #1, #3, #4

Phase 4 — Reporting (depends on Phase 3)
  6. generate_daily_report.py (Task: 20260516184631) — assembles all CSVs

Phase 5 — Persistence (depends on all previous)
  7. build_dashboard_db.py (Task: 20260516184743) — loads all CSVs into SQLite

---

## Shared Conventions (ALL scripts must follow)

### Environment & Config
- All scripts read environment from ~/.hermes/.env (sourced via python-dotenv).
- YOUTUBE_API_KEY: supports comma-separated list for automatic fallback.
  Script tries next key on 403/quota-exhausted errors.
- REPO_ROOT: auto-detected as the parent of the scripts/ directory.
- All scripts accept an optional --repo-root CLI arg to override.

### Output Directory Convention
- All dated outputs go under data/ with the pattern:
  data/{subsystem}/{daily|weekly|transcripts|comments|thumbnails}/YYYY-MM-DD_{name}.{ext}
- All scripts create directories if they don't exist (mkdir -p behavior).

### Date Convention
- All dates in ISO 8601 format: YYYY-MM-DD.
- All timestamps in ISO 8601 with timezone: YYYY-MM-DDTHH:MM:SS+05:30 (Asia/Kolkata).
- publishedAfter for YouTube API: RFC 3339, e.g. 2026-05-09T00:00:00Z.

### Error Handling
- Every script logs to stderr, outputs data to stdout or files.
- Exit code 0 = success, 1 = partial success (some items failed), 2 = total failure.
- No script crashes on a single video/channel failure. It logs and continues.
- Every script has a --dry-run mode that prints what it would do without API calls.

### Logging Format
- Standard prefix: [LEVEL] YYYY-MM-DD HH:MM:SS message
- Levels: INFO, WARN, ERROR
- Example: [INFO] 2026-05-16 08:00:00 Fetching videos for @DrMichaelKent

### CSV Convention
- All CSVs use UTF-8 encoding, comma-separated, with header row.
- All CSVs match their corresponding schema in schemas/*.json.
- No BOM (byte order mark). No trailing commas.

### Rate Limiting
- YouTube API: exponential backoff starting at 2s, max 60s, 5 retries.
- Between API calls: 0.5s sleep to avoid burst limits.
- Track quota usage in a local file: data/youtube_api_quota_log.json.

---

## Subsystem Specifications

### 1. YouTube API Competitor Fetcher
Task file: 20260516184405-youtube-api-competitor-fetcher.md

Script: scripts/fetch_competitor_videos.py

Input: memory/competitor_watchlist.csv
Output: data/competitors/daily/YYYY-MM-DD_competitors.csv

Key design:
  - Reads channel URLs from watchlist, extracts channel IDs or custom handles.
  - For each channel, calls search:list with publishedAfter (last 7 days) and channelId.
  - For each result, calls videos:list to get full metadata.
  - Captures: title, video_id, url, published_at, view_count, like_count,
    comment_count, duration, description, tags.
  - Quota budget: ~500 units/day (12 channels x ~40 units each).
  - Supports --days-back flag (default 7, max 30).
  - Supports --channel flag to scan a single channel.

Schema match: schemas/competitor_daily_snapshot.schema.json

### 2. Transcript Extraction Pipeline
Task file: 20260516184428-transcript-extraction-pipeline.md

Script: scripts/extract_transcripts.py

Input: data/competitors/daily/YYYY-MM-DD_competitors.csv (video URLs)
Output:
  - data/competitors/transcripts/YYYY-MM-DD_{channel}_{video_id}.txt
  - data/competitors/transcripts/YYYY-MM-DD_transcript_summaries.csv

Key design:
  - Primary: youtube-transcript-api (pip install youtube-transcript-api).
  - Fallback: yt-dlp --write-auto-sub --sub-lang en --skip-download.
  - For each video: try manual captions first, then auto-generated.
  - Summary CSV columns: video_url, transcript_status, word_count,
    first_100_chars, key_hook_summary (first sentence of transcript).
  - No API key needed. No quota cost.
  - Handles: age-restricted (try yt-dlp), private (skip), unavailable (skip).

### 3. Comment Extraction Pipeline
Task file: 20260516184502-comment-extraction-pipeline.md

Script: scripts/extract_comments.py

Input: data/competitors/daily/YYYY-MM-DD_competitors.csv
Output:
  - data/competitors/comments/YYYY-MM-DD_{video_id}_comments.json
  - data/competitors/comments/YYYY-MM-DD_comment_summaries.csv

Key design:
  - Uses YouTube Data API v3 commentThreads.list.
  - Fetches top 100 comments per video, sorted by relevance.
  - Captures: comment_text, like_count, reply_count, published_date, author.
  - Theme extraction: keyword frequency count across 8 pillar terms.
  - Sentiment hint: ratio of likes to total comments (positive if >70% liked).
  - Quota cost: ~1 unit per video. Very budget-friendly.
  - Handles: disabled comments (skip), quota exhaustion (rotate key, resume).

### 4. Thumbnail Screenshot and Storage
Task file: 20260516184525-thumbnail-screenshot-and-storage-system.md

Script: scripts/capture_thumbnails.py

Input: data/competitors/daily/YYYY-MM-DD_competitors.csv
Output:
  - data/thumbnails/competitor/YYYY-MM-DD_{channel}_{video_id}.jpg
  - data/thumbnails/competitor_thumbnails_log.csv

Key design:
  - Pure HTTP downloads. No API quota used.
  - URL pattern: https://img.youtube.com/vi/{video_id}/maxresdefault.jpg
  - Fallback: hqdefault.jpg if maxres returns 404.
  - Optional: yt-dlp --write-thumbnail for age-restricted videos.
  - Log CSV: date_found, channel, video_id, video_url, thumbnail_path,
    file_size_bytes, download_status.
  - Later: thumbnail-analyst tags these with layout/color/text metadata.

### 5. Trend Scoring Formula Engine
Task file: 20260516184602-trend-scoring-formula-engine.md

Script: scripts/trend_scorer.py (+ config/scoring_weights.yaml)

Input:
  - data/competitors/daily/YYYY-MM-DD_competitors.csv
  - data/competitors/comments/YYYY-MM-DD_comment_summaries.csv
  - memory/video_idea_bank.csv
  - memory/winning_patterns.md (parsed for title formula matching)

Output: data/competitors/daily/YYYY-MM-DD_scored_ideas.csv

Scoring formula (0-20 scale):
  - view_velocity_score (0-5): views/day of similar competitor videos.
    0 = 0 views/day, 5 = 500+ views/day (log scale).
  - title_formula_match (0-3): overlap with winning title patterns.
    3 = matches 2+ patterns, 1 = matches 1, 0 = none.
  - thumbnail_gap_score (0-3): underserved visual angle.
    3 = no competitor used this visual, 1 = some, 0 = saturated.
  - comment_demand_score (0-3): comment volume + question frequency.
    3 = 50+ comments with question marks, 0 = <5 comments.
  - pillar_priority (0-2): current strategic pillar weight.
    2 = top-3 priority pillar, 1 = mid, 0 = low priority.
  - freshness_score (0-2): recency of topic trend.
    2 = trending in last 48h, 1 = last week, 0 = older.
  - competition_saturation_penalty (-2 to 0): how many competitors covered it.
    0 = 0-1 competitors, -1 = 2-4, -2 = 5+.

  Total = sum of above. Green = 15+, Yellow = 10-14, Red = <10.

Config file: config/scoring_weights.yaml
  - Each signal has a weight multiplier (default 1.0).
  - User can tune without editing code.

Unit tests: tests/test_trend_scorer.py
  - Test each scoring component independently.
  - Test full scoring with known input/output.
  - Test edge cases: zero views, no comments, all patterns match.

### 6. Daily Report Generator
Task file: 20260516184631-daily-report-generator.md

Script: scripts/generate_daily_report.py

Input:
  - data/competitors/daily/YYYY-MM-DD_competitors.csv
  - data/competitors/transcripts/YYYY-MM-DD_transcript_summaries.csv
  - data/competitors/comments/YYYY-MM-DD_comment_summaries.csv
  - data/competitors/daily/YYYY-MM-DD_scored_ideas.csv

Output:
  - outputs/reports/YYYY-MM-DD_daily_competitor_intelligence.md
  - outputs/reports/YYYY-MM-DD_telegram_summary.txt

Report sections:
  1. Executive Summary (3-4 sentences, populated by AI agent)
  2. New Uploads Table (channel, title, views, pillar, hook)
  3. Top 3 Trending Topics (from comment themes + view velocity)
  4. Top 10 Scored Ideas (with score breakdown)
  5. Thumbnail Patterns Observed (from thumbnail log)
  6. Comment Pain Points & Questions (from comment summaries)
  7. Recommended Actions for Tomorrow
  8. Memory Update Proposals

Telegram summary: under 4000 chars, condensed version of the report.
Missing input files: section shows "No data today" instead of crashing.

### 7. Dashboard-Ready Database Builder
Task file: 20260516184743-dashboard-ready-database-builder.md

Script: scripts/build_dashboard_db.py + scripts/query_dashboard.py

Input: All CSV files produced by subsystems 1-6.
Output: data/hermes_dashboard.db

Tables:
  - competitor_videos: all-time competitor video data.
  - competitor_daily_snapshots: daily metrics per video.
  - channel_videos: our channel's videos.
  - channel_daily_metrics: daily analytics per video.
  - video_ideas: scored ideas from trend_scorer.
  - idea_outcomes: tracking which ideas were produced and performance.
  - thumbnail_records: thumbnail metadata and file paths.
  - daily_reports: report metadata and key metrics.

Views:
  - v_top_ideas: top 20 ideas by score, not yet produced.
  - v_competitor_trends: views/day by pillar, last 30 days.
  - v_channel_performance: our videos ranked by views and CTR.
  - v_thumbnail_win_rate: thumbnail patterns by performance tier.

Key design:
  - SQLite (zero-config, single file, no server).
  - Upsert logic: running twice produces no duplicates.
  - Incremental: only processes new/changed CSV rows.
  - query_dashboard.py: CLI for common lookups (top ideas, trends, etc.).
  - Future migration path: SQLite -> PostgreSQL for Appsmith/NocoBase.

---

## Integration Points with Existing Systems

### Cron Jobs (already created)
- Daily competitor scan (8am IST) runs: fetch -> transcripts -> comments ->
  thumbnails -> score -> report -> dashboard -> Telegram.
- Weekly strategy review (Sunday 9am IST) reads from dashboard DB.

### Memory System
- Each daily run proposes updates to:
  - memory/competitor_memory.md (new patterns observed)
  - memory/winning_patterns.md (validated patterns)
  - memory/failed_patterns.md (if any)
  - memory/video_idea_bank.csv (new scored ideas)
- Proposals are reviewed by memory-curator before commit.

### Validation
- After each build phase, run: python3 scripts/hermes_auto_update.py validate
- Schema validation: CSV headers match schemas/*.json.
- Data validation: no duplicate rows, no null required fields.

### Telegram Delivery
- Report generator produces YYYY-MM-DD_telegram_summary.txt.
- Cron job reads this file and sends via Telegram bot.
- Note: Current Telegram token is INVALID (from memory). Must be refreshed
  from @BotFather before delivery works.

---

## Testing Strategy

Each subsystem must pass these tests before being marked complete:

1. Unit tests: tests/test_{subsystem}.py with >= 90% coverage of core logic.
2. Integration test: run the full pipeline with --dry-run on sample data.
3. End-to-end test: run against 2-3 real competitor channels, verify output.
4. Error handling test: simulate API failure, missing data, quota exhaustion.
5. Idempotency test: running twice produces same output (no duplicates).

---

## File Inventory (to be created)

New files this plan requires:
  - scripts/fetch_competitor_videos.py
  - scripts/extract_transcripts.py
  - scripts/extract_comments.py
  - scripts/capture_thumbnails.py
  - scripts/trend_scorer.py
  - scripts/generate_daily_report.py
  - scripts/build_dashboard_db.py
  - scripts/query_dashboard.py
  - config/scoring_weights.yaml
  - tests/test_trend_scorer.py
  - tests/test_fetch_competitor_videos.py
  - tests/test_extract_transcripts.py
  - tests/test_extract_comments.py
  - tests/test_capture_thumbnails.py
  - tests/test_generate_daily_report.py
  - tests/test_build_dashboard_db.py
  - data/competitors/transcripts/.gitkeep
  - data/competitors/comments/.gitkeep
  - data/thumbnails/competitor/.gitkeep

Existing files that are inputs (do not modify):
  - memory/competitor_watchlist.csv
  - memory/winning_patterns.md
  - memory/competitor_memory.md
  - memory/video_idea_bank.csv
  - schemas/competitor_daily_snapshot.schema.json
  - schemas/thumbnail_record.schema.json
  - schemas/channel_analytics_snapshot.schema.json
  - schemas/video_pipeline.schema.json
  - scripts/hermes_auto_update.py

---

## Risk Register

1. YouTube API quota exhaustion: Mitigated by multi-key fallback, 7-day window,
   and quota logging. Worst case: scan fewer channels per day.
2. Transcript API blocking: Mitigated by yt-dlp fallback. Worst case: skip
   transcripts for that run.
3. Thumbnail URL changes: Mitigated by fallback from maxres to hqdefault.
   Worst case: log failure, continue.
4. Telegram token invalid: Already known. Must get new token from @BotFather.
   Workaround: save reports locally until token is fixed.
5. Channel URL format changes: Watchlist uses full URLs. If YouTube changes URL
   format, the channel ID extraction regex must be updated.

---

## Success Criteria (All 7 Subsystems Complete)

- [ ] All 8 scripts exist and run without errors.
- [ ] All 7 test files exist and pass.
- [ ] Full pipeline runs end-to-end: fetch -> enrich -> score -> report -> db.
- [ ] Dashboard DB is queryable and returns correct results.
- [ ] Telegram summary is generated (delivery pending valid bot token).
- [ ] Repo passes validation: python3 scripts/hermes_auto_update.py validate.
- [ ] All new files are committed to git.
