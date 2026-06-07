# Presentation To-Do List

## Key Talking Points to Prepare

- [ ] **Versatility pitch** — explain how VendorLens isn't just for LMS/ERP/Payroll procurement.
  - The rubric (bundle) is the only thing that's department-specific.
  - Any department that receives vendor proposals can plug in their own scoring criteria.
  - Examples to have ready: IT infrastructure, facilities, marketing agencies, staffing vendors, consulting firms.
  - Frame it as: "we built this for UMass Procurement, but the architecture is generic — swap the rubric, keep everything else."

- [ ] **The "how would we extend this" question** — anticipate it and have a concrete answer.
  - New bundle = new JSON rubric file + a few scoring dimension labels. No code changes needed.
  - Could support free-text rubric upload in a future version (let the department define their own criteria).

- [ ] **Live demo flow** — decide whether to use `?demo` (instant results) or `?processing` (shows the pipeline running).
  - `?processing` is more impressive if the timing works out.
  - Have `?demo` as a fallback if the live backend is slow.

## Other Things to Cover

- [ ] What each AI agent actually does (extract → risk → score → memo)
- [ ] Why five agents instead of one big prompt (per-stage specialization, better structured output)
- [ ] How risk flags are surfaced and what makes something HIGH vs MEDIUM
- [ ] The scoring rubric — what the 8 dimensions are and how they map to real procurement concerns
- [ ] Data privacy: proposals stay in-memory (10-min TTL), nothing persisted long-term

## Potential Questions to Prepare For

- "Could we use this for X department?" → yes, explain rubric swap
- "How long does it actually take?" → under 60 seconds for 2–3 vendors
- "What if the vendor doc is a PDF?" → supported (.txt and .pdf accepted)
- "Who would maintain this?" → low maintenance, model calls are the only moving part
- "What does it cost to run?" → token cost per analysis, roughly $X per run (fill in)
