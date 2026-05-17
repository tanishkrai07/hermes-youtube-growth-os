#!/usr/bin/env python3
"""
Hermes YouTube Growth OS — Daily Report Generator
Generates a daily competitor intelligence report from all pipeline outputs.

Usage:
    python3 scripts/generate_daily_report.py [--date YYYY-MM-DD] [--dry-run]

Input:
    data/competitors/daily/YYYY-MM-DD_competitors.csv
    data/competitors/transcripts/YYYY-MM-DD_transcript_summaries.csv (optional)
    data/competitors/comments/YYYY-MM-DD_comment_summaries.csv (optional)
    data/competitors/daily/YYYY-MM-DD_scored_ideas.csv (optional)

Output:
    outputs/reports/YYYY-MM-DD_daily_competitor_intelligence.md
    outputs/reports/YYYY-MM-DD_telegram_summary.txt
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = REPO_ROOT / "data" / "competitors" / "daily"
TRANSCRIPTS_DIR = REPO_ROOT / "data" / "competitors" / "transcripts"
COMMENTS_DIR = REPO_ROOT / "data" / "competitors" / "comments"
REPORTS_DIR = REPO_ROOT / "outputs" / "reports"


def log(level, message):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{level}] {ts} {message}", flush=True)


def read_csv_safe(path):
    """Read CSV file, return list of dicts. Returns empty list if file doesn't exist."""
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def generate_markdown_report(date_str, competitors, transcripts, comments, scored_ideas):
    """Generate the full markdown report."""
    lines = []
    lines.append(f"# Daily Competitor Intelligence Report — {date_str}")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Videos tracked:** {len(competitors)}")
    lines.append(f"**Ideas scored:** {len(scored_ideas)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 1: Executive Summary
    lines.append("## 1. Executive Summary")
    lines.append("")
    if scored_ideas:
        top_ideas = sorted(scored_ideas, key=lambda x: float(x.get("total_score", 0)), reverse=True)[:3]
        green_count = sum(1 for s in scored_ideas if s.get("priority") == "GREEN")
        lines.append(f"Today's scan identified {len(competitors)} competitor videos across "
                      f"{len(set(v.get('channel', '') for v in competitors))} channels. "
                      f"{len(scored_ideas)} ideas were scored, with {green_count} rated GREEN (15+). "
                      f"Top opportunity: \"{top_ideas[0].get('title_suggestion', 'N/A')}\" "
                      f"(Score: {top_ideas[0].get('total_score', 'N/A')}).")
    else:
        lines.append("No competitor data available for today.")
    lines.append("")

    # Section 2: New Uploads Table
    lines.append("## 2. New Competitor Uploads")
    lines.append("")
    if competitors:
        lines.append("| # | Channel | Title | Pillar | Views | Signal |")
        lines.append("|---|---------|-------|--------|-------|--------|")
        for i, v in enumerate(competitors[:20], 1):
            title = v.get("video_title", "")[:50]
            views = v.get("views", "N/A")
            signal = v.get("idea_signal", "")[:30]
            lines.append(f"| {i} | {v.get('channel', '')} | {title} | {v.get('pillar', '')} | {views} | {signal} |")
    else:
        lines.append("_No data today._")
    lines.append("")

    # Section 3: Top Trending Topics
    lines.append("## 3. Top Trending Topics")
    lines.append("")
    if scored_ideas:
        # Group by pillar
        pillars = {}
        for idea in scored_ideas:
            p = idea.get("pillar", "Unknown")
            if p not in pillars:
                pillars[p] = []
            pillars[p].append(idea)

        # Sort pillars by average score
        pillar_avg = []
        for p, ideas in pillars.items():
            avg = sum(float(i.get("total_score", 0)) for i in ideas) / len(ideas)
            pillar_avg.append((p, avg, len(ideas)))
        pillar_avg.sort(key=lambda x: x[1], reverse=True)

        for p, avg, count in pillar_avg[:5]:
            lines.append(f"- **{p}** — {count} videos, avg score {avg:.1f}")
    else:
        lines.append("_No data today._")
    lines.append("")

    # Section 4: Top 10 Scored Ideas
    lines.append("## 4. Top 10 Scored Ideas")
    lines.append("")
    if scored_ideas:
        sorted_ideas = sorted(scored_ideas, key=lambda x: float(x.get("total_score", 0)), reverse=True)
        lines.append("| # | Idea | Pillar | Score | Priority |")
        lines.append("|---|------|--------|-------|----------|")
        for i, idea in enumerate(sorted_ideas[:10], 1):
            title = idea.get("title_suggestion", "")[:45]
            lines.append(f"| {i} | {title} | {idea.get('pillar', '')} | {idea.get('total_score', '')} | {idea.get('priority', '')} |")
    else:
        lines.append("_No data today._")
    lines.append("")

    # Section 5: Transcript Insights
    lines.append("## 5. Transcript Insights")
    lines.append("")
    if transcripts:
        successful = [t for t in transcripts if "ok" in t.get("transcript_status", "")]
        lines.append(f"Transcripts extracted: {len(successful)}/{len(transcripts)} successful.")
        for t in successful[:5]:
            hook = t.get("key_hook_summary", "")[:80]
            lines.append(f"- **{t.get('channel', '')}**: \"{hook}...\"")
    else:
        lines.append("_No transcript data today. Run extract_transcripts.py to enable._")
    lines.append("")

    # Section 6: Comment Pain Points
    lines.append("## 6. Comment Pain Points & Questions")
    lines.append("")
    if comments:
        for c in comments[:5]:
            themes = c.get("comment_themes", "")[:100]
            if themes:
                lines.append(f"- **{c.get('channel', '')}**: {themes}")
    else:
        lines.append("_No comment data today. Run comment_miner.py to enable._")
    lines.append("")

    # Section 7: Recommended Actions
    lines.append("## 7. Recommended Actions for Tomorrow")
    lines.append("")
    if scored_ideas:
        top3 = sorted(scored_ideas, key=lambda x: float(x.get("total_score", 0)), reverse=True)[:3]
        for i, idea in enumerate(top3, 1):
            lines.append(f"{i}. **{idea.get('title_suggestion', '')}** — "
                          f"Score: {idea.get('total_score', '')} ({idea.get('pillar', '')})")
    else:
        lines.append("- Run competitor scan to generate recommendations.")
    lines.append("")

    # Section 8: Memory Update Proposals
    lines.append("## 8. Memory Update Proposals")
    lines.append("")
    lines.append("_Review these proposals and update memory files as needed:_")
    lines.append("")
    if scored_ideas:
        top_idea = max(scored_ideas, key=lambda x: float(x.get("total_score", 0) or 0))
        lines.append(f"- **New opportunity**: {top_idea.get('title_suggestion', '')} "
                      f"(Score: {top_idea.get('total_score', '')})")
    lines.append("- Update competitor_memory.md with any new patterns observed.")
    lines.append("- Update winning_patterns.md if new title/thumbnail formulas detected.")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*Report generated by Hermes Daily Report Generator — {date_str}*")

    return "\n".join(lines)


def generate_telegram_summary(date_str, competitors, scored_ideas):
    """Generate a condensed Telegram summary (under 4000 chars)."""
    lines = []
    lines.append(f"Hermes Daily Intel — {date_str}")
    lines.append("")

    if scored_ideas:
        top3 = sorted(scored_ideas, key=lambda x: float(x.get("total_score", 0)), reverse=True)[:3]
        lines.append("TOP 3 IDEAS:")
        for i, idea in enumerate(top3, 1):
            lines.append(f"{i}. {idea.get('title_suggestion', '')} ({idea.get('total_score', '')})")
        lines.append("")

    if competitors:
        lines.append(f"SCAN: {len(competitors)} videos from {len(set(v.get('channel', '') for v in competitors))} channels")
        lines.append("")

    # Top pillar
    if scored_ideas:
        pillars = {}
        for idea in scored_ideas:
            p = idea.get("pillar", "Unknown")
            pillars[p] = pillars.get(p, 0) + 1
        top_pillar = max(pillars, key=pillars.get)
        lines.append(f"HOTTEST PILLAR: {top_pillar} ({pillars[top_pillar]} videos)")
        lines.append("")

    lines.append("Full report: outputs/reports/")

    text = "\n".join(lines)
    # Ensure under 4000 chars
    if len(text) > 4000:
        text = text[:3997] + "..."
    return text


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate daily competitor intelligence report")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"),
                        help="Date to generate report for (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done")
    parser.add_argument("--repo-root", type=str, default=str(REPO_ROOT))
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    reports_dir = repo_root / "outputs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    date_str = args.date

    log("INFO", f"Hermes Daily Report Generator — {date_str}")

    # Read all input files
    competitors = read_csv_safe(repo_root / "data" / "competitors" / "daily" / f"{date_str}_competitors.csv")
    transcripts = read_csv_safe(repo_root / "data" / "competitors" / "transcripts" / f"{date_str}_transcript_summaries.csv")
    comments = read_csv_safe(repo_root / "data" / "competitors" / "comments" / f"{date_str}_comment_summaries.csv")
    scored_ideas = read_csv_safe(repo_root / "data" / "competitors" / "daily" / f"{date_str}_scored_ideas.csv")

    log("INFO", f"Input data: {len(competitors)} competitors, {len(transcripts)} transcripts, "
                f"{len(comments)} comments, {len(scored_ideas)} scored ideas")

    if args.dry_run:
        log("INFO", "DRY RUN — would generate:")
        log("INFO", f"  - outputs/reports/{date_str}_daily_competitor_intelligence.md")
        log("INFO", f"  - outputs/reports/{date_str}_telegram_summary.txt")
        return

    # Generate reports
    md_report = generate_markdown_report(date_str, competitors, transcripts, comments, scored_ideas)
    telegram_summary = generate_telegram_summary(date_str, competitors, scored_ideas)

    # Write outputs
    md_path = reports_dir / f"{date_str}_daily_competitor_intelligence.md"
    telegram_path = reports_dir / f"{date_str}_telegram_summary.txt"

    md_path.write_text(md_report, encoding="utf-8")
    telegram_path.write_text(telegram_summary, encoding="utf-8")

    log("INFO", f"Markdown report: {md_path}")
    log("INFO", f"Telegram summary: {telegram_path}")
    log("INFO", "Report generation complete")


if __name__ == "__main__":
    main()
