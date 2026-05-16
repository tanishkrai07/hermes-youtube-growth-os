#!/usr/bin/env python3
"""Create a dated weekly analytics CSV from the template."""

from __future__ import annotations

from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data" / "channel_analytics" / "weekly" / "channel_analytics_weekly_template.csv"


def main() -> None:
    target = ROOT / "data" / "channel_analytics" / "weekly" / f"{date.today().isoformat()}_weekly_analytics.csv"
    if target.exists():
        print(f"Already exists: {target}")
        return
    target.write_text(TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Created {target}")


if __name__ == "__main__":
    main()
