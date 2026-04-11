"""Open Targets Platform GraphQL API wrapper."""

import httpx
import logging

log = logging.getLogger(__name__)

GRAPHQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"

SEARCH_DISEASE_QUERY = """
query SearchDisease($name: String!) {
  search(queryString: $name, entityNames: ["disease"], page: {index: 0, size: 5}) {
    hits {
      id
      name
      description
      entity
    }
  }
}
"""

DISEASE_TARGETS_QUERY = """
query DiseaseTargets($efoId: String!) {
  disease(efoId: $efoId) {
    id
    name
    description
    associatedTargets(page: {index: 0, size: 10}) {
      rows {
        target {
          id
          approvedSymbol
          approvedName
        }
        score
      }
    }
  }
}
"""

TARGET_DISEASES_QUERY = """
query TargetDiseases($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    associatedDiseases(page: {index: 0, size: 15}) {
      rows {
        disease {
          id
          name
        }
        score
      }
    }
  }
}
"""


async def search_disease(name: str) -> dict | None:
    """Search Open Targets for a disease by name, return best match with EFO ID."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(GRAPHQL_URL, json={
                "query": SEARCH_DISEASE_QUERY,
                "variables": {"name": name},
            })
            resp.raise_for_status()
            data = resp.json()

        hits = data.get("data", {}).get("search", {}).get("hits", [])
        disease_hits = [h for h in hits if h.get("entity") == "disease"]
        if not disease_hits:
            return None

        best = disease_hits[0]
        return {
            "efo_id": best["id"],
            "name": best["name"],
            "description": best.get("description", ""),
        }
    except Exception as e:
        log.error("Open Targets search failed: %s", e)
        return None


async def get_disease_targets(efo_id: str) -> list[dict]:
    """Get top associated protein targets for a disease by EFO ID."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(GRAPHQL_URL, json={
                "query": DISEASE_TARGETS_QUERY,
                "variables": {"efoId": efo_id},
            })
            resp.raise_for_status()
            data = resp.json()

        disease = data.get("data", {}).get("disease")
        if not disease:
            return []

        rows = disease.get("associatedTargets", {}).get("rows", [])
        targets = []
        for row in rows:
            t = row.get("target", {})
            targets.append({
                "gene_name": t.get("approvedSymbol", ""),
                "protein_name": t.get("approvedName", ""),
                "target_id": t.get("id", ""),
                "association_score": round(row.get("score", 0), 4),
            })
        return targets
    except Exception as e:
        log.error("Open Targets targets query failed: %s", e)
        return []


async def get_target_diseases(ensembl_id: str) -> list[dict]:
    """Reverse lookup: get diseases associated with a protein target."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(GRAPHQL_URL, json={
                "query": TARGET_DISEASES_QUERY,
                "variables": {"ensemblId": ensembl_id},
            })
            resp.raise_for_status()
            data = resp.json()

        target = data.get("data", {}).get("target")
        if not target:
            return []

        rows = target.get("associatedDiseases", {}).get("rows", [])
        diseases = []
        for row in rows:
            d = row.get("disease", {})
            diseases.append({
                "efo_id": d.get("id", ""),
                "name": d.get("name", ""),
                "score": round(row.get("score", 0), 4),
            })
        return diseases
    except Exception as e:
        log.error("Open Targets target-diseases query failed: %s", e)
        return []
