"""Agent 3: Safety Checker — queries FDA FAERS for adverse events, rule-based verdicts."""

from backend.models import DrugCandidate, SafetyAssessment, SafetyVerdict
from backend.services.faers import get_adverse_events

HIGH_RISK_TERMS = {
    "death", "cardiac failure", "cardiac arrest", "hepatic failure",
    "renal failure", "respiratory failure", "anaphylactic shock",
    "agranulocytosis", "pancytopenia", "stevens-johnson syndrome",
    "toxic epidermal necrolysis", "pulmonary embolism", "cerebrovascular accident",
}

ORGAN_KEYWORDS = {
    "cardiac": "heart", "hepatic": "liver", "renal": "kidney",
    "pulmonary": "lungs", "cerebr": "brain", "neuro": "nervous system",
    "pancrea": "pancreas", "gastro": "GI tract",
}


def _classify_event(term: str) -> tuple[bool, list[str]]:
    """Check if an adverse event is high-risk and identify affected organs."""
    lower = term.lower()
    is_high_risk = any(r in lower for r in HIGH_RISK_TERMS)
    organs = [organ for keyword, organ in ORGAN_KEYWORDS.items() if keyword in lower]
    return is_high_risk, organs


async def check_safety(
    candidates: list[DrugCandidate],
    disease_name: str,
    disease_summary: str,
) -> list[SafetyAssessment]:
    """Check each candidate drug against FDA FAERS — pure rule-based, no LLM."""
    assessments = []

    for drug in candidates:
        events = await get_adverse_events(drug.drug_name)
        event_names = [e["term"] for e in events]
        report_counts = {e["term"]: e["count"] for e in events}

        high_risk_events = []
        all_organ_conflicts = []

        for event in events:
            is_risky, organs = _classify_event(event["term"])
            if is_risky:
                high_risk_events.append(event["term"])
            all_organ_conflicts.extend(organs)

        organ_conflicts = list(set(all_organ_conflicts))

        if not events:
            verdict = SafetyVerdict.PASS
            reasoning = (
                f"No adverse event data found in FDA FAERS for {drug.drug_name}. "
                f"This may mean limited post-market surveillance data exists. "
                f"Absence of FAERS data does not confirm safety."
            )
        elif high_risk_events:
            if len(high_risk_events) >= 3 or organ_conflicts:
                verdict = SafetyVerdict.HARD_FAIL
                reasoning = (
                    f"{len(high_risk_events)} serious adverse events found in FDA FAERS: "
                    f"{', '.join(high_risk_events[:5])}. "
                    f"{'Organ conflicts: ' + ', '.join(organ_conflicts) + '.' if organ_conflicts else ''}"
                )
            else:
                verdict = SafetyVerdict.WARNING
                reasoning = (
                    f"Some concerning events in FDA FAERS ({len(events)} total reports): "
                    f"{', '.join(high_risk_events[:3])}. Requires clinical review."
                )
        else:
            verdict = SafetyVerdict.PASS
            reasoning = (
                f"Based on {len(events)} FAERS reports. "
                f"No critical safety signals detected. Most common: "
                f"{', '.join(event_names[:3])}."
            )

        assessments.append(SafetyAssessment(
            drug_name=drug.drug_name,
            verdict=verdict,
            adverse_events=event_names[:10],
            reasoning=reasoning,
            organ_conflicts=organ_conflicts,
            source="FDA FAERS (openFDA)",
            report_counts=report_counts,
        ))

    return assessments
