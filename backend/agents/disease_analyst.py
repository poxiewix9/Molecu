"""Agent 1: Disease Analyst — queries Open Targets for disease biology and protein targets."""

from backend.models import DiseaseTarget
from backend.services.open_targets import search_disease, get_disease_targets
from backend.services.llm import ask_llm


async def analyze_disease(disease_name: str) -> tuple[list[DiseaseTarget], str, str]:
    """
    Returns (targets, disease_summary, efo_id).
    Falls back gracefully if APIs or LLM are unavailable.
    """
    disease_info = await search_disease(disease_name)
    efo_id = ""
    resolved_name = disease_name

    if disease_info:
        efo_id = disease_info["efo_id"]
        resolved_name = disease_info["name"]

    raw_targets = []
    if efo_id:
        raw_targets = await get_disease_targets(efo_id)

    targets = []
    for t in raw_targets:
        targets.append(DiseaseTarget(
            gene_name=t["gene_name"],
            protein_name=t["protein_name"],
            target_id=t["target_id"],
            association_score=t["association_score"],
            description=f"{t['gene_name']} ({t['protein_name']}) — association score {t['association_score']}",
        ))

    target_text = "\n".join(
        f"- {t.gene_name} ({t.protein_name}): score {t.association_score}"
        for t in targets
    ) if targets else "No targets found via Open Targets."

    summary = await ask_llm(
        system_prompt=(
            "You are a biomedical research assistant. Summarize disease biology "
            "in 3-4 sentences for a drug-discovery audience. Explain what kind of "
            "drug mechanism could help and which protein targets are most promising."
        ),
        user_prompt=(
            f"Disease: {resolved_name}\n"
            f"Description: {disease_info.get('description', 'N/A') if disease_info else 'N/A'}\n"
            f"Top associated targets:\n{target_text}\n\n"
            f"Provide a concise disease biology summary and what drug mechanisms to look for."
        ),
    )

    if not summary:
        desc = disease_info.get("description", "") if disease_info else ""
        summary = (
            f"{resolved_name}: {desc[:300]}" if desc
            else f"{resolved_name} — associated with {len(targets)} protein targets. "
                 f"Top targets include {', '.join(t.gene_name for t in targets[:3])}."
        )

    return targets, summary, efo_id
