"""Agent 2: Drug Hunter — searches ClinicalTrials.gov AND ChEMBL for repurposing candidates."""

from backend.models import DiseaseTarget, DrugCandidate, EvidenceScore
from backend.services.clinical_trials import search_failed_trials
from backend.services.chembl import search_drugs_for_targets
from backend.services.llm import ask_llm_json


def compute_evidence_score(
    target_score: float,
    phase: str,
    paper_count: int = 0,
    safety_verdict: str = "",
) -> EvidenceScore:
    """Transparent, reproducible scoring — no LLM involved."""
    target_pts = min(int(target_score * 30), 30)

    phase_upper = phase.upper()
    if "PHASE3" in phase_upper or "PHASE 3" in phase_upper:
        trial_pts = 25
    elif "PHASE2" in phase_upper or "PHASE 2" in phase_upper:
        trial_pts = 15
    elif "PHASE1" in phase_upper or "PHASE 1" in phase_upper:
        trial_pts = 5
    else:
        trial_pts = 0

    if paper_count >= 5:
        lit_pts = 25
    elif paper_count >= 3:
        lit_pts = 15
    elif paper_count >= 1:
        lit_pts = 8
    else:
        lit_pts = 0

    if safety_verdict == "PASS":
        safety_pts = 20
    elif safety_verdict == "WARNING":
        safety_pts = 10
    elif safety_verdict == "HARD_FAIL":
        safety_pts = 0
    else:
        safety_pts = 10  # unknown = cautious middle

    total = target_pts + trial_pts + lit_pts + safety_pts

    breakdown = (
        f"Target: {target_pts}/30 (association {target_score:.2f}), "
        f"Trial: {trial_pts}/25 ({phase}), "
        f"Literature: {lit_pts}/25 ({paper_count} papers), "
        f"Safety: {safety_pts}/20 ({safety_verdict or 'pending'})"
    )

    return EvidenceScore(
        target_association=target_pts,
        trial_evidence=trial_pts,
        literature_support=lit_pts,
        safety_profile=safety_pts,
        total=total,
        breakdown=breakdown,
    )


async def hunt_drugs(
    disease_name: str,
    targets: list[DiseaseTarget],
    disease_summary: str,
) -> list[DrugCandidate]:
    """Search ClinicalTrials.gov + ChEMBL for candidates. Uses evidence-based scoring."""
    gene_names = [t.gene_name for t in targets]
    target_scores = {t.gene_name: t.association_score for t in targets}
    best_target_score = max((t.association_score for t in targets), default=0)

    # Parallel data fetching from two real sources
    raw_trials = await search_failed_trials(gene_names, disease_name)
    chembl_drugs = await search_drugs_for_targets(gene_names)

    candidates = []
    seen_drugs = set()
    sources_used = []

    # Process ClinicalTrials.gov results
    if raw_trials:
        sources_used.append("ClinicalTrials.gov")
        trials_text = ""
        for i, trial in enumerate(raw_trials[:15], 1):
            drugs = ", ".join(trial["drug_names"])
            trials_text += (
                f"{i}. [{trial['trial_id']}] {trial['title']}\n"
                f"   Drugs: {drugs}\n"
                f"   Phase: {trial['phase']} | Status: {trial['status']}\n"
                f"   Why stopped: {trial['why_stopped']}\n"
                f"   Conditions: {', '.join(trial['conditions'][:3])}\n\n"
            )

        target_text = ", ".join(f"{t.gene_name} ({t.protein_name})" for t in targets[:5])

        llm_result = await ask_llm_json(
            system_prompt=(
                "You are a drug repurposing expert. Analyze failed clinical trials and "
                "identify which drugs could be repurposed for the given disease. "
                "Return a JSON array of objects with keys: drug_name, trial_id, "
                "original_indication, phase, failure_reason, mechanism, "
                "repurposing_rationale."
            ),
            user_prompt=(
                f"Disease: {disease_name}\n"
                f"Disease biology: {disease_summary}\n"
                f"Key protein targets: {target_text}\n\n"
                f"Failed/terminated trials:\n{trials_text}\n\n"
                f"Which of these drugs have mechanisms that could plausibly treat "
                f"{disease_name}? Rank by mechanistic overlap. For each, explain why it "
                f"failed originally and why it might work for this new indication. "
                f"Return top 5 as JSON array."
            ),
            max_tokens=3000,
        )

        if isinstance(llm_result, list):
            for item in llm_result[:5]:
                try:
                    name = item.get("drug_name", "Unknown")
                    phase = item.get("phase", "")
                    score = compute_evidence_score(best_target_score, phase)
                    c = DrugCandidate(
                        drug_name=name,
                        trial_id=item.get("trial_id", ""),
                        original_indication=item.get("original_indication", ""),
                        phase=phase,
                        failure_reason=item.get("failure_reason", "Not specified"),
                        mechanism=item.get("mechanism", ""),
                        repurposing_rationale=item.get("repurposing_rationale", ""),
                        confidence=score.total / 100,
                        evidence_score=score,
                        sources=["ClinicalTrials.gov"],
                    )
                    candidates.append(c)
                    seen_drugs.add(name.lower())
                except Exception:
                    continue

        if not candidates:
            for trial in raw_trials[:8]:
                if not trial["drug_names"]:
                    continue
                drug = trial["drug_names"][0]
                if not drug or drug.lower() in seen_drugs or drug == "Unknown":
                    continue
                if len(drug) > 50 or " " in drug and len(drug.split()) > 5:
                    continue
                phase = trial["phase"]
                score = compute_evidence_score(best_target_score, phase)
                conditions = ", ".join(trial["conditions"][:2])
                candidates.append(DrugCandidate(
                    drug_name=drug,
                    trial_id=trial["trial_id"],
                    original_indication=conditions,
                    phase=phase,
                    failure_reason=trial["why_stopped"],
                    mechanism=f"Investigated for: {conditions}. Exact mechanism of action requires further literature review.",
                    repurposing_rationale=(
                        f"This drug was tested in a Phase 2/3 trial ({trial['trial_id']}) for conditions "
                        f"related to {disease_name}. The trial was {trial['status'].lower()}: "
                        f"\"{trial['why_stopped']}\". The drug's mechanism may have relevance to "
                        f"{disease_name} through shared pathological pathways."
                    ),
                    confidence=score.total / 100,
                    evidence_score=score,
                    sources=["ClinicalTrials.gov"],
                ))
                seen_drugs.add(drug.lower())
                if len(candidates) >= 5:
                    break

    # Process ChEMBL results — add drugs not already found in trials
    if chembl_drugs:
        sources_used.append("ChEMBL")
        for cdrug in chembl_drugs:
            name = cdrug["drug_name"]
            if name.lower() in seen_drugs:
                # Upgrade existing candidate with ChEMBL source
                for c in candidates:
                    if c.drug_name.lower() == name.lower():
                        if "ChEMBL" not in c.sources:
                            c.sources.append("ChEMBL")
                continue

            matched_gene = cdrug.get("matched_target", "")
            tscore = target_scores.get(matched_gene, 0.3)
            score = compute_evidence_score(tscore, "")

            candidates.append(DrugCandidate(
                drug_name=name,
                trial_id="",
                original_indication=cdrug.get("mechanism_of_action", ""),
                phase="Pre-clinical / Approved for other indication",
                failure_reason="N/A — identified via target binding data, not trial failure.",
                mechanism=cdrug.get("mechanism_of_action", "Unknown mechanism"),
                repurposing_rationale=(
                    f"Binds to {matched_gene}, which is associated with {disease_name} "
                    f"(association score: {tscore:.2f}). Identified via ChEMBL drug-target data."
                ),
                confidence=score.total / 100,
                evidence_score=score,
                sources=["ChEMBL"],
            ))
            seen_drugs.add(name.lower())

    # Sort by evidence score
    candidates.sort(key=lambda c: c.evidence_score.total if c.evidence_score else 0, reverse=True)
    return candidates[:8]
