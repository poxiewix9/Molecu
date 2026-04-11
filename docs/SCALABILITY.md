# Scalability

## Current Performance

| Metric | Current Performance |
|--------|-------------------|
| End-to-end pipeline time | ~30-60s depending on disease complexity |
| External API calls per analysis | ~15-25 across 6 databases |
| Frontend build (Turbopack) | ~11s production build |
| Session load from localStorage | Instant (<10ms) |
| PDF generation (client-side) | 1-3 seconds |
| Concurrent users supported | ~10 (single backend instance) |

---

## Optimization Techniques (Implemented)

### 1. Async Pipeline + Thread-Pooled NLI
All external API calls are async via `httpx.AsyncClient`. Independent agents could be parallelized, but we run them sequentially for SSE streaming UX — users see each step complete in order.

The DeBERTa NLI model (which uses synchronous PyTorch inference) is offloaded to a `ThreadPoolExecutor` with 2 workers via `asyncio.run_in_executor()`. This prevents the ~2-4s inference from blocking the async event loop, allowing other requests to be served concurrently.

### 2. Graceful Degradation
Every agent handles failures without blocking:
```python
try:
    result = await external_api_call()
except Exception as e:
    log.warning("API error: %s", e)
    result = []  # Continue pipeline with empty data
```

### 3. Staggered PubChem Requests
Multiple 3D molecule viewers stagger their PubChem API calls (600ms delay per card) to avoid rate limiting.

### 4. Drug Name Variation Matching
```python
def generateNameVariations(drugName):
    # Tries 6+ permutations to maximize PubChem hit rate
    # base, no-parentheses, lowercase, no-hyphens, first-word, no-trailing-numbers
```

### 5. Client-Side PDF Generation
PDF reports are generated entirely in the browser using `@react-pdf/renderer` — no server round-trip, works offline.

### 6. localStorage Sessions
Zero server-side storage. Sessions persist in the browser with instant load times. Max 20 sessions to prevent storage bloat.

---

## Scaling Strategy (Planned)

### Phase 1: Caching Layer
```
Request → Check Redis Cache → Hit? Return cached → Miss? Query API → Cache result
```
- Cache disease targets (24h TTL)
- Cache clinical trial data (1h TTL)
- Cache PubMed results (24h TTL)

### Phase 2: Horizontal Scaling
```
Load Balancer → Backend Instance 1
              → Backend Instance 2
              → Backend Instance N
              → Shared Redis Cache
```

### Phase 3: Queue-Based Processing
For high traffic: decouple request handling from pipeline execution via a message queue.

---

## External API Rate Limits

| API | Rate Limit | Our Strategy |
|-----|-----------|-------------|
| Open Targets | ~10 req/s | Single query per analysis |
| ClinicalTrials.gov | ~3 req/s | Single query per analysis |
| FDA FAERS | 240 req/min | Retry with backoff (3 attempts) |
| PubMed | 3 req/s (no API key) | 350ms delay between calls |
| ChEMBL | ~10 req/s | Sequential target queries |
| PubChem | ~5 req/s | Staggered frontend requests |
| Google Gemini | Free tier varies | Immediate fallback on rate limit |
