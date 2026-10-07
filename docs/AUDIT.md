# V0.1 adversarial audit

## Findings and dispositions

| Severity | Finding | Disposition |
|---|---|---|
| Critical | `propose` accepted JOY/MUST, so AI could claim human motivation before confirmation. | Fixed in schema v2. Motivation is unknown at proposal and must be explicitly supplied by `confirm`. |
| High | A Hook that did not bite had no terminal state, causing survivor bias and losing user agency. | Added `USER_REJECTED`; it never becomes a positive learning signal. |
| High | Entry objects accepted unknown fields, allowing an accidental aggregate score or undeclared data to enter the canonical store. | Entry fields are now closed and validated exactly. |
| Medium | IDs and timestamps were not validated. | UUID and timezone-aware ISO-8601 validation added. |
| Medium | Duplicate impact flags silently overwrote each other. | Duplicate axes now fail closed. |
| Medium | There was no operational integrity report. | Added read-only `audit`, reporting state counts, MUST-only count, and learnable count without ranking or a composite score. |
| Low | Atomic replacement did not explicitly flush data before replacement. | Added flush and filesystem sync before replacement. |

## Deliberately not added

- Recommendation ranking or automated next-Hook selection
- Vector database, event database, queue, cache, or user profile database
- Composite QOL score
- Streaks, engagement metrics, or notification loops
- Automatic inference of JOY/MUST from conversation

These remain outside the minimal closed loop and require separate evidence before expansion.
