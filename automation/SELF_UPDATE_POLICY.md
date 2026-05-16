# Self-Update Policy

Hermes may improve this repo, but every autonomous change must be structured, inspectable, and reversible.

## Allowed

- Add or revise prompts when repeated output quality issues appear.
- Add memory updates supported by exact evidence.
- Add schemas and templates for recurring data.
- Add scripts that reduce manual work.
- Create generated agent specs under `agents/generated/`.
- Create delegated task files under `automation/tasks/`.
- Create proposal files under `automation/proposals/`.
- Rebuild context packs.
- Commit and push after validation passes.

## Restricted

- Raw SOP files in `knowledge/raw_initial_upload/` are read-only unless the user explicitly approves.
- Do not store secrets, API keys, cookies, session files, or credentials.
- Do not commit raw long-form video renders or large production media.
- Do not change medical advice rules without Safety and Claims Checker approval.
- Do not delete source evidence unless the user explicitly asks.

## Required Audit Trail

Every system-level change should record:

- date
- owner agent
- reason
- files changed or proposed
- source evidence
- validation performed
- rollback note

## Validation Gate

Before push, run:

```bash
python3 scripts/hermes_auto_update.py validate
```

If validation fails, fix the failure or leave the change unpushed with a clear note.

