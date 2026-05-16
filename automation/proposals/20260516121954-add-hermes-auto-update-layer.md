---
id: 20260516121954-add-hermes-auto-update-layer
created_at: "2026-05-16 12:19:54"
owner_agent: auto-update-orchestrator
change_type: workflow
status: proposed
---

# Add Hermes auto-update layer

## Reason

Enable Hermes agents to delegate tasks, create generated agents, propose system changes, validate updates, and publish approved repo improvements.

## Files Affected

  - automation/SELF_UPDATE_POLICY.md
  - prompts/auto_update_orchestrator.md
  - scripts/hermes_auto_update.py

## Evidence

User requested auto update where Hermes agents update themselves, delegate tasks, make new agents, make new files, and push changes.

## Validation Plan

Run python3 scripts/hermes_auto_update.py validate.

## Rollback Note

Revert the commit that introduced this proposal if it fails.
