#!/usr/bin/env python3
"""
Hermes YouTube Growth OS — Trend Scoring Engine
Scores competitor signals to generate prioritized video ideas.

Usage:
    python3 scripts/trend_scorer.py [--date YYYY-MM-DD] [--dry-run]

Input:
    data/competitors/daily/YYYY-MM-DD_competitors.csv
    data/competitors/comments/YYYY-MM-DD_comment_summaries.csv (optional)
    memory/video_idea_bank.csv
    memory/winning_patterns.md (parsed for title formula matching)

Output:
    data/competitors/daily/YYYY-MM-DD_scored_ideas.csv
"""

import csv
import math
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "scoring_weights.yaml"
INPUT_DIR = REPO_ROOT / "data" / "competitors" / "daily"
COMMENTS_DIR = REPO_ROOT / "data" / "competitors" / "comments"
IDEA_BANK_PATH = REPO_ROOT / "memory" / "video_idea_bank.csv"
WINNING_PATTERNS_PATH = REPO_ROOT / "memory" / "winning_patterns.md"
CHANNEL_BRAIN_PATH = REPO_ROOT / "memory" / "channel_brain.md"

CSV_HEADERS = [
    "date_scored", "idea_id", "title_suggestion", "pillar", "source_channel",
    "source_video_url", "view_velocity_score", "title_formula_match_score",
    "thumbnail_gap_score", "comment_demand_score", "pillar_priority_score",
    "freshness_score", "competition_saturation_penalty", "total_score",
    "priority", "status", "notes"
]

# Default scoring weights (used if config file doesn't exist)
DEFAULT_WEIGHTS = {
    "view_velocity": 1.0,
    "title_formula_match": 1.0,
    "thumbnail_gap": 1.0,
    "comment_demand": 1.0,
    "pillar_priority": 1.0,
    "freshness": 1.0,
    "competition_saturation": 1.0,
}

# Current strategic pillars (from channel_brain.md)
PRIORITY_PILLARS = [
    "Leg / Circulation",
    "Muscle / Strength",
    "Sleep / Night Peeing",
    "Food + Warning",
    "Brain / Memory",
    "Medication Warning",
    "Heart Attack / Stroke Warning",
    "Blood Type / Genetic Risk",
    "Stem Cell / Anti-Aging",
    "Microplastics / Organ Damage",
]

MID_PILLARS = [
    "Pain / Joints",
    "Organ Damage",
    "Longevity / Genetic Risk",
    "Warning / Night Habits",
    "Cancer Prevention",
    "Supplement Warning",
]


def log(level, message):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{level}] {ts} {message}", flush=True)


def load_weights():
    """Load scoring weights from config file."""
    weights = DEFAULT_WEIGHTS.copy()
    if CONFIG_PATH.exists():
        try:
            import yaml
            with open(CONFIG_PATH) as f:
                config = yaml.safe_load(f) or {}
            weights.update(config.get("weights", {}))
            log("INFO", f"Loaded scoring weights from {CONFIG_PATH}")
        except ImportError:
            log("WARN", "pyyaml not installed, using default weights")
        except Exception as e:
            log("WARN", f"Error loading config: {e}, using default weights")
    else:
        log("INFO", "No config file found, using default weights")
    return weights


def load_winning_patterns():
    """Parse winning_patterns.md to extract title formulas."""
    formulas = []
    if WINNING_PATTERNS_PATH.exists():
        content = WINNING_PATTERNS_PATH.read_text(encoding="utf-8")
        # Extract formula patterns from the file
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith('"') and line.endswith('"'):
                formula = line.strip('"')
                formulas.append(formula.lower())
            elif "— Score:" in line:
                # Extract the formula part before the score
                formula = line.split("— Score:")[0].strip().strip('"')
                if formula:
                    formulas.append(formula.lower())
    return formulas


def score_view_velocity(views, published_date):
    """Score 0-5 based on view velocity (views per day)."""
    try:
        views = int(views)
    except (ValueError, TypeError):
        return 0

    if views == 0:
        return 0

    # Estimate days since published
    days = 7  # default
    if published_date:
        try:
            pub_date = datetime.strptime(published_date[:10], "%Y-%m-%d")
            days = max(1, (datetime.now() - pub_date).days)
        except ValueError:
            pass

    views_per_day = views / days

    # Log scale: 0 = 0 vpd, 5 = 500+ vpd
    if views_per_day >= 500:
        return 5
    elif views_per_day >= 100:
        return 4
    elif views_per_day >= 50:
        return 3
    elif views_per_day >= 10:
        return 2
    elif views_per_day >= 1:
        return 1
    return 0


def score_title_formula(title, winning_formulas):
    """Score 0-3 based on overlap with winning title patterns."""
    title_lower = title.lower()
    matches = 0

    # Check for key pattern elements
    pattern_elements = [
        (r"\bnever\b", "NEVER frame"),
        (r"\bstop\b", "STOP frame"),
        (r"\bwarn", "Warning frame"),
        (r"\bforgotten\b", "Forgotten frame"),
        (r"\bsimple\b", "Simple frame"),
        (r"\bdestroy", "Destruction frame"),
        (r"\bdoes your\b", "Personalized frame"),
        (r"\bsigns?\b", "Signs frame"),
        (r"\bhe died\b", "Death fear frame"),
        (r"\bdoctor\b|\bsurgeon\b", "Authority frame"),
        (r"\b\d+\s*(second|minute|hour)", "Time hook"),
        (r"\bafter\s+\d+\b", "Age marker"),
        (r"\bover\s+\d+\b", "Age marker"),
        (r"\bseniors?\b", "Age marker"),
        (r"\btr[io]ple|\bdouble|\btwo\b", "Multiplier claim"),
    ]

    for pattern, _ in pattern_elements:
        if re.search(pattern, title_lower):
            matches += 1

    if matches >= 3:
        return 3
    elif matches >= 2:
        return 2
    elif matches >= 1:
        return 1
    return 0


def score_thumbnail_gap(idea_pillar, existing_thumbnails):
    """Score 0-3 based on underserved visual angle."""
    # If no competitor has covered this pillar recently, score high
    pillar_coverage = {}
    for thumb in existing_thumbnails:
        p = thumb.get("pillar", "Unknown")
        pillar_coverage[p] = pillar_coverage.get(p, 0) + 1

    coverage = pillar_coverage.get(idea_pillar, 0)
    if coverage == 0:
        return 3
    elif coverage <= 2:
        return 2
    elif coverage <= 5:
        return 1
    return 0


def score_comment_demand(comment_count, comment_themes):
    """Score 0-3 based on comment volume and question frequency."""
    try:
        count = int(comment_count)
    except (ValueError, TypeError):
        count = 0

    question_marks = comment_themes.count("?") if comment_themes else 0

    if count >= 50 and question_marks >= 5:
        return 3
    elif count >= 20 or question_marks >= 3:
        return 2
    elif count >= 5 or question_marks >= 1:
        return 1
    return 0


def score_pillar_priority(pillar):
    """Score 0-2 based on current strategic pillar weight."""
    if pillar in PRIORITY_PILLARS[:3]:
        return 2
    elif pillar in PRIORITY_PILLARS:
        return 1
    elif pillar in MID_PILLARS:
        return 1
    return 0


def score_freshness(published_date):
    """Score 0-2 based on recency of topic trend."""
    if not published_date:
        return 0
    try:
        pub_date = datetime.strptime(published_date[:10], "%Y-%m-%d")
        days_ago = (datetime.now() - pub_date).days
        if days_ago <= 2:
            return 2
        elif days_ago <= 7:
            return 1
        return 0
    except ValueError:
        return 0


def score_competition_saturation(pillar, all_videos):
    """Score -2 to 0 based on how many competitors covered this pillar."""
    competitors_covering = set()
    for v in all_videos:
        if v.get("pillar") == pillar:
            competitors_covering.add(v.get("channel", ""))

    count = len(competitors_covering)
    if count >= 5:
        return -2
    elif count >= 2:
        return -1
    return 0


def generate_idea_title(video):
    """Generate a Dr. Victor Kane-style idea title from a competitor video."""
    original_title = video.get("video_title", "")
    pillar = video.get("pillar", "")

    # Transform competitor title to Dr. Victor Kane style
    # Remove competitor's doctor name
    import re
    title = re.sub(r"^(Dr\.|Doctor)\s+\w+", "", original_title).strip()
    title = re.sub(r"^\s*[-:]\s*", "", title).strip()

    # Add Dr. Victor Kane branding
    if "never" in original_title.lower():
        return f"Dr. Victor Kane: {title}"
    elif "?" in original_title:
        return f"Dr. Victor Kane: {title}"
    else:
        return f"Dr. Victor Kane: {title}"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Score competitor signals for video ideas")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"),
                        help="Date of the competitor CSV to process (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done")
    parser.add_argument("--repo-root", type=str, default=str(REPO_ROOT))
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    input_dir = repo_root / "data" / "competitors" / "daily"
    output_dir = repo_root / "data" / "competitors" / "daily"
    output_dir.mkdir(parents=True, exist_ok=True)

    input_path = input_dir / f"{args.date}_competitors.csv"
    output_path = output_dir / f"{args.date}_scored_ideas.csv"

    if not input_path.exists():
        log("ERROR", f"Input file not found: {input_path}")
        log("INFO", "Run fetch_competitor_videos.py first to generate the daily CSV.")
        sys.exit(2)

    log("INFO", f"Hermes Trend Scorer — {args.date}")
    log("INFO", f"Input: {input_path}")

    # Load data
    weights = load_weights()
    winning_formulas = load_winning_patterns()

    videos = []
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            videos.append(row)

    log("INFO", f"Scoring {len(videos)} videos")

    if args.dry_run:
        log("INFO", "DRY RUN — would score:")
        for v in videos:
            log("INFO", f"  - {v['channel']}: {v['video_title'][:60]}...")
        return

    # Score each video
    scored_ideas = []
    for i, video in enumerate(videos):
        pillar = video.get("pillar", "General Health")
        title = video.get("video_title", "")
        views = video.get("views", 0)
        published = video.get("published_date", "")
        comments = video.get("comment_themes", "")

        # Calculate scores
        vs = score_view_velocity(views, published) * weights["view_velocity"]
        fs = score_title_formula(title, winning_formulas) * weights["title_formula_match"]
        ts = score_thumbnail_gap(pillar, videos) * weights["thumbnail_gap"]
        cs = score_comment_demand(video.get("comment_count", 0), comments) * weights["comment_demand"]
        ps = score_pillar_priority(pillar) * weights["pillar_priority"]
        fres = score_freshness(published) * weights["freshness"]
        sat = score_competition_saturation(pillar, videos) * weights["competition_saturation"]

        total = vs + fs + ts + cs + ps + fres + sat

        # Determine priority
        if total >= 15:
            priority = "GREEN"
        elif total >= 10:
            priority = "YELLOW"
        else:
            priority = "RED"

        idea_title = generate_idea_title(video)

        scored_ideas.append({
            "date_scored": args.date,
            "idea_id": f"I{args.date.replace('-', '')}_{i + 1:03d}",
            "title_suggestion": idea_title[:100],
            "pillar": pillar,
            "source_channel": video.get("channel", ""),
            "source_video_url": video.get("url", ""),
            "view_velocity_score": round(vs, 1),
            "title_formula_match_score": round(fs, 1),
            "thumbnail_gap_score": round(ts, 1),
            "comment_demand_score": round(cs, 1),
            "pillar_priority_score": round(ps, 1),
            "freshness_score": round(fres, 1),
            "competition_saturation_penalty": round(sat, 1),
            "total_score": round(total, 1),
            "priority": priority,
            "status": "scored",
            "notes": video.get("idea_signal", "")
        })

    # Sort by total score descending
    scored_ideas.sort(key=lambda x: x["total_score"], reverse=True)

    # Write output
    file_exists = output_path.exists()
    with open(output_path, "a" if file_exists else "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        for idea in scored_ideas:
            writer.writerow(idea)

    # Summary
    green = sum(1 for s in scored_ideas if s["priority"] == "GREEN")
    yellow = sum(1 for s in scored_ideas if s["priority"] == "YELLOW")
    red = sum(1 for s in scored_ideas if s["priority"] == "RED")

    log("INFO", f"Scored {len(scored_ideas)} ideas: {green} GREEN, {yellow} YELLOW, {red} RED")
    log("INFO", f"Output: {output_path}")

    if scored_ideas:
        top = scored_ideas[0]
        log("INFO", f"Top idea: {top['title_suggestion']} (Score: {top['total_score']})")


if __name__ == "__main__":
    main()
