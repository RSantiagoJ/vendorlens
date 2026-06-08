---
name: feedback-testing-discipline
description: Test-first rules, when to run which tests, offline vs live
metadata:
  type: feedback
---

Test-first is non-negotiable. Write the test, confirm it fails for the right reason, then make the change.

**Why:** A test that was never red proves nothing. Ricardo built this discipline intentionally.

**How to apply:** Never write a test after the implementation. If a test passes immediately on first run, the test is wrong.

---

Offline tests (`pytest tests/ -q`) mock everything — no API calls, no real files, no API keys needed. Runs in ~5s.

**Why:** Fast feedback, zero cost, works without credentials.

**How to apply:** Run before every commit. This is the default test command.

---

Live tests use `alpha_lms.txt` and `beta_lms.txt` only (~$0.05/run). Never use the full corpus for live testing.

**Why:** Full corpus burns tokens unnecessarily during development.

**How to apply:** Live tests are in `tests/live/`, excluded from default pytest. Only run when suspecting a real pipeline issue.

---

Frontend scoring/display logic lives in `frontend/lib/scoring.ts`, tested with `cd frontend && npm test`.
