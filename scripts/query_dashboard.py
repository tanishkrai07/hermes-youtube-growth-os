#!/usr/bin/env python3
"""
Hermes YouTube Growth OS — Dashboard Query CLI
Query the Hermes intelligence database for common lookups.

Usage:
    python3 scripts/query_dashboard.py top-ideas [--limit 20] [--min-score 15]
    python3 scripts/query_dashboard.py trends [--days 30] [--pillar PILLAR]
    python3 scripts/query_dashboard.py competitors [--channel NAME]
    python3 scripts/query_dashboard.py idea-bank [--pillar PILLAR] [--min-score 15]
    python3 scripts/query_dashboard.py scan-log [--limit 10]
"""

import csv
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "hermes_intelligence.db"
IDEA_BANK_PATH = REPO_ROOT / "memory" / "video_idea_bank.csv"
SCORE_DIR = REPO_ROOT / "data" / "competitors" / "daily"


def get_db():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        print("Run build_database.py first to create the database.")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def cmd_top_ideas(args):
    """Show top ideas by score."""
    limit = int(getattr(args, "limit", 20) or 20)
    min_score = float(getattr(args, "min_score", 15) or 15)

    # Try database first, fall back to CSV
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT idea_id, title_suggestion, pillar, total_score, priority, source_channel, date_scored
            FROM video_ideas
            WHERE total_score >= ?
            ORDER BY total_score DESC
            LIMIT ?
        """, (min_score, limit))
        rows = c.fetchall()
        conn.close()
    except Exception:
        rows = []

    if not rows:
        # Fall back to CSV files
        print("No database results. Checking CSV files...")
        ideas = []
        for csv_file in sorted(SCORE_DIR.glob("*_scored_ideas.csv")):
            with open(csv_file, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        if float(row.get("total_score", 0)) >= min_score:
                            ideas.append(row)
                    except ValueError:
                        pass
        ideas.sort(key=lambda x: float(x.get("total_score", 0)), reverse=True)
        rows = ideas[:limit]

        if not rows:
            print(f"No ideas found with score >= {min_score}")
            return

        print(f"\nTop {len(rows)} Ideas (score >= {min_score}):")
        print("-" * 80)
        for i, row in enumerate(rows, 1):
            print(f"{i:3d}. [{row.get('priority', '?'):6s}] {row.get('total_score', '?'):5s} | "
                  f"{row.get('title_suggestion', '')[:50]}")
            print(f"     Pillar: {row.get('pillar', '')} | Source: {row.get('source_channel', '')}")
        return

    print(f"\nTop {len(rows)} Ideas (score >= {min_score}):")
    print("-" * 80)
    for i, row in enumerate(rows, 1):
        print(f"{i:3d}. [{row['priority']:6s}] {row['total_score']:5.1f} | "
              f"{row['title_suggestion'][:50]}")
        print(f"     Pillar: {row['pillar']} | Source: {row['source_channel']}")


def cmd_trends(args):
    """Show trending topics by pillar."""
    days = int(getattr(args, "days", 30) or 30)
    pillar_filter = getattr(args, "pillar", None)

    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    try:
        conn = get_db()
        c = conn.cursor()

        if pillar_filter:
            c.execute("""
                SELECT pillar, COUNT(*) as video_count, AVG(view_count) as avg_views
                FROM videos
                WHERE pillar = ? AND published_date >= ?
                GROUP BY pillar
            """, (pillar_filter, since))
        else:
            c.execute("""
                SELECT pillar, COUNT(*) as video_count, AVG(view_count) as avg_views
                FROM videos
                WHERE published_date >= ?
                GROUP BY pillar
                ORDER BY avg_views DESC
            """, (since,))

        rows = c.fetchall()
        conn.close()

        if not rows:
            print(f"No trend data found for the last {days} days.")
            return

        print(f"\nTrending Pillars (last {days} days):")
        print("-" * 70)
        print(f"{'Pillar':<30s} {'Videos':>8s} {'Avg Views':>12s}")
        print("-" * 70)
        for row in rows:
            print(f"{row['pillar']:<30s} {row['video_count']:>8d} {row['avg_views']:>12,.0f}")

    except Exception as e:
        print(f"Error querying trends: {e}")


def cmd_competitors(args):
    """Show competitor information."""
    channel = getattr(args, "channel", None)

    try:
        conn = get_db()
        c = conn.cursor()

        if channel:
            c.execute("""
                SELECT channel_name, channel_url, priority, subscriber_count,
                       total_videos, total_views, last_scanned
                FROM competitors
                WHERE channel_name LIKE ?
            """, (f"%{channel}%",))
        else:
            c.execute("""
                SELECT channel_name, priority, subscriber_count, last_scanned
                FROM competitors
                WHERE is_active = 1
                ORDER BY priority, channel_name
            """)

        rows = c.fetchall()
        conn.close()

        if not rows:
            print("No competitor data found.")
            return

        print(f"\nCompetitor Watchlist:")
        print("-" * 70)
        for row in rows:
            subs = f"{row['subscriber_count']:,}" if row['subscriber_count'] else "N/A"
            print(f"{row['channel_name']:<30s} [{row['priority']:6s}] Subs: {subs} | Last: {row['last_scanned']}")

    except Exception as e:
        print(f"Error querying competitors: {e}")


def cmd_idea_bank(args):
    """Show ideas from the idea bank."""
    pillar_filter = getattr(args, "pillar", None)
    min_score = float(getattr(args, "min_score", 0) or 0)

    if not IDEA_BANK_PATH.exists():
        print(f"Idea bank not found: {IDEA_BANK_PATH}")
        return

    ideas = []
    with open(IDEA_BANK_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                score = float(row.get("score", 0))
            except ValueError:
                score = 0
            if score >= min_score:
                if not pillar_filter or pillar_filter.lower() in row.get("pillar", "").lower():
                    ideas.append({**row, "score_num": score})

    ideas.sort(key=lambda x: x["score_num"], reverse=True)

    if not ideas:
        print("No ideas match the criteria.")
        return

    print(f"\nIdea Bank ({len(ideas)} ideas):")
    print("-" * 80)
    for i, idea in enumerate(ideas[:20], 1):
        print(f"{i:3d}. [{idea.get('score', '?'):>3s}] {idea.get('title', '')[:55]}")
        print(f"     Pillar: {idea.get('pillar', '')} | Status: {idea.get('status', '')}")


def cmd_scan_log(args):
    """Show recent scan log entries."""
    limit = int(getattr(args, "limit", 10) or 10)

    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT scan_date, channels_scanned, videos_found,
                   new_ideas_generated, trends_detected, status
            FROM scan_log
            ORDER BY scan_date DESC
            LIMIT ?
        """, (limit,))
        rows = c.fetchall()
        conn.close()

        if not rows:
            print("No scan log entries found.")
            return

        print(f"\nRecent Scans (last {len(rows)}):")
        print("-" * 80)
        print(f"{'Date':<12s} {'Channels':>8s} {'Videos':>7s} {'Ideas':>6s} {'Trends':>7s} {'Status':<12s}")
        print("-" * 80)
        for row in rows:
            print(f"{row['scan_date']:<12s} {row['channels_scanned']:>8d} {row['videos_found']:>7d} "
                  f"{row['new_ideas_generated']:>6d} {row['trends_detected']:>7d} {row['status']:<12s}")

    except Exception as e:
        print(f"Error querying scan log: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Query Hermes intelligence database")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # top-ideas
    p_ideas = subparsers.add_parser("top-ideas", help="Show top ideas by score")
    p_ideas.add_argument("--limit", type=int, default=20)
    p_ideas.add_argument("--min-score", type=float, default=15)

    # trends
    p_trends = subparsers.add_parser("trends", help="Show trending topics by pillar")
    p_trends.add_argument("--days", type=int, default=30)
    p_trends.add_argument("--pillar", type=str)

    # competitors
    p_comp = subparsers.add_parser("competitors", help="Show competitor information")
    p_comp.add_argument("--channel", type=str)

    # idea-bank
    p_bank = subparsers.add_parser("idea-bank", help="Show ideas from the idea bank")
    p_bank.add_argument("--pillar", type=str)
    p_bank.add_argument("--min-score", type=float, default=0)

    # scan-log
    p_log = subparsers.add_parser("scan-log", help="Show recent scan log entries")
    p_log.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "top-ideas": cmd_top_ideas,
        "trends": cmd_trends,
        "competitors": cmd_competitors,
        "idea-bank": cmd_idea_bank,
        "scan-log": cmd_scan_log,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
