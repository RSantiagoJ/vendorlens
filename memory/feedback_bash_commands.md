---
name: feedback-bash-commands
description: Ricardo runs all shell commands himself — Claude prints the command, never executes it
metadata:
  type: feedback
---

Never use the Bash tool to run commands. Print the exact command for Ricardo to run instead.

**Why:** Saves tokens and context window. Ricardo is comfortable running commands himself.

**How to apply:** All shell commands (tests, docker, git, curl, scripts) — print and let Ricardo run. File edits (Read/Edit/Write tools) are fine to do directly without asking.
