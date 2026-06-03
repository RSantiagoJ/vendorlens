# Context Bundle Mapping

This folder contains runtime-ready context files consumed by agents.

## Why this exists

The files here are distilled, stable inputs for agent prompts and retrieval.
They are intentionally formatted for machine consumption (consistent headings,
explicit thresholds, and unambiguous policy rules).

Using one normalized bundle prevents prompt drift across agents.

## Source mapping

The files here are the authoritative source for agent context. The upstream
source notes (policy_notes.md, rfp_criteria.md, contract_terms.md) are kept
by Ricardo outside the repo. The `_lms` suffix on criteria and rubric files
signals which procurement they belong to — this naming pattern allows multiple
procurement bundles to coexist in the folder.

To add a new procurement context, add a new `rfp_criteria_<domain>.txt` and
`scoring_rubric_<domain>.txt` pair, then update `prompts.yaml` to point agents
at the new files. See `architecture.md` — Making VendorLens Generic.

## Update protocol

When source notes change:

1. Update corresponding file(s) in `context/`.
2. Rebuild the distilled file(s) in this folder.
3. Keep thresholds and requirements explicit (numbers, deadlines, policy triggers).
4. Run the Docker Day 1 smoke check to verify retrieval still passes.
5. Commit source note change and bundle change together.

## Agent usage

- Risk logic reads `policy.txt`.
- Scoring logic reads `rfp_criteria_lms.txt` and `scoring_rubric_lms.txt`.
- Any policy-aware extraction should reference these files instead of hardcoded text.

## Verification (Docker-first)

From repository root:

```bash
docker compose build backend
docker compose run --rm backend python ingest.py --force
docker compose run --rm backend python test_rag.py
```
