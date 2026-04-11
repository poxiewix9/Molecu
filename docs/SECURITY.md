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

## Threat Model

| Threat | Risk | Mitigation |
|--------|------|------------|
| API key exposure | Critical | Environment variables, .gitignore, no hardcoding |
| Injection attacks | Medium | Pydantic validation, URL encoding for external APIs |
| XSS attacks | Low | React default escaping, no dangerouslySetInnerHTML |
| LLM prompt injection | Low | User input treated as data in structured prompts |
| Dependency vulnerabilities | Medium | npm audit, pip safety check |
| Data exfiltration | N/A | No user data to exfiltrate |
