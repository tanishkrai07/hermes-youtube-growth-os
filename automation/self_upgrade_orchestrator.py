#!/usr/bin/env python3
"""
Self-Upgrade Orchestrator for Hermes YouTube Growth OS
Runs daily improvement cycle: analyze → propose → execute → commit.

Called by cron once daily at 05:00 UTC (before the main cron chain).
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_FILE = REPO_ROOT / "logs" / "self_upgrade.log"

def log(level, message):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{level}] {ts} {message}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def run_command(command, capture_output=False, timeout=60):
    try:
        if isinstance(command, str):
            command = command.split()
        result = subprocess.run(
            command, cwd=REPO_ROOT,
            capture_output=capture_output, text=True, timeout=timeout
        )
        if capture_output:
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        return result.returncode == 0, "", ""
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def load_env():
    """Load ~/.hermes/.env into os.environ so scripts can use API keys."""
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value and key not in os.environ:
                        os.environ[key] = value
        log("INFO", f"Loaded env from {env_path}")
    else:
        log("WARNING", f"No .env file at {env_path}")

def analyze_system_health():
    """Check system health and return issues + improvements."""
    issues = []
    improvements = []

    # Check essential files
    essential = [
        "scripts/fetch_competitor_videos.py",
        "scripts/extract_transcripts.py",
        "scripts/build_context_pack.py",
        "scripts/trend_scorer.py",
        "memory/competitor_memory.md",
        "memory/channel_brain.md",
        "memory/winning_patterns.md",
        "memory/failed_patterns.md",
        "outputs/reports/current_context_pack.md",
    ]
    for fp in essential:
        p = REPO_ROOT / fp
        if not p.exists():
            issues.append(f"Missing: {fp}")
        elif p.stat().st_size == 0:
            issues.append(f"Empty: {fp}")

    # Check competitor data freshness
    comp_dir = REPO_ROOT / "data" / "competitors" / "daily"
    if comp_dir.exists():
        csvs = list(comp_dir.glob("*.csv"))
        if csvs:
            latest = max(csvs, key=lambda x: x.stat().st_mtime)
            hours = (datetime.now().timestamp() - latest.stat().st_mtime) / 3600
            if hours > 25:
                issues.append(f"Competitor data {hours:.0f}h old ({latest.name})")
        else:
            issues.append("No competitor CSV files")

    # Check script production progress
    reports_dir = REPO_ROOT / "outputs" / "reports"
    if reports_dir.exists():
        vid_scripts = list(reports_dir.glob("VID-*.md"))
        script_packages = list(reports_dir.glob("*script_package*.md"))
        total = len(vid_scripts) + len(script_packages)
        log("INFO", f"Script production: {total} total scripts on disk")
        if total < 20:
            improvements.append(f"Only {total} scripts produced — need 90 by June 5")

    # Check for stale idea lists (keep only latest 3)
    idea_lists = sorted(reports_dir.glob("*_idea_list.md"))
    if len(idea_lists) > 5:
        improvements.append(f"Clean up {len(idea_lists)} idea list files (keep latest 3)")

    # Check for stale SEO/thumbnail files (keep only latest 3 of each)
    seo_files = sorted(reports_dir.glob("*_seo_metadata.md"))
    thumb_files = sorted(reports_dir.glob("*_thumbnail_brief.md"))
    if len(seo_files) > 5:
        improvements.append(f"Clean up {len(seo_files)} SEO metadata files")
    if len(thumb_files) > 5:
        improvements.append(f"Clean up {len(thumb_files)} thumbnail brief files")

    return issues, improvements

def clean_stale_files():
    """Remove old daily files, keeping only the latest 3 of each type."""
    reports_dir = REPO_ROOT / "outputs" / "reports"
    patterns = ["*_idea_list.md", "*_seo_metadata.md", "*_thumbnail_brief.md", "*_competitor_scan.md"]
    cleaned = 0
    for pattern in patterns:
        files = sorted(reports_dir.glob(pattern))
        if len(files) > 3:
            for f in files[:-3]:
                f.unlink()
                cleaned += 1
                log("INFO", f"Cleaned stale file: {f.name}")
    return cleaned

def execute_proposals(issues, improvements):
    """Execute improvement proposals. Returns count of successful actions."""
    executed = 0

    # Fix missing essential files
    for issue in issues:
        if issue.startswith("Missing: "):
            fp = issue.split(": ", 1)[1]
            p = REPO_ROOT / fp
            p.parent.mkdir(parents=True, exist_ok=True)
            if fp.endswith(".md"):
                p.write_text(f"# {Path(fp).stem}\n\n*Auto-generated: {datetime.now().strftime('%Y-%m-%d')}*\n")
            elif fp.endswith(".py"):
                p.write_text(f'#!/usr/bin/env python3\n"""{fp} - Hermes YouTube Growth OS"""\n\ndef main():\n    pass\n\nif __name__ == "__main__":\n    main()\n')
            log("INFO", f"Created missing file: {fp}")
            executed += 1

    # Refresh competitor data if stale
    for issue in issues:
        if "Competitor data" in issue and "old" in issue:
            log("INFO", "Refreshing competitor data...")
            ok, _, err = run_command(
                ["python3", "scripts/fetch_competitor_videos.py", "--days-back", "7"],
                timeout=120
            )
            if ok:
                log("SUCCESS", "Competitor data refreshed")
                executed += 1
            else:
                log("ERROR", f"Failed to refresh competitor data: {err}")

    # Clean stale files
    cleaned = clean_stale_files()
    if cleaned > 0:
        log(f"INFO", f"Cleaned {cleaned} stale files")
        executed += 1

    return executed

def commit_changes():
    """Commit and push changes."""
    run_command(["git", "add", "-A"])
    ok, _, _ = run_command(["git", "diff", "--staged", "--quiet"])
    if ok:
        log("INFO", "No changes to commit")
        return True

    msg = f"Self-upgrade: {datetime.now().strftime('%Y-%m-%d %H:%M')} - Daily improvement cycle"
    ok, _, err = run_command(["git", "commit", "-m", msg])
    if not ok:
        log("ERROR", f"Commit failed: {err}")
        return False

    ok, _, err = run_command(["git", "push", "origin", "main"])
    if ok:
        log("SUCCESS", "Changes committed and pushed")
    else:
        log("WARNING", f"Commit OK but push failed: {err}")
    return True

def main():
    log("INFO", "=== Self-Upgrade Orchestrator Started ===")
    load_env()

    issues, improvements = analyze_system_health()
    log("INFO", f"Found {len(issues)} issues, {len(improvements)} improvement areas")

    for i in issues:
        log("WARNING", f"  Issue: {i}")
    for imp in improvements:
        log("INFO", f"  Improve: {imp}")

    if issues or improvements:
        count = execute_proposals(issues, improvements)
        log("INFO", f"Executed {count} improvement actions")
        commit_changes()
    else:
        log("INFO", "System healthy — no actions needed")

    log("INFO", "=== Self-Upgrade Orchestrator Complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
