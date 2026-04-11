# Code Quality

## Standards & Patterns

PharmaSynapse maintains high code quality through TypeScript strict mode, Pydantic validation, and consistent patterns across the codebase.

---

## Python Backend Standards

### Type Hints Throughout
Every function has type hints:
```python
async def hunt_drugs(
    disease_name: str,
    targets: list[DiseaseTarget],
    disease_summary: str,
) -> list[DrugCandidate]:
```

### Pydantic Data Models
All data exchange uses validated Pydantic models:
```python
class EvidenceScore(BaseModel):
    target_association: int   # 0-30
    trial_evidence: int       # 0-25
    literature_support: int   # 0-25
    safety_profile: int       # 0-20
    total: int                # 0-100
    breakdown: str
```

### Async Patterns
All external API calls are async:
```python
async with httpx.AsyncClient(timeout=15) as client:
    resp = await client.get(url, params=params)
```

### Graceful Error Handling
Every agent wraps external calls:
```python
try:
    result = await external_api_call()
except Exception as e:
    log.error("Agent error: %s", e)
    result = []  # Never crash the pipeline
```

### Separation of Concerns
```
backend/
├── main.py          # API layer + SSE pipeline orchestration
├── models.py        # Data models only (Pydantic)
├── cache.py         # Thread-safe ResultCache singleton (DI-friendly)
├── agents/          # Business logic (one agent per file)
├── endpoints/       # Additional REST endpoints (import cache, not main)
├── services/        # External API wrappers (one per API)
└── tests/           # 78 pytest tests (zero external API calls)
```

Endpoints never import mutable state from `main.py` — they access the `ResultCache` singleton via `get_result_cache()`, eliminating circular import risks and enabling clean dependency injection.

---

## TypeScript Frontend Standards

### Strict TypeScript
All components are TypeScript with strict mode:
```typescript
interface DrugCardProps {
  drug: DrugCandidate;
  safety?: SafetyAssessment;
  evidence?: EvidenceSummary;
  rank: number;
  isStarred: boolean;
  onToggleStar: () => void;
  note: string;
  onNoteChange: (note: string) => void;
}
```

### Shared Type Definitions
`diseaseTypes.ts` defines interfaces matching backend Pydantic models:
```typescript
export interface EvidenceScore {
  target_association: number;
  trial_evidence: number;
  literature_support: number;
  safety_profile: number;
  total: number;
  breakdown: string;
}
```

### React Patterns
- Functional components with hooks
- `useMemo` for expensive computations (safety maps, sorted candidates)
- `useCallback` for stable function references
- `useEffect` with cleanup for async operations
- Dynamic imports (`next/dynamic`) for heavy components (Three.js, 3Dmol.js, PDF)

### Component Structure
```
Dashboard.tsx (orchestrator)
├── State management (useState, useMemo, useEffect)
├── Event handlers (search, star, note, compare)
├── Render: header, sidebar, search, results
└── Sub-components:
    ├── PipelineProgress (animation)
    ├── DrugCard (complex, 100+ lines)
    ├── ScorePill (reusable)
    ├── DetailBlock (reusable)
    ├── SourceBadge (reusable)
    └── AgentLog (expandable)
```

---

## Architecture Principles

1. **Single Responsibility**: Each file/function does one thing
2. **Explicit Over Implicit**: Clear naming, no magic strings
3. **Fail Gracefully**: Every external call has a fallback
4. **Type Everything**: Pydantic (Python) + TypeScript (frontend)
5. **No LLM in Critical Paths**: Scoring and safety are deterministic
6. **Source Attribution**: Every data point traces to a database
7. **Client-Side First**: Sessions, PDF generation, and 3D rendering happen in the browser
