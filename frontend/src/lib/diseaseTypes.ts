export interface DiseaseTarget {
  gene_name: string;
  protein_name: string;
  target_id: string;
  association_score: number;
  description: string;
}

export interface PaperCitation {
  pmid: string;
  title: string;
  authors: string;
  journal: string;
  year: number;
  url: string;
}

export interface EvidenceScore {
  target_association: number;
  trial_evidence: number;
  literature_support: number;
  safety_profile: number;
  total: number;
  breakdown: string;
}

export interface DrugCandidate {
  drug_name: string;
  trial_id: string;
  original_indication: string;
  phase: string;
  failure_reason: string;
  mechanism: string;
  repurposing_rationale: string;
  confidence: number;
  evidence_score?: EvidenceScore;
  sources?: string[];
}

export interface SafetyAssessment {
  drug_name: string;
  verdict: "PASS" | "WARNING" | "HARD_FAIL";
  adverse_events: string[];
  reasoning: string;
  organ_conflicts: string[];
  source?: string;
  report_counts?: Record<string, number>;
}

export interface EvidenceSummary {
  drug_name: string;
  paper_count: number;
  top_papers: PaperCitation[];
  evidence_summary: string;
}

export interface Contradiction {
  severity: "BLOCKING" | "WARNING";
  agent_a: string;
  agent_b: string;
  claim_a: string;
  claim_b: string;
  explanation: string;
}

export interface SSEEvent {
  agent: string;
  status: "working" | "complete" | "error";
  message: string;
  data?: Record<string, unknown>;
}

export interface DiseaseEvaluation {
  disease_name: string;
  disease_summary: string;
  targets: DiseaseTarget[];
  candidates: DrugCandidate[];
  safety_assessments: SafetyAssessment[];
  contradictions: Contradiction[];
  evidence_summaries: EvidenceSummary[];
  data_sources: string[];
}
