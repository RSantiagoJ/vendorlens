# Context Bundle Mapping

This folder contains runtime-ready context files consumed by agents.

## Why this exists

The files in `context/` are human working notes.
The files here are distilled, stable inputs for agent prompts and retrieval.

Using one normalized bundle prevents prompt drift across agents.

## Source mapping

- `context/policy_notes.md` + `context/contract_terms.md` -> `policy.txt`
- `context/rfp_criteria.md` -> `rfp_criteria.txt`
- RFP criteria + scoring standards -> `scoring_rubric.txt`

## Update protocol

When source notes change:

1. Update corresponding file(s) in `context/`.
2. Rebuild the distilled file(s) in this folder.
3. Keep thresholds and requirements explicit (numbers, deadlines, policy triggers).
4. Run the Day 1 smoke check to verify retrieval still passes.
5. Commit source note change and bundle change together.

## Agent usage

- Risk logic reads `policy.txt`.
- Scoring logic reads `rfp_criteria.txt` and `scoring_rubric.txt`.
- Any policy-aware extraction should reference these files instead of hardcoded text.
