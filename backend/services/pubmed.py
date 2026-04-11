"""NCBI E-utilities wrapper for PubMed literature search."""

import httpx
import logging
import asyncio

log = logging.getLogger(__name__)

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

NCBI_DELAY = 0.35  # stay under 3 req/sec without an API key


async def search_pubmed(drug_name: str, disease_name: str, max_results: int = 10) -> list[str]:
    """Return list of PMIDs for papers connecting a drug to a disease."""
    queries = [
        f'"{drug_name}" AND "{disease_name}" AND (repurpos* OR reposition*)',
        f'"{drug_name}" AND "{disease_name}"',
    ]

    for query in queries:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(ESEARCH_URL, params={
                    "db": "pubmed",
                    "term": query,
                    "retmax": str(max_results),
                    "retmode": "json",
                    "sort": "relevance",
                })
                resp.raise_for_status()
                data = resp.json()

            ids = data.get("esearchresult", {}).get("idlist", [])
            if ids:
                return ids
            await asyncio.sleep(NCBI_DELAY)
        except Exception as e:
            log.warning("PubMed search failed for '%s' + '%s': %s", drug_name, disease_name, e)

    return []


async def get_paper_summaries(pmids: list[str]) -> list[dict]:
    """Fetch summary metadata for a list of PMIDs."""
    if not pmids:
        return []

    try:
        await asyncio.sleep(NCBI_DELAY)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(ESUMMARY_URL, params={
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "json",
            })
            resp.raise_for_status()
            data = resp.json()

        result_block = data.get("result", {})
        papers = []
        for pmid in pmids:
            info = result_block.get(pmid)
            if not info or "error" in info:
                continue

            authors_list = info.get("authors", [])
            author_str = ", ".join(a.get("name", "") for a in authors_list[:3])
            if len(authors_list) > 3:
                author_str += " et al."

            papers.append({
                "pmid": pmid,
                "title": info.get("title", ""),
                "authors": author_str,
                "journal": info.get("source", ""),
                "year": int(info.get("pubdate", "0")[:4]) if info.get("pubdate") else 0,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })

        return papers
    except Exception as e:
        log.warning("PubMed summary fetch failed: %s", e)
        return []


async def get_abstracts(pmids: list[str]) -> dict[str, str]:
    """Fetch abstracts for PMIDs. Returns {pmid: abstract_text}."""
    if not pmids:
        return {}

    try:
        await asyncio.sleep(NCBI_DELAY)
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(EFETCH_URL, params={
                "db": "pubmed",
                "id": ",".join(pmids[:5]),
                "rettype": "abstract",
                "retmode": "text",
            })
            resp.raise_for_status()

        text = resp.text
        abstracts = {}
        chunks = text.split("\n\n\n")
        for i, chunk in enumerate(chunks):
            if i < len(pmids):
                abstracts[pmids[i]] = chunk.strip()[:2000]

        return abstracts
    except Exception as e:
        log.warning("PubMed abstract fetch failed: %s", e)
        return {}


async def search_drug_disease_literature(drug_name: str, disease_name: str) -> dict:
    """Full pipeline: search -> summaries -> abstracts. Returns structured result."""
    pmids = await search_pubmed(drug_name, disease_name, max_results=5)

    if not pmids:
        return {"paper_count": 0, "papers": [], "abstracts": {}}

    papers = await get_paper_summaries(pmids)
    abstracts = await get_abstracts(pmids[:3])

    return {
        "paper_count": len(pmids),
        "papers": papers,
        "abstracts": abstracts,
    }
