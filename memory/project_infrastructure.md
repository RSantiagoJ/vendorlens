---
name: project-infrastructure
description: Deployment setup — what runs where, how to deploy, how to tear down
metadata:
  type: project
---

**Frontend:** Vercel — https://vendorlens-beryl.vercel.app
- Auto-deploys on every push to `main`. No manual step needed.

**Backend:** AWS App Runner — https://brpste4mu9.us-east-1.awsapprunner.com
- Image in ECR: `438920434591.dkr.ecr.us-east-1.amazonaws.com/vendorlens-backend`
- Deploy: `bash scripts/deploy_backend.ps1` (Windows) or `bash scripts/deploy_backend.sh` (Linux)
- Costs ~$5-7/month idle. Tear down after presentation: `cd terraform && terraform destroy`

**Local:**
- Backend + Postgres via Docker Compose. All Python runs inside Docker — never on host.
- Frontend via `cd frontend && npm run dev`

**What triggers a redeploy:**
- Frontend change → push to main (Vercel auto-deploys)
- Backend `.py` change → run deploy script
- Both changed → push first, then deploy script

**Why App Runner over Render free tier:** No cold start during demo. Worth the cost for presentation reliability.
