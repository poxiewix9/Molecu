"""Deep-dive endpoint for a single drug-disease pair."""

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.services.pubmed import search_pubmed, get_paper_summaries, get_abstracts
from backend.services.faers import get_adverse_events

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/drug-detail/{drug_name}")
async def drug_detail(drug_name: str, disease: str = ""):
    """Return expanded data for a single drug-disease pair."""

    pmids: list[str] = []
    papers: list[dict] = []
    abstracts: dict[str, str] = {}
    adverse_events: list[dict] = []
    all_trials: list[dict] = []

    # Full PubMed search (up to 20 papers)
    try:
        if disease:
            pmids = await search_pubmed(drug_name, disease, max_results=20)
            if pmids:
                papers = await get_paper_summaries(pmids)
                abstracts = await get_abstracts(pmids[:5])
    except Exception as e:
        log.warning("PubMed lookup failed for %s: %s", drug_name, e)

    # Full FAERS adverse events (up to 25)
    try:
        adverse_events = await get_adverse_events(drug_name, limit=25)
    except Exception as e:
        log.warning("FAERS lookup failed for %s: %s", drug_name, e)

    # All trials for this drug (not just failed)
    try:
        import httpx
        params = {
            "query.term": drug_name,
            "pageSize": "10",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://clinicaltrials.gov/api/v2/studies", params=params)
            if resp.status_code == 200:
                studies = resp.json().get("studies", [])
                for study in studies:
                    proto = study.get("protocolSection", {})
                    ident = proto.get("identificationModule", {})
                    status_mod = proto.get("statusModule", {})
                    design = proto.get("designModule", {})
                    phases = design.get("phases", [])
                    all_trials.append({
                        "trial_id": ident.get("nctId", ""),
                        "title": ident.get("briefTitle", ""),
                        "status": status_mod.get("overallStatus", ""),
                        "phase": ", ".join(phases) if phases else "Unknown",
                        "conditions": proto.get("conditionsModule", {}).get("conditions", []),
                    })
    except Exception as e:
        log.warning("Trial lookup failed for %s: %s", drug_name, e)

    return JSONResponse(content={
        "drug_name": drug_name,
        "disease": disease,
        "literature": {
            "total_papers": len(pmids),
            "papers": papers,
            "abstracts": abstracts,
        },
        "adverse_events": adverse_events,
        "all_trials": all_trials,
    })
