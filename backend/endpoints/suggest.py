"""Disease name suggestion endpoint using Open Targets search API."""

import logging
import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

log = logging.getLogger(__name__)
router = APIRouter()

OT_SEARCH_URL = "https://api.platform.opentargets.org/api/v4/graphql"

SEARCH_QUERY = """
query SearchDisease($q: String!) {
  search(queryString: $q, entityNames: ["disease"], page: {index: 0, size: 8}) {
    hits {
      id
      name
      description
    }
  }
}
"""


@router.get("/api/suggest/{query}")
async def suggest(query: str):
    """Return disease name suggestions from Open Targets."""
    if len(query) < 2:
        return JSONResponse(content={"suggestions": []})

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.post(
                OT_SEARCH_URL,
                json={"query": SEARCH_QUERY, "variables": {"q": query}},
            )
            if resp.status_code != 200:
                return JSONResponse(content={"suggestions": []})

            data = resp.json()
            hits = data.get("data", {}).get("search", {}).get("hits", [])
            suggestions = [
                {"id": h["id"], "name": h["name"], "description": (h.get("description") or "")[:120]}
                for h in hits
            ]
            return JSONResponse(content={"suggestions": suggestions})
    except Exception as e:
        log.warning("Suggest error: %s", e)
        return JSONResponse(content={"suggestions": []})
