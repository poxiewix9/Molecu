# Testing Strategy

## Testing Philosophy

PharmaSynapse tests focus on **pipeline reliability** and **data integrity** — the two things that matter most for a research tool. A false positive drug candidate could waste months of a researcher's time.

---

## Testing Pyramid

```
                    ┌───────────────┐
                    │     E2E       │  ← Full pipeline: disease → candidates
                    │   Pipeline    │
                    └───────┬───────┘
                            │
                    ┌───────┴───────┐
                    │  Integration  │  ← Agent + service interaction
                    │    Tests      │
                    └───────┬───────┘
                            │
            ┌───────────────┴───────────────┐
            │         Unit Tests            │  ← Models, scoring, parsing
            └───────────────────────────────┘
```

---

## Implemented Test Suite

**78 tests across 6 files, all passing** (`pytest backend/tests/ -v`):

| File | Tests | Coverage |
|------|-------|----------|
| `test_scoring.py` | 20 | Evidence score formula: target (0-30), trial phase (0-25), literature (0-25), safety (0-20), total bounds, serialization |
| `test_safety.py` | 18 | Event classification, organ detection, high-risk terms, case sensitivity, verdict enum |
| `test_models.py` | 18 | Pydantic model validation, required fields, serialization roundtrip, empty/full evaluation |
| `test_cache.py` | 9 | ResultCache put/get, case-insensitive keys, max-entry eviction, singleton pattern |
| `test_endpoints.py` | 8 | Integration tests: health, export, grant-abstract (mock LLM), related-diseases (mock Open Targets), SSE evaluate (mock agents), 404 responses |
| `test_contradiction_engine.py` | 5 | DeBERTa NLI contract: required keys, high/low contradiction detection, score normalization, async thread-pool delegation |

Tests require **zero external API calls** — endpoint integration tests use FastAPI's `TestClient` with `unittest.mock.patch` to inject controlled responses.

```bash
$ pytest backend/tests/ -v
============================== 78 passed in 4.21s ==============================
```

---

## Test Categories

### 1. Evidence Scoring Tests (Implemented: `backend/tests/test_scoring.py`)
The scoring system is deterministic — the most testable part of the system.

```python
def test_evidence_score_computation():
    score = compute_evidence_score(
        target_score=0.8,     # Strong association
        phase="PHASE3",       # Advanced trial
        paper_count=5,        # Good literature
        safety_verdict="PASS" # Clean safety
    )
    assert score.target_association == 24  # 0.8 * 30
    assert score.trial_evidence == 25     # Phase 3 max
    assert score.literature_support == 25 # 5*5 capped at 25
    assert score.safety_profile == 20     # PASS = max
    assert score.total == 94
```

### 2. Safety Classification Tests (Implemented: `backend/tests/test_safety.py`)
Rule-based safety is fully testable:

```python
def test_high_risk_event_detection():
    events = [{"term": "cardiac failure", "count": 50}]
    verdict = classify_safety(events, disease_name="huntington")
    assert verdict == "HARD_FAIL"

def test_clean_safety_profile():
    events = [{"term": "headache", "count": 100}]
    verdict = classify_safety(events, disease_name="huntington")
    assert verdict == "PASS"
```

### 3. API Response Parsing Tests
Verify parsers handle real API responses correctly:

```python
def test_clinical_trials_parsing():
    raw_response = load_fixture("clinicaltrials_response.json")
    trials = parse_clinical_trials(raw_response)
    assert all(t["drug_names"] for t in trials)
    assert all(len(name) < 60 for t in trials for name in t["drug_names"])

def test_open_targets_parsing():
    raw_response = load_fixture("opentargets_response.json")
    targets = parse_targets(raw_response)
    assert all(0 <= t.association_score <= 1 for t in targets)
```

### 4. Data Model Validation Tests (Implemented: `backend/tests/test_models.py`)
Pydantic models enforce data contracts:

```python
def test_drug_candidate_model():
    candidate = DrugCandidate(
        drug_name="Idebenone",
        trial_id="NCT00229632",
        original_indication="Alzheimer's",
        phase="Phase 3",
        confidence=0.85,
        ...
    )
    assert candidate.drug_name == "Idebenone"

def test_invalid_confidence_rejected():
    with pytest.raises(ValidationError):
        DrugCandidate(confidence=1.5, ...)  # > 1.0
```

### 5. Pipeline Integration Tests

```python
@pytest.mark.asyncio
async def test_full_pipeline():
    async with AsyncClient(app=app, base_url="http://test") as client:
        async with client.stream("GET", "/api/evaluate/huntington") as resp:
            assert resp.status_code == 200
            events = []
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    events.append(json.loads(line[5:]))
            # Verify all agents reported
            agents = {e["agent"] for e in events}
            assert "disease_analyst" in agents
            assert "drug_hunter" in agents
            assert "safety_checker" in agents
            assert "system" in agents
```

---

## Frontend Testing

### TypeScript Type Safety
15+ components with full TypeScript interfaces:
- `diseaseTypes.ts` — all data model interfaces
- `sessions.ts` — session management types
- `useEventStream.ts` — SSE state type

### Component Testing Approach

```typescript
// Drug card renders score correctly
test('DrugCard shows evidence score breakdown', () => {
  render(<DrugCard drug={mockDrug} safety={mockSafety} ... />);
  expect(screen.getByText('72/100')).toBeInTheDocument();
  expect(screen.getByText('Target 20/30')).toBeInTheDocument();
});

// Session persistence
test('Sessions save and load from localStorage', () => {
  const session = createSessionFromResults(mockResults);
  saveSession(session);
  const loaded = getSession(session.id);
  expect(loaded?.disease_name).toBe(mockResults.disease_name);
});

// Molecule editor state management
test('MoleculeEditor undo/redo restores state', () => {
  // useReducer history stack: past/present/future
  dispatch({ type: 'addAtom', atom: newCarbon });
  dispatch({ type: 'undo' });
  expect(state.atoms.length).toBe(initialCount);
  dispatch({ type: 'redo' });
  expect(state.atoms.length).toBe(initialCount + 1);
});

// SDF parser round-trip
test('parseSDF → toSDF preserves atom/bond data', () => {
  const parsed = parseSDF(sampleSDF);
  const exported = toSDF(parsed.atoms, parsed.bonds);
  const reparsed = parseSDF(exported);
  expect(reparsed.atoms.length).toBe(parsed.atoms.length);
  expect(reparsed.bonds.length).toBe(parsed.bonds.length);
});
```

---

## Quality Gates

### CI/CD Pipeline (GitHub Actions — `.github/workflows/ci.yml`)

Runs on every push to `main` and every pull request:

| Job | Steps | Purpose |
|-----|-------|---------|
| `backend-tests` | Python 3.11 → `pip install` → `pytest backend/tests/ -v` | Validate scoring, safety, cache, endpoints, NLI |
| `frontend-build` | Node 20 → `npm ci` → `npm run build` (NODE_ENV=production) | TypeScript type-check + production compilation |

### Pre-Commit
- TypeScript compilation (strict mode)
- ESLint
- Python type hints
- No hardcoded API keys (verified by `grep` in push scripts)

### Build Verification
- `next build` succeeds (TypeScript + compilation)
- All Pydantic models validate
- All agent imports resolve
- 78 pytest tests pass with zero external API dependencies
