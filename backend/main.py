"""
FastAPI entry point for PharmaSynapse.
- Disease-search drug-repurposing pipeline (SSE streaming)
- Evidence-based scoring with real data sources
- JSON export endpoint
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv(Path(__file__).resolve().parent / ".env")

import os

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from backend.middleware import RateLimitMiddleware
from backend.agents.disease_analyst import analyze_disease
from backend.agents.drug_hunter import hunt_drugs, compute_evidence_score
from backend.agents.safety_checker import check_safety
from backend.agents.contradiction import check_contradictions
from backend.agents.evidence_agent import gather_evidence
from backend.models import EvaluationResult
from backend.cache import get_result_cache
from backend.endpoints.drug_detail import router as drug_detail_router
from backend.endpoints.suggest import router as suggest_router
from backend.endpoints.grant_abstract import router as grant_abstract_router
from backend.endpoints.related_diseases import router as related_diseases_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="PharmaSynapse API", version="2.0.0", lifespan=lifespan)

_allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(RateLimitMiddleware, evaluate_limit=5, general_limit=20, window_seconds=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(drug_detail_router)
app.include_router(suggest_router)
app.include_router(grant_abstract_router)
app.include_router(related_diseases_router)


def _sse_event(agent: str, status: str, message: str, data: dict | None = None) -> str:
    payload = {"agent": agent, "status": status, "message": message}
    if data is not None:
        payload["data"] = data
    return f"data: {json.dumps(payload)}\n\n"


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "PharmaSynapse", "version": "2.0.0"}


@app.get("/api/evaluate/{disease_name}")
async def evaluate_disease(disease_name: str):
    """SSE streaming endpoint — runs the full repurposing pipeline. No fake fallbacks."""

    async def event_stream():
        data_sources = []

        # --- Agent 1: Disease Analyst (Open Targets) ---
        yield _sse_event("disease_analyst", "working", f"Searching Open Targets for {disease_name}...")

        try:
            targets, disease_summary, efo_id = await analyze_disease(disease_name)
        except Exception as e:
            log.error("Disease analyst error: %s", e)
            targets, disease_summary, efo_id = [], "", ""

        if targets:
            data_sources.append("Open Targets Platform")
        else:
            disease_summary = (
                f"No known protein targets found for '{disease_name}' in the Open Targets database. "
                f"This may mean the disease uses a different name, is very recently described, "
                f"or has limited genomic association data. Try alternative names or broader terms."
            )

        yield _sse_event("disease_analyst", "complete",
            f"Found {len(targets)} protein targets for {disease_name}." if targets
            else f"No targets found for '{disease_name}' in Open Targets.",
            {
                "disease_summary": disease_summary,
                "targets": [t.model_dump() for t in targets],
            })

        # --- Agent 2: Drug Hunter (ClinicalTrials.gov + ChEMBL) ---
        yield _sse_event("drug_hunter", "working", "Searching ClinicalTrials.gov and ChEMBL...")

        try:
            candidates = await hunt_drugs(disease_name, targets, disease_summary)
        except Exception as e:
            log.error("Drug hunter error: %s", e)
            candidates = []

        if candidates:
            trial_sources = set()
            for c in candidates:
                trial_sources.update(c.sources)
            data_sources.extend(trial_sources)

        yield _sse_event("drug_hunter", "complete",
            f"Found {len(candidates)} repurposing candidates." if candidates
            else "No drug candidates found from clinical trials or target databases.",
            {"candidates": [c.model_dump() for c in candidates]})

        # --- Agent 3: Safety Checker (FDA FAERS) ---
        yield _sse_event("safety_checker", "working", "Checking FDA FAERS for adverse events...")

        if candidates:
            try:
                safety_assessments = await check_safety(candidates, disease_name, disease_summary)
            except Exception as e:
                log.error("Safety checker error: %s", e)
                safety_assessments = []
            if safety_assessments:
                data_sources.append("FDA FAERS (openFDA)")
        else:
            safety_assessments = []

        # Update evidence scores with safety verdicts
        safety_map = {sa.drug_name: sa for sa in safety_assessments}
        for c in candidates:
            sa = safety_map.get(c.drug_name)
            if sa and c.evidence_score:
                updated = compute_evidence_score(
                    c.evidence_score.target_association / 30,
                    c.phase,
                    c.evidence_score.literature_support,  # will be updated after evidence agent
                    sa.verdict.value,
                )
                c.evidence_score = updated
                c.confidence = updated.total / 100

        yield _sse_event("safety_checker", "complete",
            f"Safety evaluation done for {len(safety_assessments)} drugs.",
            {"safety_assessments": [s.model_dump() for s in safety_assessments]})

        # --- Agent 4: Evidence Agent (PubMed) ---
        yield _sse_event("evidence_agent", "working", "Searching PubMed for supporting literature...")

        evidence_summaries = []
        if candidates:
            try:
                evidence_summaries = await gather_evidence(candidates, disease_name)
            except Exception as e:
                log.error("Evidence agent error: %s", e)

            if evidence_summaries:
                data_sources.append("PubMed / NCBI")

                # Final score update with literature counts
                ev_map = {es.drug_name: es for es in evidence_summaries}
                for c in candidates:
                    es = ev_map.get(c.drug_name)
                    sa = safety_map.get(c.drug_name)
                    if es and c.evidence_score:
                        updated = compute_evidence_score(
                            c.evidence_score.target_association / 30,
                            c.phase,
                            es.paper_count,
                            sa.verdict.value if sa else "",
                        )
                        c.evidence_score = updated
                        c.confidence = updated.total / 100

        # Re-sort after final scores
        candidates.sort(key=lambda c: c.evidence_score.total if c.evidence_score else 0, reverse=True)

        yield _sse_event("evidence_agent", "complete",
            f"Found literature for {sum(1 for e in evidence_summaries if e.paper_count > 0)} drugs.",
            {"evidence_summaries": [e.model_dump() for e in evidence_summaries]})

        # --- Contradiction Check ---
        yield _sse_event("contradiction", "working", "Running contradiction analysis...")

        try:
            contradictions = await check_contradictions(
                disease_name, disease_summary, targets, candidates, safety_assessments,
            )
        except Exception as e:
            log.error("Contradiction check error: %s", e)
            contradictions = []

        yield _sse_event("contradiction", "complete",
            f"Found {len(contradictions)} contradiction(s)." if contradictions
            else "No contradictions detected.",
            {"contradictions": [c.model_dump() for c in contradictions]})

        # --- Final result ---
        data_sources = list(dict.fromkeys(data_sources))  # deduplicate preserving order
        result = EvaluationResult(
            disease_name=disease_name,
            disease_summary=disease_summary,
            targets=targets,
            candidates=candidates,
            safety_assessments=safety_assessments,
            contradictions=contradictions,
            evidence_summaries=evidence_summaries,
            data_sources=data_sources,
        )

        get_result_cache().put(disease_name, result)

        yield _sse_event("system", "complete", "Evaluation complete.", result.model_dump())

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/export/{disease_name}")
async def export_report(disease_name: str):
    """Export the last evaluation as structured JSON."""
    result = get_result_cache().get(disease_name)
    if not result:
        return JSONResponse(
            status_code=404,
            content={"error": f"No evaluation found for '{disease_name}'. Run a search first."},
        )

    report = {
        "report_title": f"Drug Repurposing Report: {result.disease_name}",
        "disclaimer": (
            "This is a computational research exploration tool. Results are generated from "
            "public databases (Open Targets, ClinicalTrials.gov, FDA FAERS, PubMed, ChEMBL) "
            "and should not be interpreted as medical advice. All findings require validation "
            "through proper clinical and regulatory processes."
        ),
        "data_sources": result.data_sources,
        "disease": {
            "name": result.disease_name,
            "summary": result.disease_summary,
            "targets": [t.model_dump() for t in result.targets],
        },
        "candidates": [],
        "contradictions": [c.model_dump() for c in result.contradictions],
        "methodology": {
            "step_1": "Disease target identification via Open Targets Platform GraphQL API",
            "step_2": "Drug candidate search via ClinicalTrials.gov API v2 (failed/withdrawn Phase 2/3) and ChEMBL REST API (drug-target binding)",
            "step_3": "Safety evaluation via FDA FAERS adverse event data (openFDA API), rule-based classification",
            "step_4": "Literature evidence via PubMed E-utilities (NCBI)",
            "step_5": "Contradiction detection via DeBERTa NLI model + rule-based logic",
            "scoring": "Evidence Score = Target Association (0-30) + Trial Phase (0-25) + Literature (0-25) + Safety (0-20)",
        },
    }

    ev_map = {es.drug_name: es for es in result.evidence_summaries}
    sa_map = {sa.drug_name: sa for sa in result.safety_assessments}

    for c in result.candidates:
        entry = c.model_dump()
        es = ev_map.get(c.drug_name)
        sa = sa_map.get(c.drug_name)
        if es:
            entry["literature"] = es.model_dump()
        if sa:
            entry["safety_detail"] = sa.model_dump()
        report["candidates"].append(entry)

    return JSONResponse(content=report)
