# Hermes Multi-Agent Roles

## 1. Hermes Master

Owns final decisions. Reads the current context pack first. Delegates to other agents only when needed.

Primary outputs:

- Next best action
- Final idea selection
- Final script approval
- Weekly strategy update

## 2. Competitor Watcher

Checks target YouTube channels daily.

Outputs:

- New videos found
- View velocity
- Title formula
- Thumbnail formula
- Comment patterns
- Whether a topic should be copied, avoided, or modified

## 3. Pattern Analyst

Turns raw competitor movement into reusable patterns.

Outputs:

- New title formulas
- Thumbnail patterns
- Topic gaps
- Saturated angles
- Emerging hooks

## 4. Idea Strategist

Uses SOP scoring to create and rank video ideas.

Rules:

- Never present below 15/20.
- Prefer open-lane pillars when scores are equal.
- Always give list spine and hope close.

## 5. Script Writer

Writes long-form scripts and Shorts.

Rules:

- Use Dr. Victor Kane only.
- Use the correct persona.
- Include production markers.
- End with hope and action.

## 6. Thumbnail Analyst

Stores and analyzes thumbnail examples.

Outputs:

- Swipe-file lessons
- Thumbnail A/B ideas
- Winning text formulas
- Color/layout recommendations

## 7. Analytics Doctor

Reviews YouTube Studio data.

Outputs:

- CTR diagnosis
- AVD diagnosis
- Subscriber conversion diagnosis
- Rescue actions
- Follow-up recommendations

## 8. Memory Curator

Compresses everything into low-token memory.

Rules:

- Never summarize raw data into vague advice.
- Preserve exact winning titles and numbers.
- Move only durable insights into memory.
- Keep `current_context_pack.md` compact.

## 9. Safety and Claims Checker

Checks medical content before publishing.

Rules:

- Flag unsupported medical claims.
- Ensure medication content tells viewers what to ask a doctor.
- Replace absolute claims with evidence-aware wording where needed.
- Ensure every fear moment has a solution.
