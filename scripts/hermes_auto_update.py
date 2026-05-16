#!/usr/bin/env python3
"""Utilities for Hermes self-updates.

This script does not call an AI model. It gives Hermes a predictable way to
create audit files, create generated agent specs, validate the repo, and publish
approved local changes.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def write_new(path: Path, content: str) -> None:
    if path.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {path.relative_to(ROOT)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Created {path.relative_to(ROOT)}")


def new_task(args: argparse.Namespace) -> None:
    task_id = f"{stamp()}-{slugify(args.title)}"
    path = ROOT / "automation" / "tasks" / f"{task_id}.md"
    source_files = "\n".join(f"  - {item}" for item in args.source_file) or "  - TBD"
    content = f"""---
id: {task_id}
created_at: "{now()}"
owner_agent: {args.owner}
priority: {args.priority}
status: open
---

# {args.title}

## Source Files

{source_files}

## Expected Output

{args.expected_output}

## Done Criteria

{args.done_criteria}

## Notes

{args.notes}
"""
    write_new(path, content)


def new_agent(args: argparse.Namespace) -> None:
    agent_id = slugify(args.agent_id)
    path = ROOT / "agents" / "generated" / f"{agent_id}.md"
    content = f"""---
id: {agent_id}
name: "{args.name}"
created_at: "{now()}"
---

# {args.name}

## Mission

{args.mission}

## Inputs

- Current context pack
- Relevant memory files
- Relevant task or proposal file

## Outputs

- Diagnosis or completed artifact
- Evidence used
- Recommended memory updates
- Handoff notes

## Boundaries

- Do not edit raw SOP files without explicit user approval.
- Do not make unsupported medical claims.
- Do not commit secrets or credentials.

## Handoff Rules

- Hand off medical claim wording to `safety-claims-checker`.
- Hand off durable learnings to `memory-curator`.
- Hand off repo-level changes to `auto-update-orchestrator`.
"""
    write_new(path, content)


def new_proposal(args: argparse.Namespace) -> None:
    proposal_id = f"{stamp()}-{slugify(args.title)}"
    path = ROOT / "automation" / "proposals" / f"{proposal_id}.md"
    files = "\n".join(f"  - {item}" for item in args.file) or "  - TBD"
    content = f"""---
id: {proposal_id}
created_at: "{now()}"
owner_agent: {args.owner}
change_type: {args.change_type}
status: proposed
---

# {args.title}

## Reason

{args.reason}

## Files Affected

{files}

## Evidence

{args.evidence}

## Validation Plan

{args.validation_plan}

## Rollback Note

{args.rollback_note}
"""
    write_new(path, content)


def validate(_: argparse.Namespace) -> None:
    run(["python3", "scripts/build_context_pack.py"])
    run([
        "python3",
        "scripts/validate_csv_headers.py",
        "schemas/video_pipeline.schema.json",
        "data/video_pipeline/first_10_tracker.csv",
    ])
    print("Hermes validation passed.")


def publish(args: argparse.Namespace) -> None:
    validate(args)
    run(["git", "add", "."])
    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not status:
        print("No changes to publish.")
        return
    run(["git", "commit", "-m", args.message])
    if args.push:
        run(["git", "push"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes self-update utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    task = subparsers.add_parser("new-task", help="Create a delegated task file")
    task.add_argument("title")
    task.add_argument("--owner", default="auto-update-orchestrator")
    task.add_argument("--priority", choices=["low", "medium", "high", "urgent"], default="medium")
    task.add_argument("--source-file", action="append", default=[])
    task.add_argument("--expected-output", default="A production-ready artifact or clear recommendation.")
    task.add_argument("--done-criteria", default="The owner agent has produced the expected output with evidence.")
    task.add_argument("--notes", default="None.")
    task.set_defaults(func=new_task)

    agent = subparsers.add_parser("new-agent", help="Create a generated agent spec")
    agent.add_argument("agent_id")
    agent.add_argument("name")
    agent.add_argument("--mission", required=True)
    agent.set_defaults(func=new_agent)

    proposal = subparsers.add_parser("new-proposal", help="Create a system change proposal")
    proposal.add_argument("title")
    proposal.add_argument("--owner", default="auto-update-orchestrator")
    proposal.add_argument("--change-type", choices=["prompt", "memory", "schema", "script", "agent", "data_template", "docs", "workflow"], default="workflow")
    proposal.add_argument("--file", action="append", default=[])
    proposal.add_argument("--reason", default="Improve repeatability and reduce manual work.")
    proposal.add_argument("--evidence", default="User requested self-update capability.")
    proposal.add_argument("--validation-plan", default="Run python3 scripts/hermes_auto_update.py validate.")
    proposal.add_argument("--rollback-note", default="Revert the commit that introduced this proposal if it fails.")
    proposal.set_defaults(func=new_proposal)

    check = subparsers.add_parser("validate", help="Run Hermes validation checks")
    check.set_defaults(func=validate)

    publish_parser = subparsers.add_parser("publish", help="Validate, commit, and optionally push")
    publish_parser.add_argument("message")
    publish_parser.add_argument("--push", action="store_true")
    publish_parser.set_defaults(func=publish)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
