#!/usr/bin/env python3
"""Build a compact context pack for Hermes.

This script intentionally reads curated memory files, not the full raw archive.
The output is meant to be pasted into Hermes before daily research, idea work,
script work, or analytics review.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "context_packs" / "current_context_pack.md"

MEMORY_FILES = [
    "memory/channel_brain.md",
    "memory/competitor_memory.md",
    "memory/winning_patterns.md",
    "memory/failed_patterns.md",
    "memory/analytics_memory.md",
    "memory/next_actions.md",
    "memory/first_10_launch_slate_summary.md",
]


def read_text(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.exists():
        return f"_Missing: {relative_path}_\n"
    return path.read_text(encoding="utf-8").strip()


def latest_files(folder: str, limit: int = 3) -> list[Path]:
    path = ROOT / folder
    if not path.exists():
        return []
    files = [p for p in path.iterdir() if p.is_file() and not p.name.startswith(".")]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]


def csv_preview(path: Path, limit: int = 5) -> str:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                return "_No CSV headers found._"
            rows = []
            for idx, row in enumerate(reader):
                if idx >= limit:
                    break
                compact = {k: v for k, v in row.items() if v}
                rows.append(compact)
    except UnicodeDecodeError:
        return "_Could not preview non-UTF-8 CSV._"

    if not rows:
        return f"Headers only: {', '.join(reader.fieldnames)}"

    lines = [f"Columns: {', '.join(reader.fieldnames)}"]
    for idx, row in enumerate(rows, 1):
        rendered = "; ".join(f"{k}: {v}" for k, v in row.items())
        lines.append(f"{idx}. {rendered}")
    return "\n".join(lines)


def section(title: str, body: str) -> str:
    return f"\n## {title}\n\n{body.strip()}\n"


def build() -> str:
    parts = [
        "# Hermes Current Context Pack",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "Use this compact pack before most Hermes tasks. Read raw files only when this pack is insufficient.",
    ]

    for relative_path in MEMORY_FILES:
        parts.append(section(relative_path, read_text(relative_path)))

    tracker = ROOT / "data" / "video_pipeline" / "first_10_tracker.csv"
    if tracker.exists():
        parts.append(section("First 10 Video Tracker Preview", csv_preview(tracker, limit=10)))

    for folder, title in [
        ("data/competitors/daily", "Latest Competitor Daily Files"),
        ("data/channel_analytics/weekly", "Latest Weekly Analytics Files"),
        ("data/thumbnails/analysis", "Latest Thumbnail Analysis Files"),
    ]:
        files = latest_files(folder)
        if not files:
            parts.append(section(title, "_No files yet._"))
            continue
        body_parts = []
        for file_path in files:
            if file_path.suffix.lower() == ".csv":
                body = csv_preview(file_path)
            else:
                body = file_path.read_text(encoding="utf-8", errors="replace")[:4000]
            body_parts.append(f"### {file_path.relative_to(ROOT)}\n\n{body}")
        parts.append(section(title, "\n\n".join(body_parts)))

    return "\n".join(parts).strip() + "\n"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build(), encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
