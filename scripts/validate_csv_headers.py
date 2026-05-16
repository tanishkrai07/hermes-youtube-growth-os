#!/usr/bin/env python3
"""Validate CSV headers against a simple schema file.

Usage:
  python3 scripts/validate_csv_headers.py schemas/competitor_daily_snapshot.schema.json data/competitors/daily/file.csv
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: validate_csv_headers.py <schema.json> <file.csv>")
        return 2

    schema_path = Path(sys.argv[1])
    csv_path = Path(sys.argv[2])
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    required = schema.get("required_columns", [])

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        headers = next(reader, [])

    missing = [column for column in required if column not in headers]
    extra = [column for column in headers if column not in required]

    if missing:
        print(f"Missing columns: {', '.join(missing)}")
    if extra:
        print(f"Extra columns: {', '.join(extra)}")
    if not missing:
        print("CSV headers valid.")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
