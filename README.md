

# PharmaSynapse

**An AI-powered multi-agent drug repurposing engine that cross-references 6 biomedical databases in real-time to identify abandoned clinical trial drugs that could treat rare diseases — for free.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)

---

## Why This Exists

**7,000+ rare diseases** affect **400 million people** globally. **95% have zero FDA-approved treatments.**

Meanwhile, pharmaceutical companies have spent **billions** on drugs that passed human safety trials but were shelved because they didn't work for their *original* target disease. Many of these drugs could work for something else — but the data is scattered across 6 disconnected government databases.

The commercial tools that do this cross-referencing (Clarivate, Elsevier, BenchSci) cost **$10,000–$50,000/year per researcher**. A grad student can't afford that. A rare disease foundation can't afford that.

**PharmaSynapse queries the same public databases for free, in 60 seconds, with transparent scoring and full source attribution.**

---

## What It Does

You type a disease name. Five specialized AI agents work in sequence, querying real biomedical databases:

```
User searches: "Huntington Disease"
        │
        ▼
┌─────────────────┐     Open Targets GraphQL API
│ Disease Analyst │────▶ Identifies 5 protein targets (HTT, BDNF, GRIA1...)
└────────┬────────┘
         ▼
┌─────────────────┐     ClinicalTrials.gov API + ChEMBL REST API
│   Drug Hunter   │────▶ Finds 4 shelved drugs that target those proteins
└────────┬────────┘
         ▼
┌─────────────────┐     FDA FAERS (openFDA) API
│ Safety Checker  │────▶ Evaluates real-world adverse events for each drug
└────────┬────────┘
         ▼
┌─────────────────┐     PubMed E-utilities (NCBI)
│ Evidence Agent  │────▶ Finds 12 supporting papers with abstracts
└────────┬────────┘
         ▼
┌─────────────────┐     DeBERTa NLI Model (local)
│  Contradiction  │────▶ Flags when safety data conflicts with efficacy claims
│    Detector     │
└────────┬────────┘
         ▼
   Ranked candidates with transparent 0-100 evidence scores
   Every claim links to its source database
```

### Evidence Scoring — No Black Box

Every drug candidate receives a **transparent, deterministic evidence score** (0–100) with no LLM involvement in scoring:

| Component | Max Points | Source |
|-----------|-----------|--------|
| Target Association | 30 | Open Targets disease-gene association strength |
| Trial Phase | 25 | How far the drug progressed in human trials |
| Literature Support | 25 | Number of PubMed papers on this drug-disease pair |
| Safety Profile | 20 | FDA FAERS adverse event analysis |

The score breakdown is visible on every drug card. Researchers can see exactly *why* a drug ranked where it did.

---

## Key Features

### Research Workbench (not just a search engine)

| Feature | Description |
|---------|-------------|
| **Persistent Sessions** | Research auto-saves to browser localStorage. Return days later and pick up where you left off. |
| **Star & Annotate** | Mark drugs as promising, add research notes per candidate. Starred drugs sort to top. |
| **Deep-Dive Panel** | Slide-out panel with up to 20 PubMed papers (with abstracts), all clinical trials for a drug, and full FDA adverse event data |
| **Side-by-Side Comparison** | Select two drugs and compare scores, safety, evidence, mechanism in a two-column modal |
| **PDF Report Export** | Generate a formatted, multi-page PDF report with title page, executive summary, per-drug analysis, citations, and methodology — ready for a grant proposal |
| **JSON Export** | Structured data export for computational pipelines |
| **Grant Abstract Generator** | AI-drafted NIH R21 Specific Aims paragraph from your evidence, editable and copy-to-clipboard |
| **Related Diseases** | Discover diseases sharing protein targets — click to explore cross-disease drug overlap |
| **3D Molecule Editor** | Click "Edit molecule" on any drug to open an interactive 3D editor — add atoms, draw bonds, delete, undo/redo, export modified structures as .SDF |
| **Disease Autocomplete** | Real-time suggestions from Open Targets as you type, plus search history |

### Technical Capabilities

| Feature | Description |
|---------|-------------|
| **Multi-Agent Pipeline** | 5 specialized agents with real-time SSE streaming |
| **6 Data Sources** | Open Targets, ClinicalTrials.gov, FDA FAERS, PubMed, ChEMBL, PubChem |
| **3D Molecule Visualization** | Interactive 3Dmol.js rendering of drug structures from PubChem |
| **3D Molecular Editor** | React Three Fiber editor — load PubChem SDF, modify atoms/bonds, export .SDF files |
| **Interactive 3D Hero** | Three.js molecular scene with orbital controls |
| **Contradiction Detection** | DeBERTa NLI model catches logical conflicts between agents |
| **Graceful Degradation** | Every agent handles API failures without crashing the pipeline |
| **Rule-Based Safety** | No LLM in safety classification — deterministic rules on FDA data |
| **120+ Passing Tests** | Backend: pytest (scoring, safety, models, cache, endpoints, NLI, API contracts, orchestrator). Frontend: Vitest (sessions, type contracts) |
| **CI/CD Pipeline** | GitHub Actions: `pytest` + `next build` on every push and PR |
| **Docker Ready** | Multi-stage Dockerfiles + `docker-compose up` with health checks |

---

## Screenshots

### Landing Page
Interactive Three.js molecular scene with disease search and autocomplete.

### Results View
Drug candidates with evidence score breakdowns, 3D molecule structures, PubMed citations, safety verdicts, star/notes controls, and comparison checkboxes.

### Deep-Dive Panel
Slide-out panel with three tabs: full literature (20 papers with abstracts), all clinical trials, and complete adverse event data.

### PDF Report
Multi-page formatted report with title page, executive summary, per-drug analysis with scores and citations, methodology, and researcher notes.

---

## Tech Stack

### Backend (Python)

| Technology | Purpose |
|-----------|---------|
| **FastAPI** | Async web framework with automatic OpenAPI docs |
| **Uvicorn** | ASGI server |
| **Pydantic** | Type-safe data models for all API contracts |
| **httpx** | Async HTTP client for 6 external APIs |
| **LangGraph** | Multi-agent pipeline orchestration |
| **Transformers + PyTorch** | Local DeBERTa NLI model for contradiction detection |
| **Sentence Transformers + ChromaDB** | Vector embeddings for semantic search |
| **Google Generative AI** | Gemini 2.0 Flash for natural-language synthesis |

### Frontend (TypeScript)

| Technology | Purpose |
|-----------|---------|
| **Next.js 16** | React framework with SSR and Turbopack |
| **React 19** | UI library |
| **TypeScript 5** | Type safety across 15+ components |
| **Tailwind CSS 4** | Utility-first styling |
| **Framer Motion** | Animations and transitions |
| **Three.js / @react-three/fiber** | Interactive 3D molecular scene |
| **3Dmol.js** | PubChem molecular structure rendering |
| **@react-pdf/renderer** | Client-side PDF generation |
| **Lucide React** | Icon system |

### External APIs (all free, no paywalls)

| API | Data Provided |
|-----|---------------|
| **Open Targets Platform** | Disease-gene associations via GraphQL |
| **ClinicalTrials.gov v2** | Clinical trial data (terminated/withdrawn) |
| **ChEMBL REST API** | Drug-target binding data |
| **FDA FAERS (openFDA)** | Post-market adverse event reports |
| **PubMed E-utilities** | Biomedical literature with abstracts |
| **PubChem REST API** | Molecular structure data (SDF) |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 16 + TypeScript)                │
│                                                                          │
│  Dashboard ─── DrugCard ─── MoleculeViewer ─── HeroScene (Three.js)    │
│     │              │                                                     │
│  SessionSidebar  DrugDetailPanel  CompareView  PDFReport                │
│     │              │                  │            │                     │
│  localStorage    useEventStream (SSE)              @react-pdf/renderer  │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │ Server-Sent Events
┌──────────────────────────▼───────────────────────────────────────────────┐
│                        BACKEND (FastAPI + Python)                         │
│                                                                          │
│  /api/evaluate/{disease}     SSE streaming pipeline                      │
│  /api/drug-detail/{drug}     Deep-dive expanded data                     │
│  /api/suggest/{query}        Autocomplete via Open Targets               │
│  /api/export/{disease}       Structured JSON report                      │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Disease Analyst → Drug Hunter → Safety Checker → Evidence Agent │   │
│  │                                       → Contradiction Detector  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                           │                                              │
│         ┌─────────────────┼─────────────────┐                           │
│         ▼                 ▼                 ▼                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │
│  │ Open Targets│  │ClinicalTrials│  │  FDA FAERS  │                    │
│  │  (GraphQL)  │  │   .gov v2   │  │  (openFDA)  │                    │
│  └─────────────┘  └─────────────┘  └─────────────┘                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │
│  │   ChEMBL    │  │   PubMed    │  │   PubChem   │                    │
│  │  REST API   │  │ E-utilities │  │  REST API   │                    │
│  └─────────────┘  └─────────────┘  └─────────────┘                    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API key (free tier: [aistudio.google.com](https://aistudio.google.com))

### Setup

```bash
# Clone
git clone https://github.com/vedanthchamala/pharmasynapse.git
cd pharmasynapse

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set your API key
export GOOGLE_API_KEY=your_gemini_key_here

# Start backend
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** and search for any disease.

### Try These Searches
- **Huntington Disease** — neurodegenerative with multiple drug targets
- **Cystic Fibrosis** — well-characterized genetic disease
- **Amyotrophic Lateral Sclerosis** — complex motor neuron disease
- **Duchenne Muscular Dystrophy** — rare pediatric condition

---

## Project Structure

```
pharmasynapse/
├── README.md
├── docs/                           # Comprehensive documentation (12 files)
│   ├── VISION.md                   # Mission and long-term goals
│   ├── PROBLEM_DEFINITION.md       # The rare disease treatment gap
│   ├── TECHNICAL_ARCHITECTURE.md   # System design and data flow
│   ├── IMPLEMENTATION_PLAN.md      # Development roadmap
│   ├── USER_EXPERIENCE.md          # UI/UX design decisions
│   ├── SCALABILITY.md              # Performance and scaling
│   ├── SECURITY.md                 # Security architecture
│   ├── TESTING_STRATEGY.md         # QA approach
│   ├── DEPLOYMENT.md               # Deployment options
│   ├── IMPACT.md                   # Social impact analysis
│   └── CODE_QUALITY.md             # Standards and patterns
│
├── backend/
│   ├── main.py                     # FastAPI app, SSE pipeline, export endpoint
│   ├── models.py                   # Pydantic models (EvidenceScore, DrugCandidate, etc.)
│   ├── agents/
│   │   ├── disease_analyst.py      # Open Targets integration
│   │   ├── drug_hunter.py          # ClinicalTrials.gov + ChEMBL + evidence scoring
│   │   ├── safety_checker.py       # FDA FAERS rule-based assessment
│   │   ├── evidence_agent.py       # PubMed literature mining
│   │   └── contradiction.py        # DeBERTa NLI contradiction detection
│   ├── cache.py                    # Thread-safe ResultCache singleton (DI-friendly)
│   ├── endpoints/
│   │   ├── drug_detail.py          # Deep-dive expanded data endpoint
│   │   ├── suggest.py              # Autocomplete via Open Targets search
│   │   ├── grant_abstract.py       # LLM-drafted NIH R21 grant abstract
│   │   └── related_diseases.py     # Shared protein target disease network
│   ├── tests/                      # 100+ passing tests (pytest)
│   │   ├── test_scoring.py         # Evidence score formula validation
│   │   ├── test_safety.py          # Rule-based safety classification
│   │   ├── test_models.py          # Pydantic model contracts
│   │   ├── test_cache.py           # ResultCache singleton + eviction
│   │   ├── test_endpoints.py       # Integration tests (TestClient + mocks)
│   │   └── test_contradiction_engine.py  # DeBERTa NLI contract tests
│   └── services/
│       ├── llm.py                  # Gemini API wrapper (graceful fallback)
│       ├── open_targets.py         # GraphQL client
│       ├── clinical_trials.py      # ClinicalTrials.gov v2 REST client
│       ├── chembl.py               # ChEMBL REST client with name resolution
│       ├── faers.py                # FDA FAERS client
│       └── pubmed.py               # NCBI E-utilities client
│
└── frontend/
    ├── package.json                # Next.js 16, React 19, Three.js, @react-pdf/renderer
    └── src/
        ├── app/                    # Next.js app router
        ├── components/
        │   ├── Dashboard.tsx       # Main UI orchestration (600+ lines)
        │   ├── MoleculeViewer.tsx  # 3Dmol.js with PubChem SDF rendering
        │   ├── HeroScene.tsx       # Three.js interactive molecular scene
        │   ├── DrugDetailPanel.tsx  # Slide-out deep-dive panel
        │   ├── CompareView.tsx     # Side-by-side drug comparison modal
        │   ├── MoleculeEditor.tsx  # 3D molecular editor (R3F, SDF import/export)
        │   ├── GrantAbstractModal.tsx  # LLM-drafted grant abstract editor
        │   ├── RelatedDiseases.tsx # Shared protein target disease cards
        │   └── PDFReport.tsx       # @react-pdf/renderer multi-page template
        ├── hooks/
        │   └── useEventStream.ts   # SSE consumer with typed state
        └── lib/
            ├── diseaseTypes.ts     # TypeScript interfaces for all data models
            └── sessions.ts         # localStorage session management
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/evaluate/{disease}` | GET | SSE streaming pipeline — runs all 5 agents |
| `/api/drug-detail/{drug}?disease={disease}` | GET | Expanded data: 20 papers, all trials, full FAERS |
| `/api/suggest/{query}` | GET | Disease autocomplete from Open Targets |
| `/api/export/{disease}` | GET | Structured JSON report with methodology |
| `/api/grant-abstract/{drug}?disease={disease}` | GET | LLM-drafted NIH R21 specific aims from cached evidence |
| `/api/related-diseases/{disease}` | GET | Diseases sharing protein targets (reverse Open Targets lookup) |
| `/health` | GET | Service health check |

---

## How AI Is Used (Transparently)

PharmaSynapse uses AI in **two specific, auditable ways**:

1. **Google Gemini (LLM)** — Synthesizes raw data into plain-English explanations: *why* a drug might work, what the mechanism is, what the rationale for repurposing is. The LLM reads real data (trial records, abstracts, target associations) and summarizes it. If Gemini is unavailable, the pipeline still works with raw data.

2. **DeBERTa NLI (local model, no API)** — A Hugging Face natural language inference model that runs locally to detect contradictions between agent outputs (e.g., "Drug X is safe for cardiac patients" vs. "Drug X causes cardiac failure in FDA reports").

**What AI does NOT do:**
- Scoring is 100% deterministic — no LLM involved
- Safety classification is rule-based — predefined high-risk terms against FDA data
- All claims trace to specific database records, not LLM generation

---

## The Cost Comparison

| Tool | Annual Cost | What PharmaSynapse Replaces |
|------|------------|----------------------------|
| Clarivate Cortellis | ~$30,000/seat | Drug pipeline cross-referencing |
| Elsevier Pathway Studio | ~$15,000/seat | Target-drug-disease mapping |
| BenchSci | ~$20,000/seat | Literature + antibody search |
| **PharmaSynapse** | **$0** | **All of the above, from the same public databases** |

Every API we query is free. The pipeline runs on a laptop. A college researcher with no budget gets the same cross-database analysis that costs pharma companies tens of thousands per year.

---

## Impact

- **For Patients**: Hope where 95% of rare diseases have no treatment
- **For Researchers**: Weeks of manual database cross-referencing → 60 seconds
- **For Institutions**: PDF reports ready for grant proposals
- **For Pharma**: Identify new life for shelved assets worth billions in R&D
- **For Society**: Democratizing drug discovery — no paywall, no login, open source

---

## Documentation

Comprehensive documentation in the [`docs/`](./docs/) directory:

| Document | Contents |
|----------|----------|
| [Vision](docs/VISION.md) | Mission, goals, success metrics |
| [Problem Definition](docs/PROBLEM_DEFINITION.md) | Rare disease crisis analysis |
| [Technical Architecture](docs/TECHNICAL_ARCHITECTURE.md) | System design, agent inventory, data flow |
| [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) | Development roadmap and decisions |
| [User Experience](docs/USER_EXPERIENCE.md) | UI/UX design and interaction patterns |
| [Scalability](docs/SCALABILITY.md) | Performance optimization |
| [Security](docs/SECURITY.md) | Security architecture and threat model |
| [Testing Strategy](docs/TESTING_STRATEGY.md) | Testing approach and CI pipeline |
| [Deployment](docs/DEPLOYMENT.md) | Deployment options and Docker setup |
| [Impact](docs/IMPACT.md) | Social impact and sustainability |
| [Validation](docs/VALIDATION.md) | Empirical validation against known repurposings |
| [Code Quality](docs/CODE_QUALITY.md) | Standards and patterns |

---

## Team

| Member | Role | Ownership |
|--------|------|-----------|
| **Vedanth Chamala** | Full-stack lead | Backend pipeline, API design, agent architecture |
| **Keshav Singh** | Frontend & AI integration | Next.js UI, 3D visualization, LLM integration, research workbench |

---

## License

MIT License — free for academic, research, and commercial use.

---

## Acknowledgments

- **Open Targets Platform** — disease-target association data
- **ClinicalTrials.gov** — clinical trial records
- **FDA** — FAERS adverse event reporting system
- **NCBI** — PubMed literature database
- **EMBL-EBI** — ChEMBL drug-target data
- **PubChem** — molecular structure data
- **Google** — Gemini API for natural language synthesis
- Every rare disease patient advocate working for a cure



https://github.com/user-attachments/assets/dd884dc1-e1b2-409c-9908-c4d15069424e


