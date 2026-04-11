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

#### SSE Connection Routing Across Worker Nodes

The sequential agent pipeline — chosen for SSE UX clarity — becomes a bottleneck at scale. In a multi-worker horizontal deployment, each SSE connection must remain pinned to the worker that initiated the pipeline for that request. The design:

```
                            ┌────────────────────────────────┐
                            │   Load Balancer (sticky sessions)│
                            │   IP-hash or cookie affinity     │
                            └─────────────┬──────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              ▼                           ▼                           ▼
     ┌────────────────┐         ┌────────────────┐         ┌────────────────┐
     │  Worker 1      │         │  Worker 2      │         │  Worker N      │
     │  SSE pipeline  │         │  SSE pipeline  │         │  SSE pipeline  │
     │  + local state │         │  + local state │         │  + local state │
     └───────┬────────┘         └───────┬────────┘         └───────┬────────┘
             │                          │                          │
             └──────────────────────────┼──────────────────────────┘
                                        ▼
                              ┌──────────────────┐
                              │   Shared Redis    │
                              │ (result cache +   │
                              │  session state)   │
                              └──────────────────┘
```

**Key design decisions:**

1. **Sticky sessions via IP-hash**: The load balancer (nginx, Traefik, or Cloud Run) routes all requests from a given client IP to the same worker. This ensures the SSE stream stays connected to the worker executing that pipeline.

2. **Redis-backed ResultCache**: After pipeline completion, results are written to Redis (replacing the in-process `ResultCache`). Subsequent non-SSE requests (export, grant-abstract, related-diseases) can be served by any worker since they read from shared Redis.

3. **SSE reconnection handling**: If a worker dies mid-pipeline, the client's `EventSource` auto-reconnects. The new worker checks Redis for partial results and either resumes from the last completed agent or restarts the pipeline. Each SSE event includes a monotonic sequence ID for resumption.

4. **Graceful shutdown**: Workers drain active SSE connections before shutting down (SIGTERM → stop accepting new connections → wait for active pipelines to complete → exit).

### Phase 3: Queue-Based Processing (Fan-Out/Fan-In with Celery)

For high traffic (>50 concurrent users): decouple request handling from pipeline execution via a message queue.

```
                    ┌─────────────┐
                    │  API Server  │  (accepts SSE connections, publishes to queue)
                    └──────┬──────┘
                           │ Celery task per pipeline
                    ┌──────▼──────┐
                    │ Redis Queue  │
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ Celery Worker│ │ Celery Worker│ │ Celery Worker│
    │ (pipeline)   │ │ (pipeline)   │ │ (pipeline)   │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
                    ┌──────────────┐
                    │ Redis Pub/Sub│  (per-user SSE channel)
                    └──────┬───────┘
                           │
                    ┌──────▼──────┐
                    │  API Server  │  (subscribes to user channel, streams to SSE)
                    └─────────────┘
```

The API server publishes a Celery task with a unique `pipeline_id`. The Celery worker executes each agent sequentially, publishing progress events to a Redis Pub/Sub channel keyed by `pipeline_id`. The API server subscribes to that channel and forwards events to the client's SSE connection. This decouples the SSE connection lifetime from the pipeline execution, allowing any API server instance to stream results from any worker.

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
