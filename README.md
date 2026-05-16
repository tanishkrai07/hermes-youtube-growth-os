# Hermes YouTube Growth OS

Repo-backed operating system for the Dr. Victor Kane elder-health YouTube channel.

Goal: use Hermes agents to grow the channel toward 100K subscribers in 90 days through daily competitor monitoring, data-backed idea generation, script production, thumbnail learning, and analytics-driven improvement.

## Core Principle

Hermes should never load all raw files into context by default. Raw data lives in the repo, but active work uses compact memory layers:

1. Raw archive: SOPs, transcripts, competitor exports, YouTube dashboard exports.
2. Daily digests: short summaries of what changed today.
3. Weekly strategy memory: what is working, what failed, and what to do next.
4. Current context pack: the smallest possible prompt payload for Hermes before each task.

## Recommended GitHub Setup

- Create this as a **private GitHub repo**.
- Track SOPs, prompts, CSV/JSON exports, scripts, and thumbnail reference images.
- Do not store secrets, API keys, Telegram bot tokens, raw video files, or huge render outputs in git.
- Use Git LFS or cloud storage for large thumbnail/video assets if needed.

## Folder Map

- `knowledge/raw_initial_upload/`: original files already provided to Codex.
- `memory/`: compact long-term memory Hermes should read often.
- `data/competitors/`: daily and weekly competitor snapshots.
- `data/channel_analytics/`: your own dashboard exports by day/week/month.
- `data/thumbnails/`: thumbnail swipe file, design metadata, and analysis notes.
- `data/video_pipeline/`: per-video production status records.
- `agents/`: role definitions for the multi-agent system.
- `automation/`: self-update workflow, task queue, and change proposals.
- `prompts/`: reusable prompts for Telegram/Hermes runs.
- `schemas/`: expected CSV/JSON shapes for clean ingestion.
- `scripts/`: local utilities to build context packs and validate data.
- `outputs/`: generated context packs and reports. Most generated reports can be recreated.

## Daily Operating Loop

1. Add competitor observations or exports to `data/competitors/daily/`.
2. Add any thumbnail screenshots to `data/thumbnails/swipe_file/`.
3. Run `python3 scripts/build_context_pack.py`.
4. Send `outputs/context_packs/current_context_pack.md` to Hermes before important tasks.
5. Ask Hermes to run `prompts/daily_competitor_review.md`.
6. Save Hermes output as a dated report under `outputs/reports/`.
7. If the insight matters long-term, update `memory/channel_brain.md` and `memory/competitor_memory.md`.

## Auto-Update Loop

Hermes can evolve the operating system by using `prompts/auto_update_orchestrator.md` and the files under `automation/`.

Allowed changes:

- Create new agent specs under `agents/generated/`.
- Create delegated task files under `automation/tasks/`.
- Propose prompt, memory, schema, and script improvements.
- Create new support files when a recurring workflow needs structure.
- Run validation before committing or pushing.

Guardrails:

- Raw SOPs in `knowledge/raw_initial_upload/` are read-only unless you explicitly approve changes.
- Medical claims must pass the Safety and Claims Checker.
- Every self-update must leave a proposal or task record.
- Push only after validation passes.

## Weekly Operating Loop

1. Add your YouTube Studio weekly export to `data/channel_analytics/weekly/`.
2. Run the weekly analytics prompt.
3. Update:
   - `memory/winning_patterns.md`
   - `memory/failed_patterns.md`
   - `memory/next_actions.md`
4. Refresh the next 10 video queue.

## Non-Negotiable Channel Rules

- Use **Dr. Victor Kane** in every title, script, description, thumbnail brief, and metadata package.
- Never suggest an idea below 15/20.
- Long-form videos target 14-16 minutes.
- Shorts target 45-60 seconds.
- Every thumbnail gets two test versions.
- Every fear-based video must close with practical hope.
- Medication topics must say: "Talk to your doctor and specifically ask..." instead of telling viewers to stop prescriptions.
