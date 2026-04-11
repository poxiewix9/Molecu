# Implementation Plan

## Development Roadmap

### Phase 1: Core MVP (Completed)
**Goal**: Prove multi-agent drug repurposing works with real databases

| Milestone | Features | Status |
|-----------|----------|--------|
| M1.1 | Disease target identification via Open Targets GraphQL | ✅ Complete |
| M1.2 | Failed drug search via ClinicalTrials.gov API v2 | ✅ Complete |
| M1.3 | Safety assessment via FDA FAERS (openFDA) | ✅ Complete |
| M1.4 | LLM-powered synthesis with Google Gemini | ✅ Complete |
| M1.5 | Next.js frontend with SSE streaming | ✅ Complete |
| M1.6 | Real-time pipeline progress UI | ✅ Complete |

### Phase 2: Research-Grade Pipeline (Completed)
**Goal**: Replace LLM-generated scores with transparent, evidence-based scoring

| Milestone | Features | Status |
|-----------|----------|--------|
| M2.1 | ChEMBL drug-target binding integration | ✅ Complete |
| M2.2 | PubMed literature mining (E-utilities) | ✅ Complete |
| M2.3 | Evidence-based scoring (0-100, no LLM) | ✅ Complete |
| M2.4 | Rule-based safety classification (no LLM) | ✅ Complete |
| M2.5 | DeBERTa NLI contradiction detection | ✅ Complete |
| M2.6 | Source attribution on every claim | ✅ Complete |
| M2.7 | Removed all dishonest fallback data | ✅ Complete |
| M2.8 | JSON export endpoint with methodology | ✅ Complete |

### Phase 3: Research Workbench (Completed)
**Goal**: Transform from search engine into persistent research environment

| Milestone | Features | Status |
|-----------|----------|--------|
| M3.1 | localStorage session system (save/load/delete) | ✅ Complete |
| M3.2 | Star toggle + researcher notes on drug cards | ✅ Complete |
| M3.3 | PDF report export (@react-pdf/renderer) | ✅ Complete |
| M3.4 | Drug deep-dive panel (20 papers, all trials, full FAERS) | ✅ Complete |
| M3.5 | Side-by-side drug comparison view | ✅ Complete |
| M3.6 | Disease autocomplete via Open Targets search API | ✅ Complete |
| M3.7 | Search history in localStorage | ✅ Complete |

### Phase 4: Visualization & UX (Completed)
**Goal**: Make it visually impressive and intuitive

| Milestone | Features | Status |
|-----------|----------|--------|
| M4.1 | Interactive 3D molecular hero (Three.js) | ✅ Complete |
| M4.2 | 3Dmol.js molecule rendering from PubChem | ✅ Complete |
| M4.3 | Drug name variation matching for PubChem | ✅ Complete |
| M4.4 | Minimalist white-themed UI with Tailwind CSS 4 | ✅ Complete |
| M4.5 | Framer Motion animations throughout | ✅ Complete |

### Phase 5: Production Hardening (Complete)
**Sprint 5A (Week 1):** Testing, Docker, CORS — Vedanth (backend), Keshav (frontend build verification)
**Sprint 5B (Week 2):** Grant abstract, related diseases, LLM cleanup — Keshav (endpoints + LLM), Vedanth (Open Targets reverse lookup)
**Sprint 5C (Week 3):** 3D editor, cache refactor, CI/CD, async DeBERTa — Keshav (editor + frontend), Vedanth (cache + CI)

| Milestone | Features | Owner | Est. Hours | Status |
|-----------|----------|-------|-----------|--------|
| M5.1 | Pytest test suite (78 tests: scoring, safety, models, cache, endpoints, NLI) | Vedanth | 6h | ✅ Complete |
| M5.2 | Docker deployment (multi-stage Dockerfiles, docker-compose.yml) | Vedanth | 3h | ✅ Complete |
| M5.3 | CORS parameterization via ALLOWED_ORIGINS env var | Vedanth | 1h | ✅ Complete |
| M5.4 | Grant abstract generator (Gemini-drafted NIH R21 aims) | Keshav | 4h | ✅ Complete |
| M5.5 | Related diseases via shared protein target network | Keshav | 4h | ✅ Complete |
| M5.6 | LLM function naming cleanup (ask_claude → ask_llm) | Keshav | 1h | ✅ Complete |
| M5.7 | 3D molecular structure editor (R3F, PubChem SDF, undo/redo, SDF export) | Keshav | 8h | ✅ Complete |
| M5.8 | ResultCache singleton + dependency injection refactor | Vedanth | 3h | ✅ Complete |
| M5.9 | Async DeBERTa inference via ThreadPoolExecutor | Vedanth | 2h | ✅ Complete |
| M5.10 | GitHub Actions CI/CD pipeline (pytest + next build) | Vedanth | 2h | ✅ Complete |
| M5.11 | API caching layer (Redis) | — | — | 📋 Planned |
| M5.12 | Rate limiting middleware | — | — | 📋 Planned |

---

## Technical Decisions Log

### Decision 1: Multi-Agent Pipeline vs. Single LLM Prompt
**Decision**: Multi-agent pipeline
**Rationale**: Each agent queries a specific database and produces structured output. If one fails, others continue. The pipeline works without the LLM entirely — it just loses narrative summaries.

### Decision 2: Evidence-Based Scoring vs. LLM Confidence
**Decision**: Deterministic scoring from data
**Rationale**: LLM-generated "confidence scores" are not reproducible and can't be audited. Our 0-100 score traces directly to database values: target association strength, trial phase, paper count, safety verdict. A researcher can verify every component.

### Decision 3: Rule-Based Safety vs. LLM Safety Assessment
**Decision**: Rule-based classification
**Rationale**: Safety is too important for LLM hallucination risk. We classify FDA FAERS adverse events against predefined high-risk terms (death, cardiac failure, hepatic failure) and organ conflict rules. Deterministic, reproducible, auditable.

### Decision 4: SSE vs. WebSocket
**Decision**: Server-Sent Events
**Rationale**: Unidirectional (server → client) is sufficient. SSE is simpler, has built-in reconnection, and works through proxies. No bidirectional communication needed.

### Decision 5: localStorage vs. Database for Sessions
**Decision**: Browser localStorage
**Rationale**: No login required, no server-side storage, works offline, researcher owns their data. Overkill to add auth + database for a research tool. Max 20 sessions stored.

### Decision 6: Next.js vs. Vite + React
**Decision**: Next.js 16
**Rationale**: Server-side rendering for SEO, Turbopack for fast dev, app router for clean structure, better production builds. TypeScript support out of the box.

### Decision 7: Gemini vs. Claude vs. GPT-4
**Decision**: Google Gemini 2.0 Flash
**Rationale**: Free tier is generous for a research tool. Fast inference. Good at biomedical synthesis. Pipeline degrades gracefully when rate-limited — agents still return real data, just without narrative summaries.

---

## Risk Mitigation

| Risk | Impact | Mitigation (Implemented) |
|------|--------|--------------------------|
| External API downtime | High | Graceful degradation — every agent returns empty results, never crashes |
| LLM rate limits | Medium | Pipeline works without LLM. No retry loops. Immediate fallback to raw data |
| LLM hallucination | High | Scoring is LLM-free. Safety is rule-based. Contradiction detection via NLI model |
| Drug name mismatches | Medium | `generateNameVariations()` tries 6+ permutations per drug for PubChem lookup |
| Non-drug ClinicalTrials results | Medium | Length filter + intervention type filter removes procedures and gene names |
| ChEMBL returning IDs not names | Low | `_resolve_molecule_name()` queries molecule endpoint for human-readable names |
| DeBERTa NLI latency | Medium | Inference now runs in `ThreadPoolExecutor` (2 workers) — does not block the async event loop. Latency is ~2-4s per pair, acceptable for 5-8 candidates |
| Open Targets schema changes | Low | GraphQL queries pin to v4 API. Breaking changes monitored via version header |
| FAERS drug name normalization | Medium | Drug names in FAERS are inconsistent (brand vs generic). We pass the canonical name from ClinicalTrials.gov/ChEMBL, accepting partial miss rate |
| Gemini API key exhaustion | Medium | Startup warning if key is missing. Pipeline degrades gracefully — agents return raw data without LLM summaries. Free tier quota is ~15 RPM / 1M tokens/day |
| localStorage quota (5MB) | Low | Max 20 sessions stored. Each session ~50-100KB. Oldest sessions could be pruned. UI warns if save fails |
| External API schema changes | Medium | All API responses are parsed defensively with `.get()` and fallback defaults. Integration tests validate response shapes against mocked fixtures |
| Concurrent user state isolation | Medium | Replaced global `_last_results` dict with `ResultCache` singleton accessed via dependency injection. Thread-safe with `threading.Lock`. Per-user isolation would require session tokens (planned for Redis phase) |

### Demo-Day Contingency Plan

| Scenario | Fallback |
|----------|----------|
| Gemini API down or rate-limited | Pipeline continues — agents return structured data, just without LLM-generated summaries |
| Open Targets API down | Disease analyst returns empty targets → no drug candidates. Clear UI messaging |
| ClinicalTrials.gov slow (>15s) | httpx timeout + empty result fallback. Other agents still run |
| PubChem SDF unavailable | MoleculeViewer shows stylized fallback icon. MoleculeEditor shows "no structure" state |
| All external APIs fail | Pipeline completes with empty data at each stage. UI shows "no results" with suggestion to try alternative disease names |

---

## Team Structure

| Member | Role | Ownership |
|--------|------|-----------|
| Vedanth Chamala | Full-stack lead | Backend pipeline, API design, agent architecture |
| Keshav Singh | Frontend & AI integration | Next.js UI, 3D visualization, LLM integration, research workbench features |

**Division of labor**: Backend pipeline (agents, services, scoring) and frontend (Dashboard, components, PDF/3D) were developed in parallel. Documentation and testing were collaborative efforts. All architectural decisions were made jointly.
