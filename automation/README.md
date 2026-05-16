# Hermes Automation Layer

This folder gives Hermes a controlled way to update its own operating system.

## Folders

- `tasks/`: delegated work items for agents.
- `proposals/`: audit trail for system changes before or during implementation.
- `runs/`: optional logs from automated maintenance runs.

## How Hermes Should Use This

1. Read `automation/SELF_UPDATE_POLICY.md`.
2. Use `prompts/auto_update_orchestrator.md`.
3. Create a task file when work needs delegation.
4. Create a proposal file when changing prompts, schemas, scripts, memory, or agent behavior.
5. Run `python3 scripts/hermes_auto_update.py validate`.
6. Commit and push only after validation passes.

## Local CLI

Create a delegated task:

```bash
python3 scripts/hermes_auto_update.py new-task "Review week 2 CTR drops" --owner analytics-doctor --priority high
```

Create a generated agent spec:

```bash
python3 scripts/hermes_auto_update.py new-agent retention-doctor "Retention Doctor" --mission "Diagnose script retention problems and prescribe fixes."
```

Validate:

```bash
python3 scripts/hermes_auto_update.py validate
```

Commit and push:

```bash
python3 scripts/hermes_auto_update.py publish "Update Hermes automation layer" --push
```

