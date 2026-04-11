# PharmaSynapse Documentation

## Project Overview

**PharmaSynapse** is an AI-powered drug repurposing research workbench that identifies failed or shelved clinical trial drugs with potential to treat rare diseases. It cross-references 6 public biomedical databases in real-time, applies transparent evidence-based scoring, and provides a persistent research environment with PDF export, annotation, and comparison tools.

### The Problem We're Solving

Over 7,000 rare diseases affect 400+ million people globally, yet 95% have no FDA-approved treatment. Pharmaceutical companies have invested billions in drugs that failed clinical trials — many of which are safe and could work for different diseases. The tools that do this cross-database analysis cost $10,000–$50,000/year per seat, locking out the researchers who need them most.

**Our solution**: A free, open-source multi-agent AI system that queries the same public databases those commercial tools use, with transparent scoring and full source attribution — turning weeks of manual research into 60 seconds.

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [Vision](./VISION.md) | Product vision, mission, and long-term goals |
| [Problem Definition](./PROBLEM_DEFINITION.md) | Deep dive into the rare disease treatment gap |
| [Technical Architecture](./TECHNICAL_ARCHITECTURE.md) | System design, multi-agent orchestration, data flow |
| [Implementation Plan](./IMPLEMENTATION_PLAN.md) | Development roadmap, decisions, and milestones |
| [User Experience](./USER_EXPERIENCE.md) | UI/UX design decisions, research workbench features |
| [Scalability](./SCALABILITY.md) | Performance optimization and scaling strategy |
| [Security](./SECURITY.md) | Security measures and compliance considerations |
| [Testing Strategy](./TESTING_STRATEGY.md) | Testing approach and quality assurance |
| [Deployment](./DEPLOYMENT.md) | Deployment architecture and CI/CD |
| [Impact](./IMPACT.md) | Social impact, cost savings analysis, and sustainability |
| [Validation](./VALIDATION.md) | Empirical validation against known successful drug repurposings |
| [Code Quality](./CODE_QUALITY.md) | Coding standards and best practices |

---

## Quick Facts

- **Frontend**: Next.js 16 + TypeScript 5 + React 19 + Tailwind CSS 4 + Three.js + @react-pdf/renderer
- **Backend**: FastAPI + Python 3.10+ + Pydantic + LangGraph + Transformers (DeBERTa NLI)
- **LLM**: Google Gemini 2.0 Flash (with graceful fallback when unavailable)
- **Data Sources**: Open Targets, ClinicalTrials.gov, FDA FAERS, PubMed, ChEMBL, PubChem
- **Architecture**: Multi-agent SSE streaming pipeline with evidence-based scoring
- **Research Tools**: Persistent sessions, annotations, PDF reports, drug comparison, deep-dive panels
- **Cost to Researcher**: $0 — every API is free and public
- **Validation**: Empirically tested against known successful repurposings (see [VALIDATION.md](./VALIDATION.md))

---

## Key Innovation: Evidence-Based Multi-Agent Pipeline

PharmaSynapse implements a sequential multi-agent pipeline where each agent specializes in one data domain, queries a real external database, and produces structured, validated output:

```
Disease Analyst ──▶ Drug Hunter ──▶ Safety Checker ──▶ Evidence Agent ──▶ Contradiction Detector
(Open Targets)     (CT.gov +      (FDA FAERS)       (PubMed)          (DeBERTa NLI)
                    ChEMBL)
```

**What makes this different from a chatbot:**
- Every claim traces to a specific database record with a URL
- Scoring is 100% deterministic — no LLM involved in ranking
- Safety classification is rule-based against FDA data, not LLM opinion
- Contradictions are detected by a local NLI model, not hallucinated
- The pipeline works even when the LLM is unavailable
