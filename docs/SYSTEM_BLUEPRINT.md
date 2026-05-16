# Hermes System Blueprint

## Mission

Build a repo-backed, multi-agent content machine for the Dr. Victor Kane elder-health YouTube channel.

The system should:

- Monitor competitors daily.
- Turn competitor movement into scored video ideas.
- Generate scripts, Shorts, thumbnails, SEO, and upload checklists from SOPs.
- Learn from the channel dashboard weekly and monthly.
- Preserve memory without wasting context.
- Improve the system itself through controlled reflection loops.

## Memory Architecture

### Layer 1: Raw Archive

Location:

- `knowledge/raw_initial_upload/`
- `data/competitors/`
- `data/channel_analytics/`
- `data/thumbnails/`

Purpose: preserve source truth. Hermes should not read this entire layer unless doing a deep audit.

### Layer 2: Structured Logs

Location:

- `memory/competitor_memory.md`
- `memory/thumbnail_memory.csv`
- `memory/video_idea_bank.csv`
- `memory/analytics_memory.md`

Purpose: keep searchable summaries of raw data.

### Layer 3: Strategic Brain

Location:

- `memory/channel_brain.md`
- `memory/winning_patterns.md`
- `memory/failed_patterns.md`
- `memory/next_actions.md`

Purpose: tell Hermes what the channel currently believes.

### Layer 4: Current Context Pack

Location:

- `outputs/context_packs/current_context_pack.md`

Purpose: lowest-token working memory. This is the file Hermes should receive before doing most tasks.

Target size: under 8,000 words.

## Daily Agent Flow

1. Competitor Watcher checks target channels and records new uploads, titles, thumbnails, view velocity, and comments.
2. Pattern Analyst extracts what changed: title formulas, thumbnail patterns, emerging topics, repeated hooks.
3. Idea Strategist maps findings to the 8 channel pillars and scores ideas.
4. Memory Curator compresses useful findings into memory files.
5. Hermes Master decides whether to create a follow-up idea, script, thumbnail test, or wait.

## Weekly Agent Flow

1. Analytics Analyst reviews CTR, AVD, subscriber conversion, comments, and first 48-hour performance.
2. Strategist compares your results against competitor activity.
3. Thumbnail Analyst updates the swipe file and winner/loser patterns.
4. Script Doctor identifies retention problems and fixes future hooks.
5. Memory Curator updates the strategic brain.

## Self-Improvement Loop

Run weekly, not constantly.

Hermes should ask:

- What did we predict this week?
- What happened?
- Which SOP rule helped?
- Which SOP rule failed or needs adjustment?
- Which competitor signal did we miss?
- What should change in prompts, memory, or scoring?

Rule: Hermes may propose changes to prompts and SOP summaries, but raw SOP files should remain unchanged unless you approve.

## Token Discipline

Hermes should prefer this order:

1. Read `current_context_pack.md`.
2. Read only the specific memory file needed.
3. Read raw daily/weekly data only when the memory layer is insufficient.
4. Never load full transcripts unless doing script-style analysis.

For scripts, use:

- SOP summary
- one or two matching transcript excerpts
- target idea brief
- relevant safety notes

Do not load all transcripts to write one script.
