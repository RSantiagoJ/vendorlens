# Backend Runtime (Docker-First)

This backend is run and validated through Docker for cross-machine parity.

## Prerequisites

- Docker Desktop (or Docker Engine + Compose)
- `backend/.env` populated with required keys

## Build

From repository root:

```bash
docker compose build backend
```

## Day 1 smoke check

One-command sanity check from repository root:

```powershell
./backend/smoke_day1.ps1
```

Options:

```powershell
# Skip image build
./backend/smoke_day1.ps1 -SkipBuild

# Skip index rebuild
./backend/smoke_day1.ps1 -SkipReindex
```

Equivalent manual commands:

```bash
docker compose run --rm backend python ingest.py --force
docker compose run --rm backend python test_rag.py
```

Expected final line:

`All checks passed. Day 1 checkpoint complete.`

## Run arbitrary backend script

```bash
docker compose run --rm backend python <script.py>
```

## Notes

- `requirements.lock.txt` is used during image build for reproducible installs.
- `requirements.txt` remains the editable source dependency list.
