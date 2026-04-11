import { describe, it, expect } from "vitest";
import type {
  EvidenceScore,
  DrugCandidate,
  SafetyAssessment,
  DiseaseEvaluation,
} from "@/lib/diseaseTypes";

describe("diseaseTypes — TypeScript interface contracts", () => {
  it("EvidenceScore structure matches backend Pydantic model", () => {
    const score: EvidenceScore = {
      target_association: 24,
      trial_evidence: 15,
      literature_support: 25,
      safety_profile: 20,
      total: 84,
      breakdown: "Target: 24/30, Trial: 15/25, Literature: 25/25, Safety: 20/20",
    };
    expect(score.total).toBe(
      score.target_association + score.trial_evidence + score.literature_support + score.safety_profile
    );
    expect(score.total).toBeLessThanOrEqual(100);
    expect(score.total).toBeGreaterThanOrEqual(0);
  });

  it("DrugCandidate confidence is normalized 0-1", () => {
    const drug: DrugCandidate = {
      drug_name: "Sildenafil",
      trial_id: "NCT00001234",
      original_indication: "Erectile dysfunction",
      phase: "Phase 3",
      failure_reason: "N/A - approved for original indication",
      mechanism: "PDE5 inhibitor",
      repurposing_rationale: "Vasodilatory effects in pulmonary vasculature",
      confidence: 0.84,
      evidence_score: {
        target_association: 24,
        trial_evidence: 25,
        literature_support: 15,
        safety_profile: 20,
        total: 84,
        breakdown: "Target: 24/30, Trial: 25/25, Lit: 15/25, Safety: 20/20",
      },
      sources: ["ClinicalTrials.gov", "ChEMBL"],
    };
    expect(drug.confidence).toBeGreaterThanOrEqual(0);
    expect(drug.confidence).toBeLessThanOrEqual(1);
    expect(drug.sources).toContain("ClinicalTrials.gov");
  });

  it("SafetyAssessment verdict is one of PASS | WARNING | HARD_FAIL", () => {
    const verdicts: SafetyAssessment["verdict"][] = ["PASS", "WARNING", "HARD_FAIL"];
    verdicts.forEach((v) => {
      const sa: SafetyAssessment = {
        drug_name: "TestDrug",
        verdict: v,
        adverse_events: ["headache"],
        reasoning: "Test reasoning",
        organ_conflicts: [],
      };
      expect(["PASS", "WARNING", "HARD_FAIL"]).toContain(sa.verdict);
    });
  });

  it("DiseaseEvaluation contains all required fields", () => {
    const evaluation: DiseaseEvaluation = {
      disease_name: "Pulmonary Arterial Hypertension",
      disease_summary: "PAH is a progressive disease...",
      targets: [{ gene_name: "PDE5A", protein_name: "PDE5", target_id: "ENSG001", association_score: 0.8, description: "PDE5A" }],
      candidates: [],
      safety_assessments: [],
      contradictions: [],
      evidence_summaries: [],
      data_sources: ["Open Targets", "ClinicalTrials.gov"],
    };
    expect(evaluation.disease_name).toBeTruthy();
    expect(evaluation.data_sources.length).toBeGreaterThan(0);
    expect(Array.isArray(evaluation.targets)).toBe(true);
  });

  it("Evidence score components sum to total", () => {
    const scores: EvidenceScore[] = [
      { target_association: 30, trial_evidence: 25, literature_support: 25, safety_profile: 20, total: 100, breakdown: "Max score" },
      { target_association: 0, trial_evidence: 0, literature_support: 0, safety_profile: 0, total: 0, breakdown: "Min score" },
      { target_association: 15, trial_evidence: 15, literature_support: 8, safety_profile: 10, total: 48, breakdown: "Mid score" },
    ];
    scores.forEach((s) => {
      expect(s.target_association + s.trial_evidence + s.literature_support + s.safety_profile).toBe(s.total);
    });
  });
});
