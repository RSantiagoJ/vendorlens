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
