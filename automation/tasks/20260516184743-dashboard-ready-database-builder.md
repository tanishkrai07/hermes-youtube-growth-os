---
id: 20260516184743-dashboard-ready-database-builder
created_at: "2026-05-16 18:47:43"
owner_agent: analytics-doctor
priority: medium
status: open
---

# Dashboard-Ready Database Builder

## Source Files

  - schemas/competitor_daily_snapshot.schema.json
  - schemas/channel_analytics_snapshot.schema.json
  - schemas/video_pipeline.schema.json
  - schemas/thumbnail_record.schema.json

## Expected Output

A Python script at scripts/build_dashboard_db.py that creates and maintains a SQLite database at data/hermes_dashboard.db with normalized tables: competitor_videos (all-time competitor video data), competitor_daily_snapshots (daily metrics per video), channel_videos (our channel's videos), channel_daily_metrics (daily analytics per video), video_ideas (scored ideas from trend_scorer), idea_outcomes (tracking which ideas were produced and their performance), thumbnail_records (thumbnail metadata and file paths), daily_reports (report metadata and key metrics). Includes schema creation, data import from CSV files, incremental update logic (upsert, not duplicate), and a views layer for common queries: v_top_ideas, v_competitor_trends, v_channel_performance, v_thumbnail_win_rate. Also includes scripts/query_dashboard.py with CLI commands for common lookups.

## Done Criteria

Script creates the database, imports existing CSV data without duplicates, supports incremental updates (running twice produces same result), and the views return correct results for sample queries. Database file is created at data/hermes_dashboard.db.

## Notes

SQLite is chosen for zero-config setup - no server needed, single file, works on EC2. When the user is ready for Appsmith/NocoBase, this SQLite DB can be migrated to PostgreSQL. The key design principle: every CSV the system produces also gets loaded into this DB, so there is always a queryable, historical record. This turns flat files into a real analytics database.
