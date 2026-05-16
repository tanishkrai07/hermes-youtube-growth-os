# Auto-Update Orchestrator Prompt

Use this when Hermes is asked to improve, maintain, or evolve the repo itself.

## Inputs

Read in this order:

1. `outputs/context_packs/current_context_pack.md`
2. `docs/SYSTEM_BLUEPRINT.md`
3. `automation/SELF_UPDATE_POLICY.md`
4. `agents/AGENT_REGISTRY.md`
5. The specific prompt, memory, schema, script, or task file involved

## Decision Flow

1. State the user goal in one sentence.
2. Identify the owner agent.
3. Decide whether the work is:
   - memory update
   - prompt update
   - schema update
   - new agent
   - delegated task
   - new script/template/file
   - validation or publishing
4. Create or update the smallest useful file.
5. Add a proposal record when the change affects strategy, prompts, schemas, scripts, or agent behavior.
6. Run validation.
7. Commit and push only when validation passes and repository access is available.

## Delegation Rules

- Delegate recurring monitoring to specialized agents.
- Delegate medical risk checks to Safety and Claims Checker.
- Delegate compression and file hygiene to Memory Curator.
- Create a new generated agent only when no existing role clearly owns the repeated task.
- Every delegated task needs an owner, expected output, source files, due cadence, and done criteria.

## Output Format

Return:

1. Files changed.
2. Agents involved.
3. Tasks created or completed.
4. Validation result.
5. Commit and push status.
6. Next recommended automation.

