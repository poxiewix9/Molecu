"""ClinicalTrials.gov API v2 wrapper — searches for terminated/withdrawn Phase 2/3 trials."""

import httpx
import logging

log = logging.getLogger(__name__)

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"


async def search_failed_trials(gene_names: list[str], disease_name: str, max_results: int = 20) -> list[dict]:
    """Search for terminated or withdrawn Phase 2/3 trials related to given genes or disease."""
    query_string = disease_name

    params = {
        "query.term": query_string,
        "filter.overallStatus": "TERMINATED,WITHDRAWN",
        "pageSize": str(max_results),
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        studies = data.get("studies", [])
        results = []
        for study in studies:
            proto = study.get("protocolSection", {})
            ident = proto.get("identificationModule", {})
            status_mod = proto.get("statusModule", {})
            design = proto.get("designModule", {})
            arms = proto.get("armsInterventionsModule", {})

            interventions = arms.get("interventions", [])
            drug_names = [
                iv.get("name", "Unknown")
                for iv in interventions
                if iv.get("type", "").upper() in ("DRUG", "BIOLOGICAL", "COMBINATION_PRODUCT")
                and len(iv.get("name", "")) < 60
            ]

            phases = design.get("phases", [])
            phase_str = ", ".join(phases) if phases else "Unknown"

            results.append({
                "trial_id": ident.get("nctId", ""),
                "title": ident.get("briefTitle", ""),
                "drug_names": drug_names,
                "conditions": proto.get("conditionsModule", {}).get("conditions", []),
                "phase": phase_str,
                "status": status_mod.get("overallStatus", ""),
                "why_stopped": status_mod.get("whyStopped", "Not specified"),
            })

        return results
    except Exception as e:
        log.error("ClinicalTrials.gov search failed: %s", e)
        return []
