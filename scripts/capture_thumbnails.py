#!/usr/bin/env python3
"""
Hermes YouTube Growth OS — Thumbnail Capture
Downloads competitor video thumbnails for visual analysis.

Usage:
    python3 scripts/capture_thumbnails.py [--date YYYY-MM-DD] [--dry-run]

Input:
    data/competitors/daily/YYYY-MM-DD_competitors.csv

Output:
    data/thumbnails/competitor/YYYY-MM-DD_{channel}_{video_id}.jpg
    data/thumbnails/competitor_thumbnails_log.csv
"""

import csv
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = REPO_ROOT / "data" / "competitors" / "daily"
OUTPUT_DIR = REPO_ROOT / "data" / "thumbnails" / "competitor"
LOG_PATH = REPO_ROOT / "data" / "thumbnails" / "competitor_thumbnails_log.csv"

CSV_HEADERS = [
    "date_found", "channel", "video_id", "video_url", "thumbnail_path",
    "file_size_bytes", "download_status"
]


def log(level, message):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{level}] {ts} {message}", flush=True)


def extract_video_id(url):
    """Extract video ID from YouTube URL."""
    if not url:
        return None
    import re
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


def download_thumbnail(video_id, output_path):
    """
    Download thumbnail for a video. Tries maxresdefault first, then hqdefault.
    Returns (file_size, status).
    """
    urls = [
        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
        f"https://img.youtube.com/vi/{video_id}/sddefault.jpg",
    ]

    for url in urls:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Hermes-YouTube-Growth-OS/1.0"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                if len(data) > 1000:  # Valid image (not a 1x1 placeholder)
                    output_path.write_bytes(data)
                    return len(data), f"ok-{url.split('/')[-1].replace('.jpg', '')}"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            return 0, f"http-{e.code}"
        except Exception as e:
            return 0, f"error-{str(e)[:50]}"

    return 0, "not-found"


def download_thumbnail_ytdlp(video_id, output_path):
    """Fallback: use yt-dlp to download thumbnail."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--write-thumbnail",
                "--skip-download",
                "--no-check-certificates",
                "-o", str(output_path.with_suffix("")),
                url
            ],
            capture_output=True, text=True, timeout=60,
            cwd=str(REPO_ROOT)
        )

        # Find the downloaded thumbnail
        for ext in [".jpg", ".webp", ".png"]:
            candidate = output_path.with_suffix(ext)
            if candidate.exists():
                size = candidate.stat().st_size
                # Rename to .jpg if needed
                if ext != ".jpg":
                    new_path = output_path.with_suffix(".jpg")
                    candidate.rename(new_path)
                    return size, "yt-dlp"
                return size, "yt-dlp"

        return 0, "yt-dlp-no-thumbnail"
    except FileNotFoundError:
        return 0, "yt-dlp-not-installed"
    except subprocess.TimeoutExpired:
        return 0, "yt-dlp-timeout"
    except Exception as e:
        return 0, f"yt-dlp-error-{str(e)[:50]}"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Download competitor video thumbnails")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"),
                        help="Date of the competitor CSV to process (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done")
    parser.add_argument("--repo-root", type=str, default=str(REPO_ROOT))
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    input_dir = repo_root / "data" / "competitors" / "daily"
    output_dir = repo_root / "data" / "thumbnails" / "competitor"
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = repo_root / "data" / "thumbnails" / "competitor_thumbnails_log.csv"

    input_path = input_dir / f"{args.date}_competitors.csv"

    if not input_path.exists():
        log("ERROR", f"Input file not found: {input_path}")
        log("INFO", "Run fetch_competitor_videos.py first to generate the daily CSV.")
        sys.exit(2)

    log("INFO", f"Hermes Thumbnail Capture — {args.date}")
    log("INFO", f"Input: {input_path}")
    log("INFO", f"Output dir: {output_dir}")

    # Read input CSV
    videos = []
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("url"):
                videos.append(row)

    log("INFO", f"Found {len(videos)} videos to process")

    if args.dry_run:
        log("INFO", "DRY RUN — would download thumbnails for:")
        for v in videos:
            vid = extract_video_id(v["url"])
            log("INFO", f"  - {v['channel']}: {v['video_title'][:60]}... (ID: {vid})")
        return

    # Process each video
    log_entries = []
    success_count = 0
    fail_count = 0

    for i, video in enumerate(videos):
        url = video["url"]
        channel = video["channel"]
        video_id = extract_video_id(url)

        if not video_id:
            log("WARN", f"[{i + 1}/{len(videos)}] Could not extract video ID from: {url}")
            fail_count += 1
            log_entries.append({
                "date_found": args.date, "channel": channel, "video_id": "",
                "video_url": url, "thumbnail_path": "", "file_size_bytes": 0,
                "download_status": "no-video-id"
            })
            continue

        safe_channel = re.sub(r"[^a-zA-Z0-9]+", "_", channel.lower())[:30]
        filename = f"{args.date}_{safe_channel}_{video_id}.jpg"
        output_path = output_dir / filename

        # Skip if already downloaded
        if output_path.exists():
            size = output_path.stat().st_size
            log("INFO", f"[{i + 1}/{len(videos)}] {channel}: already exists ({size} bytes)")
            log_entries.append({
                "date_found": args.date, "channel": channel, "video_id": video_id,
                "video_url": url, "thumbnail_path": str(output_path.relative_to(repo_root)),
                "file_size_bytes": size, "download_status": "already-exists"
            })
            success_count += 1
            continue

        log("INFO", f"[{i + 1}/{len(videos)}] {channel}: downloading...")

        # Try HTTP download first
        size, status = download_thumbnail(video_id, output_path)

        # Fallback to yt-dlp
        if size == 0 and "not-found" in status:
            log("INFO", f"  HTTP download failed, trying yt-dlp fallback...")
            size, status = download_thumbnail_ytdlp(video_id, output_path)

        if size > 0:
            log("INFO", f"  OK — {size} bytes ({status})")
            success_count += 1
        else:
            log("WARN", f"  FAILED — {status}")
            fail_count += 1

        log_entries.append({
            "date_found": args.date, "channel": channel, "video_id": video_id,
            "video_url": url,
            "thumbnail_path": str(output_path.relative_to(repo_root)) if size > 0 else "",
            "file_size_bytes": size, "download_status": status
        })

        time.sleep(0.3)  # Rate limiting

    # Write log CSV
    file_exists = log_path.exists()
    with open(log_path, "a" if file_exists else "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        for entry in log_entries:
            writer.writerow(entry)

    log("INFO", f"Log written to {log_path}")
    log("INFO", f"Results: {success_count} success, {fail_count} failed, {len(videos)} total")


if __name__ == "__main__":
    main()
