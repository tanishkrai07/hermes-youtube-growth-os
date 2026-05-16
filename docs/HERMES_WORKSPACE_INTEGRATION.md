# Hermes Workspace Integration

Use this guide to connect your EC2 Hermes setup, Hermes Workspace, Telegram bot, and this GitHub repo into one operating system.

## 1. Clone The Repo On EC2

SSH into your EC2 server and place the repo somewhere stable:

```bash
mkdir -p ~/workspaces
cd ~/workspaces
git clone https://github.com/tanishkrai07/hermes-youtube-growth-os.git
cd hermes-youtube-growth-os
python3 scripts/hermes_auto_update.py validate
```

Expected result:

```text
Hermes validation passed.
```

## 2. Add Repo Paths To Hermes Env

Edit your Hermes env file:

```bash
nano ~/.hermes/.env
```

Add these non-secret workspace settings:

```bash
HERMES_PROJECT_ROOT="$HOME/workspaces/hermes-youtube-growth-os"
HERMES_PROJECT_NAME="Hermes YouTube Growth OS"
HERMES_GITHUB_REPO="https://github.com/tanishkrai07/hermes-youtube-growth-os.git"
HERMES_CONTEXT_PACK="$HOME/workspaces/hermes-youtube-growth-os/outputs/context_packs/current_context_pack.md"
HERMES_MASTER_PROMPT="$HOME/workspaces/hermes-youtube-growth-os/prompts/HERMES_MASTER_SYSTEM_PROMPT.md"
HERMES_AUTO_UPDATE_PROMPT="$HOME/workspaces/hermes-youtube-growth-os/prompts/auto_update_orchestrator.md"
HERMES_AGENT_REGISTRY="$HOME/workspaces/hermes-youtube-growth-os/agents/AGENT_REGISTRY.md"
HERMES_SELF_UPDATE_POLICY="$HOME/workspaces/hermes-youtube-growth-os/automation/SELF_UPDATE_POLICY.md"
SEARXNG_BASE_URL="http://127.0.0.1:8080"
```

Keep secrets such as Telegram, Tavily, Firecrawl, OpenRouter, and YouTube keys in the same `.env`, but never commit them to this repo.

Restart Hermes Gateway after editing:

```bash
sudo systemctl restart hermes-gateway
sudo systemctl status hermes-gateway --no-pager
```

## 3. Configure Hermes Workspace Instructions

In Hermes Workspace project instructions, paste or reference this stack:

```text
You are Hermes for the Dr. Victor Kane YouTube Growth OS.

Before most tasks:
1. Read $HERMES_CONTEXT_PACK.
2. Follow $HERMES_MASTER_PROMPT.
3. Use $HERMES_AGENT_REGISTRY for delegation.
4. Use $HERMES_SELF_UPDATE_POLICY before changing repo files.
5. Use $HERMES_AUTO_UPDATE_PROMPT for system improvements.

Repo root:
$HERMES_PROJECT_ROOT

Default validation:
python3 scripts/hermes_auto_update.py validate

Default publish path:
git pull --rebase
python3 scripts/hermes_auto_update.py validate
git add .
git commit -m "<short useful message>"
git push
```

If Hermes Workspace supports file attachments or project knowledge, add these files first:

- `prompts/HERMES_MASTER_SYSTEM_PROMPT.md`
- `prompts/auto_update_orchestrator.md`
- `automation/SELF_UPDATE_POLICY.md`
- `agents/AGENT_REGISTRY.md`
- `docs/SYSTEM_BLUEPRINT.md`
- `outputs/context_packs/current_context_pack.md`

## 4. Bootstrap Hermes In Telegram

Send this once in Telegram:

```text
Load the Hermes YouTube Growth OS workspace.

Repo root: ~/workspaces/hermes-youtube-growth-os

Read:
- prompts/HERMES_MASTER_SYSTEM_PROMPT.md
- agents/AGENT_REGISTRY.md
- automation/SELF_UPDATE_POLICY.md
- prompts/auto_update_orchestrator.md
- outputs/context_packs/current_context_pack.md

Confirm:
1. Which agent roles are available.
2. Which APIs/tools are configured.
3. Whether validation passes.
4. What the next missing automation is.
```

## 5. Give Hermes Safe Repo Powers

Hermes should use these commands for repo work:

```bash
cd "$HERMES_PROJECT_ROOT"
git pull --rebase
python3 scripts/build_context_pack.py
python3 scripts/hermes_auto_update.py validate
```

For a delegated task:

```bash
python3 scripts/hermes_auto_update.py new-task "Daily competitor report" \
  --owner competitor-watcher \
  --priority high \
  --source-file data/competitors/daily
```

For a new generated agent:

```bash
python3 scripts/hermes_auto_update.py new-agent retention-doctor "Retention Doctor" \
  --mission "Diagnose retention problems in scripts and suggest stronger hooks, open loops, and pacing fixes."
```

For an audit proposal:

```bash
python3 scripts/hermes_auto_update.py new-proposal "Improve daily competitor workflow" \
  --owner auto-update-orchestrator \
  --change-type workflow \
  --file prompts/daily_competitor_review.md
```

For publishing approved changes:

```bash
python3 scripts/hermes_auto_update.py publish "Update Hermes workspace automation" --push
```

## 6. Connect Existing Tools

Hermes should route work like this:

```text
YouTube Data API
  -> competitor video metadata, channel stats, upload detection

Tavily
  -> AI-native web research and trend discovery

Firecrawl
  -> structured extraction from pages and competitor websites

SearXNG
  -> fallback search through http://127.0.0.1:8080

OpenRouter
  -> model routing for research, scripts, and analysis

Git repo
  -> memory, prompts, task files, generated agents, reports

Telegram
  -> command interface from phone
```

## 7. Recommended First Commands

Ask Hermes:

```text
Run a workspace health check for Hermes YouTube Growth OS.
Validate the repo, list configured tools, identify missing API access, and create tasks for anything not working.
```

Then:

```text
Create the first automated daily competitor monitoring task for 20 channels.
Use the auto-update policy. Save the delegated task in automation/tasks and push the repo after validation.
```

## 8. Operating Rule

Hermes can create files, agents, tasks, reports, and proposals, but raw SOPs stay read-only unless you explicitly approve changes.

