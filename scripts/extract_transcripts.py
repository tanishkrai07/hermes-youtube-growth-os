#!/usr/bin/env python3
"""
Hermes YouTube Growth OS — Transcript Extraction Pipeline
Extracts transcripts from competitor videos using youtube-transcript-api with yt-dlp fallback.

Usage:
    python3 scripts/extract_transcripts.py [--date YYYY-MM-DD] [--dry-run]

Input:
    data/competitors/daily/YYYY-MM-DD_competitors.csv

Output:
    data/competitors/transcripts/YYYY-MM-DD_{channel}_{video_id}.txt
    data/competitors/transcripts/YYYY-MM-DD_transcript_summaries.csv
"""

import csv
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = REPO_ROOT / "data" / "competitors" / "daily"
OUTPUT_DIR = REPO_ROOT / "data" / "competitors" / "transcripts"

CSV_HEADERS = [
    "video_url", "channel", "video_title", "transcript_status",
    "word_count", "first_100_chars", "key_hook_summary", "file_path"
]


def log(level, message):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{level}] {ts} {message}", flush=True)


def extract_video_id(url):
    """Extract video ID from YouTube URL."""
    if not url:
        return None
    patterns = [
        r"v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"embed/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def fetch_transcript_youtube_api(video_id):
    """Try to fetch transcript using youtube-transcript-api."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id, languages=["en", "en-US", "en-GB"])
        # The fetch method returns a FetchedTranscript object with snippets
        text = " ".join([snippet.text for snippet in transcript.snippets])
        return text, "youtube-transcript-api"
    except ImportError:
        return None, "youtube-transcript-api-not-installed"
    except Exception as e:
        return None, f"youtube-transcript-api-failed: {str(e)[:100]}"


def fetch_transcript_ytdlp(video_id):
    """Fallback: fetch transcript using yt-dlp."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--write-auto-sub", "--sub-lang", "en",
                "--skip-download",
                "--no-check-certificates",
                "-o", str(OUTPUT_DIR / f"%(id)s"),
                url
            ],
            capture_output=True, text=True, timeout=60,
            cwd=str(REPO_ROOT)
        )

        # Find the subtitle file
        sub_files = list(OUTPUT_DIR.glob(f"{video_id}*.en.vtt")) + \
                    list(OUTPUT_DIR.glob(f"{video_id}*.en.srt")) + \
                    list(REPO_ROOT.glob(f"{video_id}*.en.vtt")) + \
                    list(REPO_ROOT.glob(f"{video_id}*.en.srt"))

        if sub_files:
            sub_file = sub_files[0]
            content = sub_file.read_text(encoding="utf-8", errors="ignore")

            # Parse VTT/SRT to plain text
            lines = []
            for line in content.split("\n"):
                line = line.strip()
                if not line or line.startswith("WEBVTT") or line.startswith("NOTE"):
                    continue
                if re.match(r"^\d+$", line):
                    continue
                if "-->" in line:
                    continue
                if re.match(r"^\d{2}:\d{2}", line):
                    continue
                # Remove VTT formatting tags
                line = re.sub(r"<[^>]+>", "", line)
                if line:
                    lines.append(line)

            text = " ".join(lines)
            # Clean up duplicate lines (VTT often repeats)
            words = text.split()
            # Remove consecutive duplicate words
            cleaned = [words[0]] if words else []
            for w in words[1:]:
                if w != cleaned[-1]:
                    cleaned.append(w)
            text = " ".join(cleaned)

            # Clean up temp files
            for f in sub_files:
                try:
                    f.unlink()
                except Exception:
                    pass

            return text, "yt-dlp"

        return None, "yt-dlp-no-subtitles"
    except FileNotFoundError:
        return None, "yt-dlp-not-installed"
    except subprocess.TimeoutExpired:
        return None, "yt-dlp-timeout"
    except Exception as e:
        return None, f"yt-dlp-error: {str(e)[:100]}"


def extract_hook(text):
    """Extract the first sentence as the key hook."""
    if not text:
        return ""
    # Get first sentence
    sentences = re.split(r"[.!?]", text)
    first = sentences[0].strip() if sentences else ""
    return first[:200]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract transcripts from competitor videos")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"),
                        help="Date of the competitor CSV to process (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done")
    parser.add_argument("--repo-root", type=str, default=str(REPO_ROOT))
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    input_dir = repo_root / "data" / "competitors" / "daily"
    output_dir = repo_root / "data" / "competitors" / "transcripts"
    output_dir.mkdir(parents=True, exist_ok=True)

    input_path = input_dir / f"{args.date}_competitors.csv"
    summary_path = output_dir / f"{args.date}_transcript_summaries.csv"

    if not input_path.exists():
        log("ERROR", f"Input file not found: {input_path}")
        log("INFO", "Run fetch_competitor_videos.py first to generate the daily CSV.")
        sys.exit(2)

    log("INFO", f"Hermes Transcript Extractor — {args.date}")
    log("INFO", f"Input: {input_path}")

    # Read input CSV
    videos = []
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("url"):
                videos.append(row)

    log("INFO", f"Found {len(videos)} videos to process")

    if args.dry_run:
        log("INFO", "DRY RUN — would extract transcripts for:")
        for v in videos:
            vid = extract_video_id(v["url"])
            log("INFO", f"  - {v['channel']}: {v['video_title'][:60]}... (ID: {vid})")
        return

    # Process each video
    summaries = []
    success_count = 0
    fail_count = 0

    for i, video in enumerate(videos):
        url = video["url"]
        channel = video["channel"]
        title = video["video_title"]
        video_id = extract_video_id(url)

        if not video_id:
            log("WARN", f"[{i + 1}/{len(videos)}] Could not extract video ID from: {url}")
            fail_count += 1
            summaries.append({
                "video_url": url, "channel": channel, "video_title": title,
                "transcript_status": "no-video-id", "word_count": 0,
                "first_100_chars": "", "key_hook_summary": "", "file_path": ""
            })
            continue

        log("INFO", f"[{i + 1}/{len(videos)}] {channel}: {title[:60]}...")

        # Try primary method
        text, status = fetch_transcript_youtube_api(video_id)

        # Fallback to yt-dlp
        if text is None and "not-installed" not in status:
            log("INFO", f"  Primary failed ({status}), trying yt-dlp fallback...")
            time.sleep(1)
            text, status = fetch_transcript_ytdlp(video_id)

        if text:
            # Save transcript
            safe_channel = re.sub(r"[^a-zA-Z0-9]+", "_", channel.lower())[:30]
            filename = f"{args.date}_{safe_channel}_{video_id}.txt"
            filepath = output_dir / filename
            filepath.write_text(text, encoding="utf-8")

            word_count = len(text.split())
            hook = extract_hook(text)
            first_100 = text[:100]

            summaries.append({
                "video_url": url, "channel": channel, "video_title": title,
                "transcript_status": status, "word_count": word_count,
                "first_100_chars": first_100, "key_hook_summary": hook,
                "file_path": str(filepath.relative_to(repo_root))
            })

            log("INFO", f"  OK ({status}) — {word_count} words")
            success_count += 1
        else:
            log("WARN", f"  FAILED — {status}")
            fail_count += 1
            summaries.append({
                "video_url": url, "channel": channel, "video_title": title,
                "transcript_status": status, "word_count": 0,
                "first_100_chars": "", "key_hook_summary": "", "file_path": ""
            })

        time.sleep(1)  # Rate limiting

    # Write summary CSV
    file_exists = summary_path.exists()
    with open(summary_path, "a" if file_exists else "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        for s in summaries:
            writer.writerow(s)

    log("INFO", f"Summary written to {summary_path}")
    log("INFO", f"Results: {success_count} success, {fail_count} failed, {len(videos)} total")


if __name__ == "__main__":
    main()
