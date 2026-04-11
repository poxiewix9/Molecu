"""Related Diseases endpoint — finds diseases sharing protein targets with the queried disease."""

import asyncio
import logging
from collections import defaultdict
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.cache import get_result_cache
from backend.services.open_targets import get_target_diseases

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/related-diseases/{disease_name}")
async def related_diseases(disease_name: str):
    """Find diseases that share protein targets with the queried disease."""

    result = get_result_cache().get(disease_name)

    if not result or not result.targets:
        return JSONResponse(content={
            "query_disease": disease_name,
            "related": [],
        })

    query_efo = None
    for t in result.targets:
        if not query_efo:
            # We'll derive the queried disease's EFO from the result object
            pass

    targets = result.targets[:6]
    target_ids = [(t.target_id, t.gene_name) for t in targets]

    # Fetch diseases for each target in parallel
    tasks = [get_target_diseases(tid) for tid, _ in target_ids]
    all_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Aggregate: disease -> { shared gene names, efo_id }
    disease_genes: dict[str, set[str]] = defaultdict(set)
    disease_meta: dict[str, dict] = {}

    for (tid, gene_name), diseases_or_err in zip(target_ids, all_results):
        if isinstance(diseases_or_err, Exception):
            log.warning("Failed to get diseases for target %s: %s", tid, diseases_or_err)
            continue
        for d in diseases_or_err:
            name = d["name"]
            # Skip the queried disease itself
            if name.lower() == disease_name.lower():
                continue
            disease_genes[name].add(gene_name)
            if name not in disease_meta:
                disease_meta[name] = {"efo_id": d["efo_id"], "name": name}

    # Sort by shared target count, then alphabetically
    related = []
    for name, genes in sorted(disease_genes.items(), key=lambda x: (-len(x[1]), x[0])):
        related.append({
            "disease_name": name,
            "efo_id": disease_meta[name]["efo_id"],
            "shared_targets": sorted(genes),
            "shared_count": len(genes),
        })

    return JSONResponse(content={
        "query_disease": disease_name,
        "related": related[:10],
    })
