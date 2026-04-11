"""Contradiction Checker — looks for logical conflicts between agent outputs.

Uses both the local DeBERTa NLI engine and an LLM (Gemini) for deeper
reasoning about mechanistic contradictions.
"""

import logging

from backend.models import (
    DiseaseTarget, DrugCandidate, SafetyAssessment, Contradiction, SafetyVerdict,
)
from backend.services.llm import ask_llm_json
from backend.contradiction_engine import evaluate_claims_async

log = logging.getLogger(__name__)


async def check_contradictions(
    disease_name: str,
    disease_summary: str,
    targets: list[DiseaseTarget],
    candidates: list[DrugCandidate],
    safety_assessments: list[SafetyAssessment],
) -> list[Contradiction]:
    """Run contradiction checks using both DeBERTa NLI and LLM reasoning."""
    contradictions: list[Contradiction] = []

    safety_map = {sa.drug_name: sa for sa in safety_assessments}

    for drug in candidates:
        sa = safety_map.get(drug.drug_name)
        if not sa:
            continue

        if sa.verdict == SafetyVerdict.HARD_FAIL and drug.confidence > 0.6:
            claim_a = f"{drug.drug_name} is a strong repurposing candidate: {drug.repurposing_rationale}"
            claim_b = f"{drug.drug_name} has unacceptable safety risks: {sa.reasoning}"

            nli_result = await evaluate_claims_async(claim_a, claim_b)
            if nli_result.get("conflict_detected", False):
                contradictions.append(Contradiction(
                    severity="BLOCKING",
                    agent_a="Drug Hunter",
                    agent_b="Safety Checker",
                    claim_a=claim_a,
                    claim_b=claim_b,
                    explanation=(
                        f"Drug Hunter rates {drug.drug_name} highly (confidence {drug.confidence:.0%}) "
                        f"but Safety Checker flags HARD_FAIL due to organ conflicts: "
                        f"{', '.join(sa.organ_conflicts) if sa.organ_conflicts else sa.reasoning}. "
                        f"DeBERTa contradiction score: {nli_result['scores']['contradiction']:.0%}."
                    ),
                ))

        if sa.verdict == SafetyVerdict.WARNING and sa.organ_conflicts:
            contradictions.append(Contradiction(
                severity="WARNING",
                agent_a="Drug Hunter",
                agent_b="Safety Checker",
                claim_a=f"{drug.drug_name} targets pathways relevant to {disease_name}.",
                claim_b=f"{drug.drug_name} adverse events affect: {', '.join(sa.organ_conflicts)}.",
                explanation=(
                    f"Potential organ overlap: {drug.drug_name}'s side effects may affect "
                    f"organs already compromised by {disease_name}. Requires clinical review."
                ),
            ))

    llm_contradictions = await _llm_contradiction_check(
        disease_name, disease_summary, targets, candidates, safety_assessments,
    )
    contradictions.extend(llm_contradictions)

    return contradictions


async def _llm_contradiction_check(
    disease_name: str,
    disease_summary: str,
    targets: list[DiseaseTarget],
    candidates: list[DrugCandidate],
    safety_assessments: list[SafetyAssessment],
) -> list[Contradiction]:
    """Use LLM for deeper mechanistic contradiction analysis."""
    targets_text = "\n".join(f"- {t.gene_name}: {t.protein_name}" for t in targets[:5])
    candidates_text = "\n".join(
        f"- {d.drug_name}: {d.mechanism} (confidence {d.confidence:.0%})"
        for d in candidates
    )
    safety_text = "\n".join(
        f"- {s.drug_name}: {s.verdict.value} — {s.reasoning[:100]}"
        for s in safety_assessments
    )

    result = await ask_llm_json(
        system_prompt=(
            "You are a pharmacology expert reviewing a drug repurposing analysis for "
            "logical contradictions. Look for conflicts such as: a drug targets a "
            "protein in the brain but can't cross the blood-brain barrier; effective "
            "dose overlaps with toxic dose; drug mechanism helps one pathway but hurts "
            "a compensatory pathway the patient depends on. "
            "Return a JSON array of contradiction objects with keys: severity "
            '("BLOCKING" or "WARNING"), agent_a, agent_b, claim_a, claim_b, explanation. '
            "Return an empty array [] if no contradictions found."
        ),
        user_prompt=(
            f"Disease: {disease_name}\n{disease_summary}\n\n"
            f"Targets:\n{targets_text}\n\n"
            f"Drug candidates:\n{candidates_text}\n\n"
            f"Safety assessments:\n{safety_text}\n\n"
            f"Identify any logical contradictions between these agent outputs."
        ),
    )

    contradictions = []
    if isinstance(result, list):
        for item in result:
            try:
                contradictions.append(Contradiction(
                    severity=item.get("severity", "WARNING"),
                    agent_a=item.get("agent_a", "Drug Hunter"),
                    agent_b=item.get("agent_b", "Safety Checker"),
                    claim_a=item.get("claim_a", ""),
                    claim_b=item.get("claim_b", ""),
                    explanation=item.get("explanation", ""),
                ))
            except Exception as e:
                log.warning("Failed to parse LLM contradiction item: %s", e)
                continue

    return contradictions
