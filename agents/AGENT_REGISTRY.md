# Hermes Agent Registry

Use this registry to decide whether an existing agent can own a task or whether Hermes should create a generated agent.

## Core Agents

- `hermes-master`: final decisions, prioritization, approval.
- `competitor-watcher`: daily competitor movement and view velocity.
- `pattern-analyst`: title, thumbnail, topic, and hook pattern extraction.
- `idea-strategist`: scored video ideas and pillar rotation.
- `script-writer`: long-form scripts and Shorts.
- `thumbnail-analyst`: thumbnail briefs, tests, and swipe-file lessons.
- `analytics-doctor`: CTR, AVD, conversion, and rescue actions.
- `memory-curator`: compression, context packs, durable memory updates.
- `safety-claims-checker`: medical risk, claim wording, and viewer safety.
- `auto-update-orchestrator`: repo self-improvement, delegated tasks, proposals, validation, commit, and push.

## Generated Agents

Generated agent specs live in `agents/generated/`.

Create one only when:

- a recurring task has a clear owner missing from the core list
- the task has stable inputs and outputs
- the new agent reduces repeated prompt complexity
- the agent has explicit boundaries and handoff rules

