---
id: 20260516184602-trend-scoring-formula-engine
created_at: "2026-05-16 18:46:02"
owner_agent: pattern-analyst
priority: high
status: open
---

# Trend Scoring Formula Engine

## Source Files

  - memory/competitor_memory.md
  - memory/winning_patterns.md
  - memory/video_idea_bank.csv

## Expected Output

A Python module at scripts/trend_scorer.py that implements a deterministic scoring formula for video ideas based on competitor signals. The formula scores each idea on a 0-20 scale using these weighted signals: view_velocity_score (0-5) based on views/day of similar competitor videos, title_formula_match (0-3) based on overlap with known winning title patterns, thumbnail_gap_score (0-3) based on how underserved the visual angle is, comment_demand_score (0-3) based on comment volume and question frequency, pillar_priority (0-2) based on channel's current strategic pillar weights, freshness_score (0-2) based on how recently the topic trended, and competition_saturation_penalty (-2 to 0) based on how many competitors already covered it. Outputs a scored CSV with columns: idea_title, total_score, signal_breakdown_json, recommendation (green/yellow/red). Includes unit tests in tests/test_trend_scorer.py.

## Done Criteria

Module runs without errors, scores a sample set of 10 ideas, produces correct CSV output, unit tests pass. Scoring is deterministic - same input always produces same output.

## Notes

This replaces the current manual 15/20 scoring with a data-driven formula. The weights should be configurable via a YAML config at config/scoring_weights.yaml so the user can tune without editing code. The formula should be explainable - every score must have a clear signal reason. This is the brain that makes the daily competitor scan actionable.
