# Deployment

## Current Architecture: Local Development

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        LOCAL DEVELOPMENT                                  │
│                                                                          │
│   ┌─────────────────┐              ┌─────────────────┐                  │
│   │   Frontend      │  ──────────▶ │    Backend      │                  │
│   │   Next.js 16    │  localhost   │    FastAPI      │                  │
│   │   :3000         │    :3000     │    Uvicorn      │  :8000           │
│   └─────────────────┘              └─────────────────┘                  │
│                                           │                              │
│                                           ▼                              │
│                              ┌─────────────────────┐                    │
│                              │   6 External APIs   │                    │
│                              │   (all public/free) │                    │
│                              └─────────────────────┘                    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API key (free: [aistudio.google.com](https://aistudio.google.com))

### Setup

```bash
# Clone repository
git clone https://github.com/vedanthchamala/pharmasynapse.git
cd pharmasynapse

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set your API key
export GOOGLE_API_KEY=your_gemini_key_here

# Start backend
uvicorn main:app --reload --port 8000

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** in your browser.

### Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key

# Optional (defaults work for local dev)
# LOG_LEVEL=INFO
```

---

## Docker Deployment

All Docker configuration files are included in the repository root:
- `Dockerfile` — Backend (Python 3.11 + FastAPI)
- `Dockerfile.frontend` — Frontend (Node 20 + Next.js)
- `docker-compose.yml` — Full-stack orchestration with health checks
- `.dockerignore` — Excludes test files, CSV datasets, `__pycache__`, IDE files, and documentation from production images (reduces image size and attack surface)

### Backend Dockerfile (`Dockerfile`) — Multi-Stage

```dockerfile
FROM python:3.11-slim AS base
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS production
COPY backend/ ./backend/
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile (`Dockerfile.frontend`) — Multi-Stage

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --production=false

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ .
ENV NODE_ENV=production
RUN npm run build

FROM node:20-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./
COPY --from=deps /app/node_modules ./node_modules
EXPOSE 3000
CMD ["npm", "start"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

---

## Cloud Deployment Options

### Option 1: Vercel + Railway
- **Frontend**: Deploy to Vercel (free tier, automatic from GitHub)
- **Backend**: Deploy to Railway ($5/month)
- Estimated cost: ~$5/month

### Option 2: AWS (Production)
- **Frontend**: S3 + CloudFront
- **Backend**: ECS Fargate or Lambda
- Estimated cost: ~$30-50/month

### Option 3: Google Cloud Run
```bash
gcloud run deploy pharmasynapse-backend \
  --source ./backend \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=$GOOGLE_API_KEY
```

---

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push to `main` and every PR:

| Job | Runtime | Steps |
|-----|---------|-------|
| `backend-tests` | Ubuntu + Python 3.11 | Install deps → `pytest backend/tests/ -v` (100+ tests: scoring, safety, models, cache, endpoints, NLI, API contracts, orchestrator) |
| `frontend-build` | Ubuntu + Node 20 | `npm ci` → `npm test` (19 Vitest tests) → `npm run build` (TypeScript + production build) |

Both jobs use dependency caching for fast subsequent runs (~30s backend, ~60s frontend).

---

## Health Check

```
GET /health
Response: {"status": "ok", "service": "MolecuThread", "version": "2.0.0"}
```
