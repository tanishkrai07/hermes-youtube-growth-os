---
id: 20260516184631-daily-report-generator
created_at: "2026-05-16 18:46:31"
owner_agent: hermes-master
priority: medium
status: open
---

# Daily Report Generator

## Source Files

  - outputs/reports/.gitkeep
  - schemas/competitor_daily_snapshot.schema.json
  - prompts/daily_competitor_review.md

## Expected Output

A Python script at scripts/generate_daily_report.py that assembles a structured daily intelligence report from the day's data. Inputs: dated competitor CSV (from fetch_competitor_videos.py), transcript summaries (from extract_transcripts.py), comment summaries (from extract_comments.py), scored ideas (from trend_scorer.py). Output: a markdown report at outputs/reports/YYYY-MM-DD_daily_competitor_intelligence.md with sections: Executive Summary (3-4 sentences), New Uploads Table (channel, title, views, pillar, hook), Top 3 Trending Topics, Top 10 Scored Ideas (with score breakdown), Thumbnail Patterns Observed, Comment Pain Points & Questions, Recommended Actions for Tomorrow, Memory Update Proposals. Also generates a condensed Telegram-friendly summary (under 4000 chars) at outputs/reports/YYYY-MM-DD_telegram_summary.txt.

## Done Criteria

Script generates a valid markdown report and Telegram summary from sample data. Report has all 8 sections populated. Telegram summary is under 4000 characters. Script handles missing input files gracefully (marks sections as 'no data today' instead of crashing).

## Notes

This is the assembly layer - it does NOT do AI analysis itself. It structures the data collected by the other 4 subsystems into a report format. The AI agent (competitor-watcher) then reads this report to add qualitative insights, adjust scores, and write the executive summary. Think of this as the 'data -> structured report' pipeline, with the agent adding the 'so what' layer on top.
