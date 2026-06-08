---
name: project-current-state
description: Current project state — what's done, what's deployed, what's next
metadata:
  type: project
---

As of 2026-06-08, VendorLens is feature-complete for the upcoming presentation (~2026-06-10).

**What's done:**
- Full pipeline: extract → risk → score → memo → negotiation (per-vendor playbooks with tooltips)
- 148 tests passing (123 backend offline + 25 frontend)
- Deployed: Frontend on Vercel, Backend on AWS App Runner
- Latest: concessions column overflow fix in NegotiationPlaybook — merged to main, deployed

**What's next after presentation:**
- Terraform + Vercel integration
- Production Postgres on AWS RDS
- DB migration: `rfp_name` column on production
- Tear down AWS App Runner after presentation (~$5-7/month idle charge)

**Demo instructions:**
- Go to https://vendorlens-beryl.vercel.app — upload proposals, run analysis
- Results have 10-min TTL in memory — don't refresh the tab during demo
- Warm backend before demo: `API=https://brpste4mu9.us-east-1.awsapprunner.com ./scripts/test_api.sh`
