---
name: feedback-working-style
description: How Ricardo wants Claude to communicate and behave during sessions
metadata:
  type: feedback
---

Don't add trailing summaries at the end of responses.

**Why:** Ricardo can read the diff. Summaries add noise.

**How to apply:** End when the work is done. One sentence max on what changed and what's next.

---

Don't fold cleanup or refactoring into unrelated fixes.

**Why:** Out-of-scope changes are unverified and add risk. Each change needs its own failing test.

**How to apply:** If you notice something to clean up while fixing something else, ask first. Never do it silently.

---

Don't re-open settled decisions or re-propose rejected ideas.

**Why:** Already evaluated. Re-raising wastes time and signals lost context.

**How to apply:** Check CLAUDE.md Settled Decisions and Do Not Suggest sections before proposing anything.

---

For exploratory questions, give a recommendation and the main tradeoff in 2-3 sentences. Don't implement until Ricardo agrees.
