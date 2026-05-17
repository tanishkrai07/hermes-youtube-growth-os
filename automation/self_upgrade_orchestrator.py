#!/usr/bin/env python3
"""
Self-Upgrade Orchestrator for Hermes YouTube Growth OS
Runs continuous improvement cycles to enhance the system's capabilities
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def log(level, message):
    """Log messages with timestamp"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{level}] {ts} {message}", flush=True)

def run_command(command, capture_output=False):
    """Run a shell command"""
    try:
        if capture_output:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=REPO_ROOT, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        else:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=REPO_ROOT, 
                timeout=30
            )
            return result.returncode == 0, "", ""
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def get_git_status():
    """Get current git status"""
    success, stdout, stderr = run_command("git status --porcelain", capture_output=True)
    if success:
        return stdout.strip()
    return ""

def get_current_branch():
    """Get current git branch"""
    success, stdout, stderr = run_command("git rev-parse --abbrev-ref HEAD", capture_output=True)
    if success:
        return stdout.strip()
    return "unknown"

def analyze_system_health():
    """Analyze the overall system health and identify improvement areas"""
    log("INFO", "Analyzing system health...")
    
    issues = []
    improvements = []
    
    # Check if essential files exist
    essential_files = [
        "scripts/fetch_competitor_videos.py",
        "scripts/extract_transcripts.py", 
        "scripts/build_context_pack.py",
        "scripts/trend_scorer.py",
        "memory/competitor_memory.md",
        "memory/channel_brain.md",
        "prompts/daily_competitor_review.md",
        "data/competitors/daily/2026-05-17_competitors.csv"
    ]
    
    for file_path in essential_files:
        full_path = REPO_ROOT / file_path
        if not full_path.exists():
            issues.append(f"Missing essential file: {file_path}")
        elif full_path.stat().st_size == 0:
            issues.append(f"Empty essential file: {file_path}")
    
    # Check for recent competitor data
    competitor_dir = REPO_ROOT / "data" / "competitors" / "daily"
    if competitor_dir.exists():
        csv_files = list(competitor_dir.glob("*.csv"))
        if csv_files:
            latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
            hours_old = (datetime.now().timestamp() - latest_file.stat().st_mtime) / 3600
            if hours_old > 25:  # More than a day old
                issues.append(f"Competitor data is {hours_old:.1f} hours old")
            else:
                log("INFO", f"Competitor data is fresh ({hours_old:.1f} hours old)")
        else:
            issues.append("No competitor CSV files found")
    else:
        issues.append("Competitor data directory missing")
    
    # Check for video pipeline scripts
    video_pipeline_dir = REPO_ROOT / "data" / "video_pipeline"
    if video_pipeline_dir.exists():
        video_files = list(video_pipeline_dir.glob("*.md"))
        log("INFO", f"Found {len(video_files)} video pipeline scripts")
        if len(video_files) == 0:
            improvements.append("No video scripts created yet - ready for content generation")
    else:
        issues.append("Video pipeline directory missing")
    
    # Check automation tasks
    automation_tasks_dir = REPO_ROOT / "automation" / "tasks"
    if automation_tasks_dir.exists():
        task_files = list(automation_tasks_dir.glob("*.md"))
        log("INFO", f"Found {len(task_files)} automation tasks")
    else:
        issues.append("Automation tasks directory missing")
    
    # Check memory files for update opportunities
    memory_dir = REPO_ROOT / "memory"
    if memory_dir.exists():
        memory_files = list(memory_dir.glob("*.md"))
        log("INFO", f"Found {len(memory_files)} memory files")
        
        # Check if competitor memory needs updating based on recent data
        competitor_memory = memory_dir / "competitor_memory.md"
        if competitor_memory.exists():
            # Check if it's been updated recently (within last hour)
            hours_since_update = (datetime.now().timestamp() - competitor_memory.stat().st_mtime) / 3600
            if hours_since_update > 2:
                improvements.append(f"Competitor memory could be updated ({hours_since_update:.1f} hours since last update)")
    
    return issues, improvements

def generate_improvement_proposals(issues, improvements):
    """Generate specific improvement proposals based on analysis"""
    proposals = []
    
    # Priority 1: Fix critical issues
    for issue in issues:
        if "Missing essential file" in issue:
            proposals.append({
                "title": f"Fix missing file: {issue.split(': ')[1]}",
                "description": f"Create or restore the missing essential file: {issue.split(': ')[1]}",
                "priority": "urgent",
                "type": "file_creation"
            })
        elif "Empty essential file" in issue:
            proposals.append({
                "title": f"Populate empty file: {issue.split(': ')[1]}",
                "description": f"Fill the empty essential file with appropriate content: {issue.split(': ')[1]}",
                "priority": "high",
                "type": "file_edit"
            })
        elif "Competitor data is" in issue and "hours old" in issue:
            proposals.append({
                "title": "Refresh competitor data",
                "description": "Run competitor video fetcher to get fresh data",
                "priority": "high",
                "type": "data_refresh"
            })
    
    # Priority 2: Implement improvements
    for improvement in improvements:
        if "video scripts created yet" in improvement:
            proposals.append({
                "title": "Generate video scripts from competitor analysis",
                "description": "Use today's competitor data to generate high-potential video concepts",
                "priority": "high",
                "type": "content_generation"
            })
        elif "Competitor memory could be updated" in improvement:
            proposals.append({
                "title": "Update competitor memory with latest insights",
                "description": "Analyze recent competitor data and update memory files with new patterns",
                "priority": "medium",
                "type": "memory_update"
            })
    
    # Priority 3: System enhancements
    proposals.extend([
        {
            "title": "Enhance trend scoring algorithm",
            "description": "Improve the trend scorer to better identify emerging opportunities",
            "priority": "medium",
            "type": "algorithm_improvement"
        },
        {
            "title": "Optimize context pack generation",
            "description": "Make context packs more compact and relevant for Hermes decision making",
            "priority": "low",
            "type": "optimization"
        },
        {
            "title": "Create video production checklist",
            "description": "Generate a standardized checklist for video production quality assurance",
            "priority": "low",
            "type": "process_improvement"
        }
    ])
    
    return proposals

def execute_proposal(proposal):
    """Execute a specific improvement proposal"""
    log("INFO", f"Executing proposal: {proposal['title']}")
    
    try:
        if proposal["type"] == "data_refresh":
            # Refresh competitor data
            success, stdout, stderr = run_command(
                "python3 scripts/fetch_competitor_videos.py --days-back 7"
            )
            if success:
                log("SUCCESS", "Competitor data refreshed")
                return True
            else:
                log("ERROR", f"Failed to refresh competitor data: {stderr}")
                return False
                
        elif proposal["type"] == "content_generation":
            # Generate video scripts from competitor analysis
            success, stdout, stderr = run_command(
                "python3 scripts/trend_scorer.py --generate-ideas"
            )
            if success:
                log("SUCCESS", "Video ideas generated from trend analysis")
                return True
            else:
                log("ERROR", f"Failed to generate video ideas: {stderr}")
                return False
                
        elif proposal["type"] == "memory_update":
            # Update competitor memory
            success, stdout, stderr = run_command(
                "python3 scripts/build_context_pack.py"
            )
            if success:
                # Run the daily competitor review to update memory
                success2, stdout2, stderr2 = run_command(
                    'echo "Use the daily competitor review prompt to analyze today\'s competitor data and provide insights for content creation." | hermes chat'
                )
                if success2:
                    log("SUCCESS", "Competitor memory updated via daily review")
                    return True
                else:
                    log("WARNING", f"Context pack built but memory update had issues: {stderr2}")
                    return True  # Context pack built is still success
            else:
                log("ERROR", f"Failed to build context pack: {stderr}")
                return False
                
        elif proposal["type"] == "file_creation":
            # Create missing file
            file_path = proposal["description"].split(": ")[1] if ": " in proposal["description"] else proposal["title"]
            full_path = REPO_ROOT / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create basic content based on file type
            if file_path.endswith(".py"):
                content = f'''#!/usr/bin/env python3
"""
{file_path} - Auto-generated component of Hermes YouTube Growth OS
"""
def main():
    print("Component {file_path} initialized")
    return 0

if __name__ == "__main__":
    main()
'''
            elif file_path.endswith(".md"):
                content = f'''# {file_path}

Auto-generated file for Hermes YouTube Growth OS

*Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
'''
            else:
                content = f"# Auto-generated file\n\nCreated: {datetime.now().isoformat()}\n"
            
            full_path.write_text(content)
            log("SUCCESS", f"Created file: {file_path}")
            return True
            
        elif proposal["type"] == "file_edit":
            # Populate empty file
            file_path = proposal["description"].split(": ")[1] if ": " in proposal["description"] else proposal["title"]
            full_path = REPO_ROOT / file_path
            
            if full_path.exists() and full_path.stat().st_size == 0:
                # Add basic content based on file type
                if file_path.endswith(".md"):
                    content = f'''# {file_path}

*Initialized: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

This file has been populated as part of the self-upgrade process.
'''
                elif file_path.endswith(".py"):
                    content = f'''#!/usr/bin/env python3
"""
{file_path} - Component of Hermes YouTube Growth OS
*Initialized: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

def main():
    """Main entry point"""
    print("Component initialized")
    return 0

if __name__ == "__main__":
    main()
'''
                else:
                    content = f"# {file_path}\n\n*Initialized: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
                
                full_path.write_text(content)
                log("SUCCESS", f"Populated file: {file_path}")
                return True
            else:
                log("WARNING", f"File {file_path} is not empty or doesn't exist")
                return False
                
        else:
            # For other types, create a task file for manual follow-up
            task_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{proposal['title'].lower().replace(' ', '-')}"
            task_path = REPO_ROOT / "automation" / "tasks" / f"{task_id}.md"
            
            task_content = f"""---
id: {task_id}
created_at: "{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
owner_agent: self-upgrade-orchestrator
priority: {proposal['priority']}
status: open
---

# {proposal['title']}

## Description
{proposal['description']}

## Type
{proposal['type']}

## Priority
{proposal['priority']}

## Notes
Auto-generated by self-upgrade orchestrator. Requires manual implementation.
"""
            
            task_path.write_text(task_content)
            log("SUCCESS", f"Created task file for manual follow-up: {task_path.name}")
            return True
            
    except Exception as e:
        log("ERROR", f"Failed to execute proposal {proposal['title']}: {str(e)}")
        return False

def commit_changes():
    """Commit any changes made during the upgrade cycle"""
    success, stdout, stderr = run_command("git add .", capture_output=True)
    if not success:
        log("ERROR", f"Failed to git add: {stderr}")
        return False
    
    # Check if there are changes to commit
    success, stdout, stderr = run_command("git diff --staged --quiet", capture_output=True)
    if success:  # No changes (exit code 0 means no differences)
        log("INFO", "No changes to commit")
        return True
    
    # There are changes, create commit
    commit_message = f"Self-upgrade: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Continuous improvement cycle"
    success, stdout, stderr = run_command(f'git commit -m "{commit_message}"', capture_output=True)
    if success:
        log("SUCCESS", f"Committed changes: {commit_message}")
        return True
    else:
        log("ERROR", f"Failed to commit: {stderr}")
        return False

def main():
    """Main self-upgrade orchestrator loop"""
    log("INFO", "=== Hermes Self-Upgrade Orchestrator Started ===")
    log("INFO", f"Current branch: {get_current_branch()}")
    
    # Analyze system health
    issues, improvements = analyze_system_health()
    
    log("INFO", f"Found {len(issues)} issues and {len(improvements)} improvement areas")
    
    if issues:
        log("WARNING", "Issues detected:")
        for issue in issues:
            log("WARNING", f"  - {issue}")
    
    if improvements:
        log("INFO", "Improvement opportunities:")
        for improvement in improvements:
            log("INFO", f"  - {improvement}")
    
    # Generate and execute proposals
    proposals = generate_improvement_proposals(issues, improvements)
    log("INFO", f"Generated {len(proposals)} improvement proposals")
    
    executed_count = 0
    for proposal in proposals:
        if execute_proposal(proposal):
            executed_count += 1
            log("INFO", f"✓ Executed: {proposal['title']}")
        else:
            log("ERROR", f"✗ Failed: {proposal['title']}")
    
    log("INFO", f"Executed {executed_count}/{len(proposals)} proposals")
    
    # Commit changes if any were made
    if executed_count > 0:
        if commit_changes():
            log("SUCCESS", "Changes committed successfully")
        else:
            log("ERROR", "Failed to commit changes")
    else:
        log("INFO", "No changes to commit")
    
    log("INFO", "=== Hermes Self-Upgrade Orchestrator Cycle Complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())