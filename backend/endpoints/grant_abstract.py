"""Grant Abstract Generator — drafts an NIH R21-style specific aims paragraph from cached evidence."""

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.cache import get_result_cache
from backend.services.llm import ask_llm

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/grant-abstract/{drug_name}")
async def grant_abstract(drug_name: str, disease: str = ""):
    """Generate an NIH R21-style grant abstract for a drug-disease repurposing hypothesis."""

    cache = get_result_cache()
    result = cache.get(disease) if disease else None

    if not result:
        return JSONResponse(
            status_code=404,
            content={"error": f"No cached results for '{disease}'. Run a pipeline search first."},
        )

    drug_data = None
    safety_data = None
    evidence_data = None
    targets_text = ""

    if result:
        for c in result.candidates:
            if c.drug_name.lower() == drug_name.lower():
                drug_data = c
                break
        for sa in result.safety_assessments:
            if sa.drug_name.lower() == drug_name.lower():
                safety_data = sa
                break
        for es in result.evidence_summaries:
            if es.drug_name.lower() == drug_name.lower():
                evidence_data = es
                break
        if result.targets:
            targets_text = ", ".join(t.gene_name for t in result.targets[:5])

    context_parts = [f"Drug: {drug_name}", f"Disease: {disease or 'unknown'}"]

    if drug_data:
        context_parts.append(f"Mechanism: {drug_data.mechanism}")
        context_parts.append(f"Repurposing rationale: {drug_data.repurposing_rationale}")
        context_parts.append(f"Trial phase: {drug_data.phase}")
        context_parts.append(f"Original indication: {drug_data.original_indication}")
        if drug_data.trial_id:
            context_parts.append(f"Trial ID: {drug_data.trial_id}")
        if drug_data.evidence_score:
            es = drug_data.evidence_score
            context_parts.append(
                f"Evidence score: {es.total}/100 "
                f"(target={es.target_association}/30, trial={es.trial_evidence}/25, "
                f"literature={es.literature_support}/25, safety={es.safety_profile}/20)"
            )

    if safety_data:
        context_parts.append(f"Safety verdict: {safety_data.verdict}")
        if safety_data.adverse_events:
            context_parts.append(f"Key adverse events: {', '.join(safety_data.adverse_events[:5])}")

    if evidence_data:
        context_parts.append(f"PubMed papers found: {evidence_data.paper_count}")
        if evidence_data.top_papers:
            refs = []
            for p in evidence_data.top_papers[:3]:
                refs.append(f"{p.authors} ({p.year}). {p.title}. {p.journal}.")
            context_parts.append(f"Key references:\n" + "\n".join(refs))

    if targets_text:
        context_parts.append(f"Disease-associated protein targets: {targets_text}")

    if result and result.disease_summary:
        context_parts.append(f"Disease biology: {result.disease_summary}")

    evidence_context = "\n".join(context_parts)

    system_prompt = (
        "You are a biomedical grant writing assistant. Write an NIH R21 (Exploratory/Developmental "
        "Research Grant) Specific Aims section for a drug repurposing proposal.\n\n"
        "Structure:\n"
        "1. Opening paragraph: State the problem, the unmet need, and why existing treatments are insufficient.\n"
        "2. Central hypothesis: State the hypothesis that this drug could be repurposed for this disease, "
        "grounded in the evidence provided.\n"
        "3. Specific Aim 1: Typically an in vitro / computational validation aim.\n"
        "4. Specific Aim 2: Typically a preclinical / translational aim.\n"
        "5. Impact statement: How this work will advance the field.\n\n"
        "Rules:\n"
        "- Use only the evidence provided — do NOT fabricate citations or data.\n"
        "- Reference real trial IDs, gene targets, and paper counts where available.\n"
        "- Keep it to ~300 words, formal academic tone.\n"
        "- This is for an exploratory R21, so emphasize novelty and feasibility over preliminary data."
    )

    abstract = await ask_llm(system_prompt, evidence_context, max_tokens=1500)

    if not abstract:
        abstract = _build_fallback(drug_name, disease, drug_data, safety_data, evidence_data, targets_text)

    return JSONResponse(content={
        "drug_name": drug_name,
        "disease": disease,
        "abstract": abstract,
    })


def _build_fallback(
    drug_name: str,
    disease: str,
    drug_data=None,
    safety_data=None,
    evidence_data=None,
    targets_text: str = "",
) -> str:
    """Structured template when LLM is unavailable."""
    lines = [f"SPECIFIC AIMS — Repurposing {drug_name} for {disease or 'the target disease'}\n"]

    lines.append(
        f"{disease or 'This disease'} represents a significant unmet medical need. "
        f"Current therapeutic options are limited, creating an urgent demand for novel treatment strategies."
    )

    mechanism = drug_data.mechanism if drug_data else "an established pharmacological mechanism"
    rationale = drug_data.repurposing_rationale if drug_data else "preliminary computational and clinical evidence"
    lines.append(
        f"\nWe hypothesize that {drug_name}, which acts via {mechanism}, can be repurposed for "
        f"{disease or 'this condition'} based on {rationale}."
    )

    if targets_text:
        lines.append(f"\nKey disease-associated targets include {targets_text}.")

    if evidence_data and evidence_data.paper_count > 0:
        lines.append(f"\n{evidence_data.paper_count} peer-reviewed publications support this hypothesis.")

    if drug_data and drug_data.trial_id:
        lines.append(f"\nPrior clinical investigation ({drug_data.trial_id}, {drug_data.phase}) provides translational context.")

    if safety_data:
        lines.append(f"\nSafety profile assessment: {safety_data.verdict} — {safety_data.reasoning[:150]}")

    lines.append(
        f"\nAim 1: Validate the molecular interaction between {drug_name} and disease-relevant targets using computational docking and in vitro binding assays."
    )
    lines.append(
        f"\nAim 2: Evaluate the therapeutic efficacy of {drug_name} in a preclinical model of {disease or 'the target disease'}."
    )
    lines.append(
        "\nThis R21 proposal will provide the foundational evidence needed to advance this repurposing "
        "hypothesis toward an R01 application and eventual clinical translation."
    )

    return "\n".join(lines)
