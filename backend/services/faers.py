"""FDA FAERS (Adverse Event Reporting System) API wrapper."""

import httpx
import asyncio
import logging

log = logging.getLogger(__name__)

BASE_URL = "https://api.fda.gov/drug/event.json"
MAX_RETRIES = 3
RETRY_DELAY = 2.0


async def get_adverse_events(drug_name: str, limit: int = 10) -> list[dict]:
    """Get top adverse events for a drug from FDA FAERS. Returns list of {term, count}."""
    search_query = f'patient.drug.openfda.generic_name:"{drug_name}"'
    params = {
        "search": search_query,
        "count": "patient.reaction.reactionmeddrapt.exact",
        "limit": str(limit),
    }

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(BASE_URL, params=params)

                if resp.status_code == 404:
                    return []
                if resp.status_code == 429:
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    continue

                resp.raise_for_status()
                data = resp.json()

            results = data.get("results", [])
            return [{"term": r.get("term", ""), "count": r.get("count", 0)} for r in results]

        except httpx.TimeoutException:
            log.warning("FAERS timeout for %s (attempt %d)", drug_name, attempt + 1)
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
            continue
        except Exception as e:
            log.error("FAERS query failed for %s: %s", drug_name, e)
            return []

    return []
