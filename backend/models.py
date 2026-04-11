from pydantic import BaseModel
from enum import Enum


class DiseaseTarget(BaseModel):
    gene_name: str
    protein_name: str
    target_id: str
    association_score: float
    description: str


class PaperCitation(BaseModel):
    pmid: str
    title: str
    authors: str
    journal: str
    year: int
    url: str


class EvidenceScore(BaseModel):
    target_association: int  # 0-30
    trial_evidence: int      # 0-25
    literature_support: int  # 0-25
    safety_profile: int      # 0-20
    total: int               # 0-100
    breakdown: str


class DrugCandidate(BaseModel):
    drug_name: str
    trial_id: str
    original_indication: str
    phase: str
    failure_reason: str
    mechanism: str
    repurposing_rationale: str
    confidence: float
    evidence_score: EvidenceScore | None = None
    sources: list[str] = []


class SafetyVerdict(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    HARD_FAIL = "HARD_FAIL"


class SafetyAssessment(BaseModel):
    drug_name: str
    verdict: SafetyVerdict
    adverse_events: list[str]
    reasoning: str
    organ_conflicts: list[str]
    source: str = "FDA FAERS"
    report_counts: dict[str, int] = {}


class EvidenceSummary(BaseModel):
    drug_name: str
    paper_count: int
    top_papers: list[PaperCitation]
    evidence_summary: str


class Contradiction(BaseModel):
    severity: str
    agent_a: str
    agent_b: str
    claim_a: str
    claim_b: str
    explanation: str


class EvaluationResult(BaseModel):
    disease_name: str
    disease_summary: str
    targets: list[DiseaseTarget]
    candidates: list[DrugCandidate]
    safety_assessments: list[SafetyAssessment]
    contradictions: list[Contradiction]
    evidence_summaries: list[EvidenceSummary] = []
    data_sources: list[str] = []


class SSEEvent(BaseModel):
    agent: str
    status: str
    message: str
    data: dict | None = None
