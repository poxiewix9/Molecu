# Technical Architecture

## System Overview

PharmaSynapse implements a **multi-agent AI pipeline** with real-time SSE streaming, evidence-based scoring, 6 external API integrations, and a persistent research workbench frontend.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 16 + TypeScript + React 19)             │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Dashboard   │  │  DrugDetail  │  │ CompareView  │  │  PDFReport    │  │
│  │  + DrugCards │  │   Panel      │  │   Modal      │  │  Generator    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘  └───────────────┘  │
│         │                 │                                                  │
│  ┌──────┴─────────────────┴──────┐  ┌──────────────┐  ┌───────────────┐   │
│  │     useEventStream (SSE)      │  │   Sessions   │  │  3D Viewers   │   │
│  │     Real-time state mgmt      │  │ (localStorage)│  │(3Dmol/Three)  │   │
│  └──────────────┬────────────────┘  └──────────────┘  └───────────────┘   │
│                 │ SSE Stream                                                 │
└─────────────────┼────────────────────────────────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI + Python 3.10+)                        │
│                                                                              │
│  Endpoints:                                                                  │
│  ├── GET /api/evaluate/{disease}             SSE streaming pipeline          │
│  ├── GET /api/drug-detail/{drug}?disease=    Deep-dive expanded data         │
│  ├── GET /api/suggest/{query}                Autocomplete (Open Targets)     │
│  ├── GET /api/export/{disease}               Structured JSON report          │
│  ├── GET /api/grant-abstract/{drug}?disease= NIH R21 draft (Gemini LLM)     │
│  └── GET /api/related-diseases/{disease}     Shared target network           │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      AGENT PIPELINE (Sequential SSE)                   │ │
│  │                                                                        │ │
│  │  Disease Analyst ──▶ Drug Hunter ──▶ Safety Checker ──▶ Evidence Agent │ │
│  │  (Open Targets)     (CT.gov +       (FDA FAERS)       (PubMed)        │ │
│  │                      ChEMBL)                                           │ │
│  │                                              ──▶ Contradiction Detector│ │
│  │                                                   (DeBERTa NLI local) │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                       SERVICE LAYER                                    │ │
│  │  open_targets.py  clinical_trials.py  faers.py  pubmed.py  chembl.py  │ │
│  │  llm.py (Gemini)                                                      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────────────────────────────────┐
│                        EXTERNAL DATA SOURCES (All Free)                      │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐   │
│  │Open Targets │ │ClinicalTrials│ │FDA FAERS │ │ PubMed │ │  ChEMBL  │   │
│  │  (GraphQL)  │ │  .gov v2     │ │(openFDA) │ │ (NCBI) │ │(REST API)│   │
│  └─────────────┘ └──────────────┘ └──────────┘ └────────┘ └──────────┘   │
│  ┌─────────────┐ ┌──────────────┐                                         │
│  │  PubChem    │ │ Google Gemini│                                         │
│  │ (SDF/REST)  │ │ (LLM API)   │                                         │
│  └─────────────┘ └──────────────┘                                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Multi-Agent Architecture

### Design Principles

1. **Single Responsibility**: Each agent queries one data domain
2. **Structured I/O**: All agents use Pydantic models for type-safe exchange
3. **Sequential Execution**: Agents depend on upstream results (targets → drugs → safety → evidence)
4. **Graceful Degradation**: Every agent handles API failures — returns empty results, never crashes
5. **LLM-Optional**: Scoring and safety classification work without the LLM
6. **Transparent Scoring**: Evidence scores are deterministic, computed from data, not LLM output

### Agent Inventory

| Agent | Input | Output | External APIs | Purpose |
|-------|-------|--------|---------------|---------|
| **Disease Analyst** | Disease name | `List[DiseaseTarget]` | Open Targets GraphQL | Identify protein targets and disease biology |
| **Drug Hunter** | Targets + disease | `List[DrugCandidate]` | ClinicalTrials.gov + ChEMBL | Find shelved drugs matching targets, compute evidence scores |
| **Safety Checker** | Drug candidates | `List[SafetyAssessment]` | FDA FAERS (openFDA) | Rule-based safety classification from adverse event data |
| **Evidence Agent** | Candidates + disease | `List[EvidenceSummary]` | PubMed E-utilities | Mine supporting literature, fetch abstracts |
| **Contradiction Detector** | All agent outputs | `List[Contradiction]` | DeBERTa NLI (local) | Cross-validate logical consistency |

### Pipeline Orchestration

The pipeline is orchestrated in `main.py` as a sequential async generator. Each agent is an `async` function with a standardized contract:

```python
# Every agent follows this pattern:
async def agent_function(
    inputs_from_upstream: ...,     # Pydantic models from prior agents
) -> list[PydanticOutputModel]:    # Structured output, never raw strings
    try:
        data = await external_service_call(...)  # httpx async client
        result = process_and_structure(data)       # Deterministic logic
        return result
    except Exception as e:
        log.error("Agent failed: %s", e)
        return []                                  # Graceful degradation
```

To add a new agent (e.g., UniProt protein data or STRING interaction networks):
1. Create `backend/services/new_api.py` with async httpx client functions
2. Create `backend/agents/new_agent.py` following the contract above
3. Add the agent call to the SSE generator in `main.py`
4. Define output Pydantic model in `models.py`

The pipeline trades parallelism for UX clarity — agents execute sequentially so users see real-time progress. At scale (>20 concurrent users), this could transition to a fan-out/fan-in pattern with Celery + Redis while preserving the SSE streaming interface.

### DeBERTa NLI Contradiction Detection

The contradiction detector uses Microsoft's DeBERTa-base model for Natural Language Inference, loaded via HuggingFace Transformers:

- **Model**: `cross-encoder/nli-deberta-v3-small` (loaded once at first use)
- **Inference**: Offloaded to a `ThreadPoolExecutor` (2 workers) via `asyncio.run_in_executor()` — does not block the async event loop
- **Latency**: ~2-4 seconds per claim pair, acceptable for 5-8 candidates
- **Usage**: Compares Drug Hunter claims ("drug X is promising") against Safety Checker claims ("drug X has fatal side effects") using entailment/contradiction/neutral scoring
- **Separation**: The NLI path (`evaluate_claims()` in `contradiction_engine.py`) is a standalone function, independent from the LLM. The optional LLM path (`_llm_contradiction_check`) provides supplementary mechanistic reasoning and is cleanly separated.

### Evidence Scoring System

The scoring is **100% deterministic** — no LLM involvement. The weight allocation (30/25/25/20) reflects the drug repurposing literature: target-disease association is the strongest predictor of repurposing success (Pushpakom et al., Nature Reviews Drug Discovery, 2019), followed by clinical trial phase reached (higher phase = more human safety/efficacy data), literature support, and post-market safety profile. These weights are configurable in `compute_evidence_score()` and could be tuned via a validation protocol comparing against known successful repurposings (e.g., thalidomide → multiple myeloma).

```python
def compute_evidence_score(target_score, phase, paper_count, safety_verdict):
    target_pts = min(int(target_score * 30), 30)      # 0-30: Open Targets association
    trial_pts = {"PHASE3": 25, "PHASE2": 18, ...}     # 0-25: Clinical trial phase reached
    lit_pts = min(paper_count * 5, 25)                 # 0-25: PubMed paper count
    safety_pts = {"PASS": 20, "WARNING": 10, ...}      # 0-20: FDA FAERS verdict
    return EvidenceScore(total=target_pts + trial_pts + lit_pts + safety_pts, ...)
```

---

## Real-Time Streaming Architecture

### Server-Sent Events (SSE)

Each agent emits events as it works, providing real-time feedback:

```
Backend                                          Frontend
   │                                                │
   │── data: {"agent":"disease_analyst",            │
   │          "status":"working",                   │
   │          "message":"Searching Open Targets"}    │
   │                                                │
   │── data: {"agent":"disease_analyst",            │
   │          "status":"complete",                  │
   │          "data":{"targets":[...]}}              │
   │                                                │
   │── data: {"agent":"drug_hunter",                │
   │          "status":"working", ...}               │
   │          ... continues for all agents ...      │
   │                                                │
   │── data: {"agent":"system",                     │
   │          "status":"complete",                  │
   │          "data":{full EvaluationResult}}         │
```

---

## Data Models (Pydantic)

```python
class EvidenceScore(BaseModel):
    target_association: int   # 0-30
    trial_evidence: int       # 0-25
    literature_support: int   # 0-25
    safety_profile: int       # 0-20
    total: int                # 0-100
    breakdown: str            # Human-readable explanation

class DrugCandidate(BaseModel):
    drug_name: str
    trial_id: str
    original_indication: str
    phase: str
    failure_reason: str
    mechanism: str
    repurposing_rationale: str
    confidence: float
    evidence_score: EvidenceScore | None
    sources: list[str]        # Database attributions

class SafetyAssessment(BaseModel):
    drug_name: str
    verdict: SafetyVerdict    # PASS | WARNING | HARD_FAIL
    adverse_events: list[str]
    reasoning: str
    organ_conflicts: list[str]
    report_counts: dict[str, int]  # FDA report counts per event
```

---

## Frontend Architecture

### Component Hierarchy

```
Dashboard.tsx (main orchestrator, ~600 lines)
├── HeroScene.tsx           Three.js interactive molecular background
├── Search + Autocomplete   Disease input with Open Targets suggestions
├── PipelineProgress        Real-time agent status indicators
├── DrugCard[]              Per-candidate cards with:
│   ├── MoleculeViewer      3Dmol.js PubChem structure rendering
│   ├── ScorePills          Evidence score breakdown
│   ├── Star toggle         Mark as promising
│   ├── Notes textarea      Researcher annotations
│   ├── Compare checkbox    Side-by-side comparison
│   ├── Deep dive button    Opens DrugDetailPanel
│   └── Edit molecule       Opens MoleculeEditor popup
├── CompareView.tsx         Two-column comparison modal
├── DrugDetailPanel.tsx     Slide-out with 3 tabs (Literature, Trials, Safety)
├── MoleculeEditor.tsx      3D molecular structure editor (R3F + PubChem SDF)
├── GrantAbstractModal.tsx  LLM-drafted NIH R21 grant abstract
├── RelatedDiseases.tsx     Shared protein target disease network
├── PDFReport.tsx           @react-pdf/renderer multi-page template
├── Session sidebar         Past research sessions from localStorage
└── AgentLog                Expandable pipeline event log
```

### State Management

- **Server state**: SSE stream via `useEventStream` custom hook
- **Session state**: localStorage via `sessions.ts` (auto-save on pipeline complete)
- **UI state**: React useState for expansion, tabs, modals
- **Derived state**: Sorted candidates (starred first), safety/evidence maps

### Technology Choices

| Choice | Rationale |
|--------|-----------|
| **Next.js 16** | Server-side rendering, Turbopack dev server, app router |
| **TypeScript** | Type safety across 15+ components and all data models |
| **Tailwind CSS 4** | Rapid UI development, consistent design tokens |
| **Framer Motion** | Smooth pipeline animations, card transitions, panel slides |
| **Three.js** | Interactive 3D molecular hero scene |
| **3Dmol.js** | Real molecular structure rendering from PubChem SDF data |
| **@react-pdf/renderer** | Client-side PDF — no server round-trip, works offline |
| **localStorage** | Zero-auth session persistence — researchers own their data |

---

## Rate Limiting

The API is protected by a token-bucket rate limiter (`backend/middleware.py`) applied as Starlette middleware:

| Endpoint Pattern | Limit | Window |
|-----------------|-------|--------|
| `/api/evaluate/{disease}` | 5 requests | 60 seconds |
| `/api/*` (other endpoints) | 20 requests | 60 seconds |
| Non-API routes (`/health`, etc.) | No limit | — |

Keyed by client IP (with `X-Forwarded-For` awareness). Returns HTTP 429 with `Retry-After` header on breach. Configurable via constructor parameters for staging vs production tuning.

---

## API Documentation (OpenAPI / Swagger)

FastAPI automatically generates OpenAPI 3.0 documentation available at:
- **Swagger UI**: `http://localhost:8000/docs` — interactive API explorer
- **ReDoc**: `http://localhost:8000/redoc` — read-optimized documentation
- **OpenAPI JSON**: `http://localhost:8000/openapi.json` — machine-readable schema

All endpoint parameters, response models, and error codes are documented via FastAPI's type annotations and Pydantic models. External consumers can use the OpenAPI spec to generate client SDKs in any language.

---

## LLM Provider

All LLM calls go through `backend/services/llm.py`, which exposes `ask_llm()` and `ask_llm_json()`. The current provider is **Google Gemini 2.0 Flash** via the `google-genai` SDK. Legacy function aliases (`ask_claude`, `ask_claude_json`) remain for backwards compatibility — the codebase was initially prototyped with Anthropic Claude before switching to Gemini for its generous free tier.

The LLM is used **only** for:
1. Disease biology summaries (natural language from structured target data)
2. Drug candidate narrative rationales (from raw clinical trial records)
3. Literature evidence summaries (from PubMed abstracts)
4. Grant abstract drafting (from cached structured evidence)
5. Supplementary contradiction reasoning (optional, alongside the deterministic DeBERTa NLI)

The LLM is **never** used for scoring, safety classification, or data retrieval.

---

## Result Cache Architecture

Pipeline results are stored in a thread-safe `ResultCache` singleton (`backend/cache.py`), accessed via `get_result_cache()`. Endpoints like `/api/grant-abstract` and `/api/related-diseases` import the cache directly rather than reaching into `main.py` globals — this eliminates circular import risks and enables clean dependency injection.

```python
class ResultCache:
    """Thread-safe in-process cache keyed by disease name (lowercased)."""
    def get(self, disease_name: str) -> EvaluationResult | None: ...
    def put(self, disease_name: str, result: EvaluationResult) -> None: ...
```

The cache has a configurable max-entry limit (default 50) with FIFO eviction. For production multi-user deployment, this would be replaced by Redis with TTL-based expiration — the `ResultCache` interface is designed as a drop-in swap target.

---

## Dual Pipeline Architecture: main.py vs. orchestrator.py

PharmaSynapse contains **two distinct pipelines** that serve different purposes:

### Pipeline 1: Drug Repurposing SSE Pipeline (`main.py`)

The **primary user-facing pipeline** — a sequential async generator in `main.py` that orchestrates 5 agents via SSE streaming. This pipeline:
- Takes a disease name as input
- Queries 6 real external APIs (Open Targets, ClinicalTrials.gov, ChEMBL, FDA FAERS, PubMed, PubChem)
- Returns ranked drug candidates with evidence scores
- Streams results to the frontend in real-time via Server-Sent Events
- **Does NOT use LangGraph** — it is a hand-written async generator chosen for fine-grained SSE event control

### Pipeline 2: Molecular Screening Pipeline (`orchestrator.py`)

A **separate experimental pipeline** built with LangGraph for molecular candidate evaluation:
- Uses LangGraph's `StateGraph` with conditional edges for branching logic (toxicity → fail, clean → evaluate → approve/reject)
- Evaluates SMILES-format molecular candidates against BACE1 binding affinity (BACE dataset), toxicity (ClinTox dataset), and inter-agent contradiction (DeBERTa NLI)
- Uses ChromaDB vector store (`memory_store.py`) for RAG-based retrieval of previously failed molecules
- Operates on local CSV datasets (ZINC subset, ClinTox, BACE binding), not external APIs
- **LangGraph is essential here**: The conditional routing (after_admet → fail vs evaluate, after_evaluation → fail vs approve) and the stateful `MoleculeState` propagation across nodes are exactly what LangGraph's StateGraph provides over a plain async generator

### Why Two Pipelines?

| Aspect | SSE Pipeline (main.py) | Molecular Pipeline (orchestrator.py) |
|--------|------------------------|--------------------------------------|
| Purpose | Disease → drug candidate discovery | Molecular candidate screening |
| Data sources | 6 external APIs | Local CSV datasets |
| Architecture | Sequential async generator | LangGraph StateGraph with conditional edges |
| State | Per-request, ephemeral | MoleculeState TypedDict with agent logs |
| Memory | ResultCache singleton | ChromaDB vector store (RAG for past failures) |
| NLI usage | Safety vs efficacy contradiction | Inter-agent claim contradiction |
| User interface | SSE streaming to frontend | Programmatic (no UI yet) |

The molecular pipeline demonstrates LangGraph's value for complex branching workflows — it would be significantly more verbose without LangGraph's declarative graph construction and conditional edge routing. The SSE pipeline remains a hand-written generator because SSE event emission requires precise control over when and what events are yielded, which is more natural as an async generator than a graph node.

---

## Architectural Note: memory_store.py

`backend/memory_store.py` contains a ChromaDB-based vector store for failed experiment retrieval (RAG pattern). It is **wired into the LangGraph molecular pipeline** (`orchestrator.py`) where it stores failed molecule SMILES with failure reasons and retrieves past failures to guide the generative agent away from known-bad candidates. It is **not connected to the primary SSE drug repurposing pipeline** — the active user-facing session strategy uses browser localStorage. For production multi-user deployment, this would transition to a Redis-backed store with TTL-based expiration.

---

## 3D Molecule Editor

`MoleculeEditor.tsx` provides an interactive 3D molecular structure editor accessible from every drug card via the "Edit molecule" button.

**Architecture:**
- Fetches the drug's 3D SDF structure from PubChem REST API (falls back to 2D if unavailable)
- Parses V2000 MOL/SDF format into an atom/bond graph
- Renders atoms as `meshPhongMaterial` spheres (CPK color convention) and bonds as cylinders (with double/triple bond rendering via parallel offset cylinders)
- Uses `@react-three/fiber` Canvas with `OrbitControls` for rotation/zoom
- State management via `useReducer` with a full undo/redo history stack
- Atom placement uses a neighbor-direction heuristic to find sterically free positions

**Editing tools:** Select, Add Atom, Bond, Delete
**Element palette:** C, N, O, S, H, F, Cl, P, Br
**Export:** Modified structures can be downloaded as standard `.sdf` files

**UX integration:** Renders as a centered popup modal matching the app's white minimalist theme (not a full-screen takeover). Closes via X button, Escape key, or backdrop click.
