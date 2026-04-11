"""Tests for Pydantic data models — validates schema contracts between backend and frontend.

These tests ensure that the data contracts are enforced, serialization
works correctly, and required fields are present.
"""

import pytest
from pydantic import ValidationError
from backend.models import (
    DiseaseTarget,
    DrugCandidate,
    SafetyAssessment,
    SafetyVerdict,
    EvidenceScore,
    EvidenceSummary,
    PaperCitation,
    Contradiction,
    EvaluationResult,
    SSEEvent,
)


class TestDiseaseTarget:
    def test_valid_target(self):
        t = DiseaseTarget(
            gene_name="FXN",
            protein_name="frataxin",
            target_id="ENSG00000165060",
            association_score=0.85,
            description="Frataxin — mitochondrial protein",
        )
        assert t.gene_name == "FXN"
        assert 0 <= t.association_score <= 1

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            DiseaseTarget(gene_name="FXN")


class TestDrugCandidate:
    def test_minimal_candidate(self):
        c = DrugCandidate(
            drug_name="Idebenone",
            trial_id="NCT00229632",
            original_indication="Friedreich's Ataxia",
            phase="Phase 3",
            failure_reason="Did not meet primary endpoint",
            mechanism="Electron carrier in mitochondrial chain",
            repurposing_rationale="Targets mitochondrial dysfunction",
            confidence=0.75,
        )
        assert c.drug_name == "Idebenone"
        assert c.evidence_score is None
        assert c.sources == []

    def test_candidate_with_score(self):
        score = EvidenceScore(
            target_association=20, trial_evidence=15,
            literature_support=10, safety_profile=15,
            total=60, breakdown="test",
        )
        c = DrugCandidate(
            drug_name="Test",
            trial_id="NCT0001",
            original_indication="Test",
            phase="Phase 2",
            failure_reason="Test",
            mechanism="Test",
            repurposing_rationale="Test",
            confidence=0.6,
            evidence_score=score,
            sources=["ClinicalTrials.gov", "ChEMBL"],
        )
        assert c.evidence_score.total == 60
        assert len(c.sources) == 2

    def test_serialization_roundtrip(self):
        c = DrugCandidate(
            drug_name="Aspirin",
            trial_id="NCT0001",
            original_indication="Pain",
            phase="Phase 3",
            failure_reason="N/A",
            mechanism="COX inhibition",
            repurposing_rationale="Anti-inflammatory",
            confidence=0.8,
        )
        d = c.model_dump()
        c2 = DrugCandidate(**d)
        assert c2.drug_name == c.drug_name


class TestSafetyAssessment:
    def test_pass_verdict(self):
        sa = SafetyAssessment(
            drug_name="Aspirin",
            verdict=SafetyVerdict.PASS,
            adverse_events=["headache", "nausea"],
            reasoning="No critical signals",
            organ_conflicts=[],
        )
        assert sa.verdict == SafetyVerdict.PASS

    def test_hard_fail_verdict(self):
        sa = SafetyAssessment(
            drug_name="Dangerous Drug",
            verdict=SafetyVerdict.HARD_FAIL,
            adverse_events=["cardiac arrest", "death"],
            reasoning="Multiple fatal events",
            organ_conflicts=["heart"],
        )
        assert sa.verdict == SafetyVerdict.HARD_FAIL
        assert "heart" in sa.organ_conflicts


class TestEvidenceScore:
    def test_score_bounds(self):
        score = EvidenceScore(
            target_association=30, trial_evidence=25,
            literature_support=25, safety_profile=20,
            total=100, breakdown="max",
        )
        assert score.total == 100

    def test_component_sum_equals_total(self):
        score = EvidenceScore(
            target_association=15, trial_evidence=15,
            literature_support=8, safety_profile=10,
            total=48, breakdown="test",
        )
        computed = (
            score.target_association + score.trial_evidence
            + score.literature_support + score.safety_profile
        )
        assert computed == score.total


class TestContradiction:
    def test_blocking_contradiction(self):
        c = Contradiction(
            severity="BLOCKING",
            agent_a="Drug Hunter",
            agent_b="Safety Checker",
            claim_a="Drug is promising",
            claim_b="Drug has fatal side effects",
            explanation="Confidence vs safety conflict",
        )
        assert c.severity == "BLOCKING"


class TestEvaluationResult:
    def test_empty_evaluation(self):
        r = EvaluationResult(
            disease_name="Test Disease",
            disease_summary="A test",
            targets=[],
            candidates=[],
            safety_assessments=[],
            contradictions=[],
        )
        assert r.evidence_summaries == []
        assert r.data_sources == []

    def test_full_serialization(self):
        r = EvaluationResult(
            disease_name="Test Disease",
            disease_summary="A test",
            targets=[],
            candidates=[],
            safety_assessments=[],
            contradictions=[],
            evidence_summaries=[],
            data_sources=["Open Targets", "PubMed"],
        )
        d = r.model_dump()
        assert d["disease_name"] == "Test Disease"
        assert len(d["data_sources"]) == 2
