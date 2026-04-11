"""Hardcoded fallback dataset for Friedreich's Ataxia — ensures the demo works even if APIs are down."""

from backend.models import (
    DiseaseTarget, DrugCandidate, SafetyAssessment, SafetyVerdict, Contradiction,
)

FRIEDREICHS_DISEASE_SUMMARY = (
    "Friedreich's Ataxia (FRDA) is a rare autosomal recessive neurodegenerative disease "
    "caused by GAA trinucleotide repeat expansion in the FXN gene, leading to reduced "
    "frataxin protein levels. Frataxin is critical for mitochondrial iron-sulfur cluster "
    "assembly. The disease primarily affects the nervous system (spinocerebellar tracts, "
    "dorsal root ganglia) and heart (hypertrophic cardiomyopathy). Onset is typically "
    "before age 25. Drug mechanisms targeting mitochondrial function, iron chelation, "
    "frataxin upregulation, or Nrf2-mediated antioxidant pathways are most promising."
)

FRIEDREICHS_TARGETS = [
    DiseaseTarget(gene_name="FXN", protein_name="Frataxin", target_id="ENSG00000165060", association_score=0.95, description="FXN (Frataxin) — the causal gene. Reduced expression causes iron accumulation in mitochondria."),
    DiseaseTarget(gene_name="NRF2", protein_name="Nuclear factor erythroid 2-related factor 2", target_id="ENSG00000116044", association_score=0.78, description="NRF2 — master regulator of antioxidant response, downregulated in FRDA."),
    DiseaseTarget(gene_name="KEAP1", protein_name="Kelch-like ECH-associated protein 1", target_id="ENSG00000079999", association_score=0.72, description="KEAP1 — negative regulator of NRF2. Inhibiting KEAP1 upregulates antioxidant defense."),
    DiseaseTarget(gene_name="SOD2", protein_name="Superoxide dismutase 2", target_id="ENSG00000112096", association_score=0.65, description="SOD2 — mitochondrial antioxidant enzyme, reduced activity in FRDA."),
    DiseaseTarget(gene_name="SIRT3", protein_name="NAD-dependent deacetylase sirtuin-3", target_id="ENSG00000171827", association_score=0.61, description="SIRT3 — mitochondrial sirtuin involved in metabolic regulation."),
    DiseaseTarget(gene_name="ACO2", protein_name="Aconitase 2", target_id="ENSG00000100412", association_score=0.58, description="ACO2 — iron-sulfur cluster enzyme affected by frataxin deficiency."),
    DiseaseTarget(gene_name="TFRC", protein_name="Transferrin receptor protein 1", target_id="ENSG00000072274", association_score=0.55, description="TFRC — iron uptake receptor, involved in iron dysregulation."),
    DiseaseTarget(gene_name="HDAC3", protein_name="Histone deacetylase 3", target_id="ENSG00000171720", association_score=0.52, description="HDAC3 — epigenetic silencer. HDAC inhibitors may reactivate FXN expression."),
]

FRIEDREICHS_CANDIDATES = [
    DrugCandidate(
        drug_name="Omaveloxolone",
        trial_id="NCT02255435",
        original_indication="Mitochondrial myopathy / Friedreich's Ataxia",
        phase="PHASE2, PHASE3",
        failure_reason="Initially slow enrollment; later reformulated and re-trialed. Early Phase 2 was terminated for protocol redesign.",
        mechanism="Nrf2 activator — inhibits KEAP1 to upregulate antioxidant gene expression and reduce oxidative stress in mitochondria.",
        repurposing_rationale="Directly addresses the NRF2/KEAP1 pathway dysfunction in FRDA. Actually received FDA approval in 2023 (Skyclarys), validating this exact repurposing hypothesis.",
        confidence=0.92,
    ),
    DrugCandidate(
        drug_name="Deferiprone",
        trial_id="NCT00897221",
        original_indication="Iron overload in thalassemia major",
        phase="PHASE2",
        failure_reason="Terminated — mixed efficacy results, cardiac iron reduction not statistically significant in the FRDA cohort.",
        mechanism="Oral iron chelator — crosses the blood-brain barrier and redistributes mitochondrial iron accumulation.",
        repurposing_rationale="Frataxin deficiency causes mitochondrial iron overload. Deferiprone can cross the BBB (unlike deferoxamine) and directly chelate the accumulated iron in neurons and cardiomyocytes.",
        confidence=0.75,
    ),
    DrugCandidate(
        drug_name="Resveratrol",
        trial_id="NCT01339884",
        original_indication="Diabetes / Cardiovascular disease",
        phase="PHASE2",
        failure_reason="Withdrawn — poor bioavailability, inconsistent results across multiple indications.",
        mechanism="SIRT1/SIRT3 activator and antioxidant — enhances mitochondrial biogenesis via PGC-1α pathway.",
        repurposing_rationale="Activates SIRT3, which is depleted in FRDA mitochondria. Enhances mitochondrial biogenesis and reduces oxidative stress. Bioavailability issues could be addressed with novel formulations.",
        confidence=0.55,
    ),
    DrugCandidate(
        drug_name="Nicotinamide (Vitamin B3)",
        trial_id="NCT01589809",
        original_indication="Pellagra / Various metabolic conditions",
        phase="PHASE2",
        failure_reason="Terminated — frataxin protein increase was modest and not sustained at tolerable doses.",
        mechanism="HDAC inhibitor (class III) — epigenetically reactivates silenced FXN gene by counteracting GAA repeat-mediated heterochromatin.",
        repurposing_rationale="High-dose nicotinamide was shown to increase frataxin mRNA and protein levels in FRDA patient cells. Targets the root cause (FXN gene silencing) rather than downstream symptoms.",
        confidence=0.60,
    ),
    DrugCandidate(
        drug_name="Idebenone",
        trial_id="NCT00905268",
        original_indication="Leber hereditary optic neuropathy / mitochondrial disease",
        phase="PHASE3",
        failure_reason="Terminated — Phase 3 (IONIA trial) failed to meet primary endpoint in FRDA ambulatory patients.",
        mechanism="Synthetic CoQ10 analogue — bypasses Complex I deficiency as an electron carrier in the mitochondrial respiratory chain.",
        repurposing_rationale="Targets mitochondrial dysfunction central to FRDA pathology. Despite trial failure, showed benefit in non-ambulatory subgroup. May work with patient stratification or combination therapy.",
        confidence=0.50,
    ),
]

FRIEDREICHS_SAFETY = [
    SafetyAssessment(
        drug_name="Omaveloxolone",
        verdict=SafetyVerdict.PASS,
        adverse_events=["nausea", "headache", "fatigue", "abdominal pain", "elevated liver enzymes"],
        reasoning="Generally well-tolerated. Liver enzyme elevations require monitoring but are manageable. No overlap with FRDA-affected organs (nervous system, heart) at concerning levels.",
        organ_conflicts=[],
    ),
    SafetyAssessment(
        drug_name="Deferiprone",
        verdict=SafetyVerdict.WARNING,
        adverse_events=["agranulocytosis", "neutropenia", "arthralgia", "nausea", "elevated ALT", "zinc deficiency"],
        reasoning="Agranulocytosis (severe neutropenia) is a known serious risk requiring weekly blood monitoring. Does not directly affect FRDA-compromised organs, but the immunosuppressive risk adds burden to already fragile patients.",
        organ_conflicts=["bone marrow (indirect immune risk)"],
    ),
    SafetyAssessment(
        drug_name="Resveratrol",
        verdict=SafetyVerdict.PASS,
        adverse_events=["diarrhea", "nausea", "abdominal discomfort"],
        reasoning="Very low toxicity profile. Main concern is poor bioavailability rather than safety. No organ conflicts with FRDA-affected systems.",
        organ_conflicts=[],
    ),
    SafetyAssessment(
        drug_name="Nicotinamide (Vitamin B3)",
        verdict=SafetyVerdict.WARNING,
        adverse_events=["hepatotoxicity at high doses", "nausea", "vomiting", "flushing"],
        reasoning="High doses needed for FXN reactivation risk hepatotoxicity. FRDA patients may have baseline liver stress. Requires careful dose titration and liver monitoring.",
        organ_conflicts=["liver"],
    ),
    SafetyAssessment(
        drug_name="Idebenone",
        verdict=SafetyVerdict.PASS,
        adverse_events=["diarrhea", "nausea", "chromaturia (orange urine)"],
        reasoning="Well-tolerated safety profile across multiple trials. No concerning organ overlap with FRDA pathology. Chromaturia is cosmetic, not clinical.",
        organ_conflicts=[],
    ),
]

FRIEDREICHS_CONTRADICTIONS = [
    Contradiction(
        severity="WARNING",
        agent_a="Drug Hunter",
        agent_b="Safety Checker",
        claim_a="Deferiprone chelates mitochondrial iron and can cross the blood-brain barrier to treat neuronal iron accumulation in FRDA.",
        claim_b="Deferiprone carries a risk of agranulocytosis requiring weekly blood monitoring, adding burden to patients already managing a complex disease.",
        explanation="The Drug Hunter identifies Deferiprone's BBB penetration as a key advantage, but the Safety Checker flags that weekly blood monitoring for agranulocytosis may be impractical for FRDA patients who already have significant care burden and mobility limitations.",
    ),
    Contradiction(
        severity="BLOCKING",
        agent_a="Drug Hunter",
        agent_b="Safety Checker",
        claim_a="High-dose Nicotinamide can reactivate the silenced FXN gene, directly addressing the root genetic cause of Friedreich's Ataxia.",
        claim_b="The doses required for meaningful FXN reactivation cause hepatotoxicity, and FRDA patients may already have compromised liver function from chronic disease.",
        explanation="Root-cause contradiction: the effective dose for frataxin upregulation overlaps with the hepatotoxic dose range. FRDA patients with cardiomyopathy may have hepatic congestion, compounding liver risk. The Drug Hunter's mechanism is sound but the Safety Checker's dose-toxicity overlap makes this a blocking conflict requiring clinical pharmacology review.",
    ),
]


def get_friedreichs_fallback() -> dict:
    return {
        "disease_name": "Friedreich's Ataxia",
        "disease_summary": FRIEDREICHS_DISEASE_SUMMARY,
        "targets": FRIEDREICHS_TARGETS,
        "candidates": FRIEDREICHS_CANDIDATES,
        "safety_assessments": FRIEDREICHS_SAFETY,
        "contradictions": FRIEDREICHS_CONTRADICTIONS,
    }
