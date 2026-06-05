# When to Restart What

## Frontend changes (components, pages, CSS, TypeScript)
**No restart needed.** Next.js hot-reloads automatically in development.

## Backend changes (any `.py` file)
```bash
docker compose restart backend
```

## Dependency changes
| What changed | Command |
|---|---|
| `frontend/package.json` | `docker compose up --build frontend` |
| `backend/requirements.txt` | `docker compose up --build backend` |
| `Dockerfile` (either) | `docker compose up --build` |

## Environment variable changes (`.env`)
```bash
docker compose down && docker compose up
```

## Nuclear option — something is broken and you don't know why
```bash
docker compose down && docker compose up --build
```

## Check what's running
```bash
docker compose ps
```

## View logs
```bash
docker compose logs -f backend     # backend only
docker compose logs -f frontend    # frontend only
docker compose logs -f             # everything
```

---

## Production (AWS — App Runner + Vercel)

### Where the app lives
- **Frontend (Vercel):** TBD — deploy with `cd frontend && npx vercel deploy --prod`
- **Backend (App Runner):** https://brpste4mu9.us-east-1.awsapprunner.com
- **Health check:** https://brpste4mu9.us-east-1.awsapprunner.com/health → `{"status":"ok"}`
- **ECR repo:** `438920434591.dkr.ecr.us-east-1.amazonaws.com/vendorlens-backend`
- **S3 uploads bucket:** `vendorlens-uploads-438920434591`

### ECR login (Windows PowerShell)
Docker Desktop will open a browser popup if you use `--password`. Use `--password-stdin` instead:
```powershell
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 438920434591.dkr.ecr.us-east-1.amazonaws.com/vendorlens-backend
```

### Deploy a new backend image
```powershell
# 1. Log in to ECR (command above)
# 2. Build, tag, and push from repo root
docker build --platform linux/amd64 -t vendorlens-backend backend/
docker tag vendorlens-backend:latest 438920434591.dkr.ecr.us-east-1.amazonaws.com/vendorlens-backend:latest
docker push 438920434591.dkr.ecr.us-east-1.amazonaws.com/vendorlens-backend:latest
# App Runner picks up the new image automatically (auto_deployments_enabled = true)
```

### Tear down after demo (stops all AWS charges)
```powershell
cd terraform && terraform destroy
```
