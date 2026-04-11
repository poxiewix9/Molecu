# Security

## Security Architecture

PharmaSynapse implements defense-in-depth security principles across all layers.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          SECURITY LAYERS                                 │
├──────────────────────────────────────────────────────────────────────────┤
│  Layer 1: Network Security                                               │
│  • HTTPS encryption (TLS 1.3)                                            │
│  • CORS policy enforcement (localhost only in dev)                       │
│  • No external inbound connections required                              │
├──────────────────────────────────────────────────────────────────────────┤
│  Layer 2: Application Security                                           │
│  • Input validation (Pydantic models on all endpoints)                  │
│  • Output sanitization (React default XSS escaping)                     │
│  • Error handling without internal state leakage                        │
│  • No user-supplied code execution                                       │
├──────────────────────────────────────────────────────────────────────────┤
│  Layer 3: Data Security                                                  │
│  • API key via environment variable only                                │
│  • No PII storage whatsoever                                            │
│  • No database — sessions in client localStorage only                   │
│  • All external API communication over HTTPS                            │
├──────────────────────────────────────────────────────────────────────────┤
│  Layer 4: AI Safety                                                      │
│  • LLM not used for scoring — deterministic evidence scores             │
│  • LLM not used for safety — rule-based classification                  │
│  • Contradiction detection catches conflicting agent outputs            │
│  • Prominent disclaimer: "Research tool, not medical advice"            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Implemented Security Controls

### 1. Input Validation (Pydantic)
All API inputs are validated via FastAPI's Pydantic integration. Disease names, drug names, and query strings are sanitized before use in external API calls.

### 2. CORS Configuration
CORS origins are parameterized via the `ALLOWED_ORIGINS` environment variable, supporting staging and production environments without code changes:
```python
_allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
Set `ALLOWED_ORIGINS=https://pharmasynapse.example.com` in production.

### 3. API Key Protection
- API key stored in environment variable `GOOGLE_API_KEY`
- `.gitignore` excludes `.env` files
- `.env.example` provides template without real keys
- Key is never sent to the frontend or logged
- Startup warning emitted if `GOOGLE_API_KEY` is not set (helps catch misconfiguration)
- Push scripts verify no hardcoded keys exist in the codebase before committing

### 3b. Result Cache Isolation
Pipeline results are stored in a `ResultCache` singleton (`backend/cache.py`) with thread-safe locking rather than a module-level global dict. This prevents accidental cross-module coupling and provides a clean swap path to per-session Redis storage for multi-user deployments.

### 4. No User Data Collection
- **No accounts**: No registration, no login
- **No PII**: No personal information collected or stored
- **No server-side sessions**: All research data stays in browser localStorage
- **No analytics/tracking**: No third-party scripts

### 5. External API Security
- All external API calls use HTTPS
- Timeout limits on every call (8–15 seconds)
- SSL verification enabled
- Graceful degradation on failure (empty results, never crash)

### 6. LLM Safety
- LLM output is **never** used for scoring or safety verdicts
- LLM generates natural-language summaries only
- If LLM is unavailable, pipeline continues with raw data
- Structured prompts prevent injection
- Output parsed as JSON with fallback to empty

---

## HIPAA / Compliance

PharmaSynapse does **not** handle Protected Health Information (PHI):
- ✅ No patient data collected
- ✅ No user accounts or personal information
- ✅ Disease names are public medical terminology
- ✅ Drug information is from public government databases
- ✅ All data processing is ephemeral (in-memory)

---

## Rate Limiting (Implemented)

The SSE evaluation endpoint is protected by a token-bucket rate limiter (`backend/middleware.py`) to prevent unbounded resource consumption:

```python
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token-bucket rate limiter keyed by client IP."""
    # /api/evaluate/{disease}: 5 requests per 60s per IP
    # All other /api/* endpoints: 20 requests per 60s per IP
```

Configuration:
- **Evaluate endpoint**: 5 requests/minute per IP (computationally expensive — runs 5 agents + NLI inference)
- **General API**: 20 requests/minute per IP (lightweight reads from cache)
- **Non-API routes**: No rate limiting (health checks, static assets)
- **429 response**: Returns `Retry-After` header with seconds until next available slot

The rate limiter uses IP-based keying (with `X-Forwarded-For` awareness for reverse proxy deployments). In production with Redis, this would transition to a distributed rate limiter (e.g., `redis-cell` or sliding-window Lua script) shared across worker instances.

---

## API Authentication Model (Planned for Enterprise Tier)

While the core PharmaSynapse tool remains free and unauthenticated (no barriers to researchers), the planned enterprise API tier requires authentication:

```
┌──────────────────────────────────────────────────────────────────────┐
│                     AUTHENTICATION ARCHITECTURE                       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Free Tier (Current):                                                │
│  • No authentication required                                        │
│  • Rate limited per IP (5 evaluate/min, 20 general/min)             │
│  • Intended for individual researchers                               │
│                                                                      │
│  Enterprise Tier (Planned):                                          │
│  • API key authentication via X-API-Key header                      │
│  • Key issued per organization, stored hashed in Redis              │
│  • Higher rate limits (50 evaluate/min, 200 general/min)            │
│  • Usage tracking per key (monthly request counts)                  │
│  • Webhook notifications on quota thresholds                        │
│                                                                      │
│  Implementation Sketch:                                              │
│  1. API keys generated as SHA-256 of org_id + secret + timestamp   │
│  2. Keys stored as bcrypt hashes in Redis (never plaintext)        │
│  3. Middleware checks X-API-Key → Redis lookup → rate limit tier    │
│  4. Missing/invalid key → falls back to free tier limits           │
│  5. /api/usage endpoint returns current period usage stats          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

This design ensures:
- **Zero friction for researchers** — no login, no API key needed for basic use
- **Scalable for institutions** — organizations get higher limits and usage tracking
- **No breaking changes** — enterprise auth is additive, never removes free access

---

## Threat Model

| Threat | Risk | Mitigation |
|--------|------|------------|
| API key exposure | Critical | Environment variables, .gitignore, no hardcoding |
| Injection attacks | Medium | Pydantic validation, URL encoding for external APIs |
| XSS attacks | Low | React default escaping, no dangerouslySetInnerHTML |
| LLM prompt injection | Low | User input treated as data in structured prompts |
| Dependency vulnerabilities | Medium | npm audit, pip safety check |
| Data exfiltration | N/A | No user data to exfiltrate |
| Unbounded SSE connections | Medium | Token-bucket rate limiter (5 eval/min per IP) |
| Open Targets schema evolution | Low | Automated API contract tests in CI validate response shapes |
