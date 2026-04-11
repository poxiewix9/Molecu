"""Integration tests for API endpoints.

Uses FastAPI's TestClient to exercise real endpoint logic with
mock-injected cache data. No external API calls are made.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.cache import get_result_cache
from backend.models import (
    EvaluationResult, DrugCandidate, SafetyAssessment, SafetyVerdict,
    EvidenceScore, DiseaseTarget, EvidenceSummary, PaperCitation,
)


def _seed_cache():
    """Seed the result cache with a realistic evaluation result."""
    cache = get_result_cache()
    targets = [
        DiseaseTarget(
            target_id="ENSG00000197386",
            gene_name="HTT",
            protein_name="Huntingtin",
            association_score=0.9,
            description="Huntingtin protein associated with Huntington disease",
        ),
    ]
    score = EvidenceScore(
        target_association=24,
        trial_evidence=15,
        literature_support=15,
        safety_profile=20,
        total=74,
        breakdown="Target: 24/30 | Trial: 15/25 | Literature: 15/25 | Safety: 20/20",
    )
    candidates = [
        DrugCandidate(
            drug_name="Idebenone",
            trial_id="NCT00229632",
            original_indication="Alzheimer's Disease",
            phase="Phase 2",
            failure_reason="Insufficient efficacy",
            mechanism="Electron carrier in mitochondrial chain",
            repurposing_rationale="Mitochondrial dysfunction in huntington",
            confidence=0.74,
            evidence_score=score,
            sources=["ClinicalTrials.gov"],
        ),
    ]
    safety = [
        SafetyAssessment(
            drug_name="Idebenone",
            verdict=SafetyVerdict.PASS,
            adverse_events=["headache", "nausea"],
            reasoning="No high-risk events detected in FDA FAERS data.",
            organ_conflicts=[],
            report_counts={"headache": 12, "nausea": 8},
        ),
    ]
    evidence = [
        EvidenceSummary(
            drug_name="Idebenone",
            paper_count=3,
            evidence_summary="Three papers found linking idebenone to neuroprotection.",
            top_papers=[
                PaperCitation(
                    title="Idebenone in neurodegenerative disease",
                    authors="Smith J et al.",
                    journal="J Neurol",
                    year=2021,
                    pmid="12345678",
                    url="https://pubmed.ncbi.nlm.nih.gov/12345678",
                ),
            ],
        ),
    ]
    result = EvaluationResult(
        disease_name="Huntington Disease",
        disease_summary="Huntington disease is a neurodegenerative condition.",
        targets=targets,
        candidates=candidates,
        safety_assessments=safety,
        contradictions=[],
        evidence_summaries=evidence,
        data_sources=["Open Targets Platform", "ClinicalTrials.gov", "FDA FAERS"],
    )
    cache.put("huntington disease", result)
    return result


@pytest.fixture(autouse=True)
def seed():
    _seed_cache()
    yield


client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestExportEndpoint:
    def test_export_returns_report(self):
        resp = client.get("/api/export/huntington disease")
        assert resp.status_code == 200
        data = resp.json()
        assert "candidates" in data
        assert data["disease"]["name"] == "Huntington Disease"

    def test_export_missing_disease_returns_404(self):
        resp = client.get("/api/export/nonexistent_disease")
        assert resp.status_code == 404


class TestGrantAbstractEndpoint:
    @patch("backend.endpoints.grant_abstract.ask_llm", new_callable=AsyncMock)
    def test_grant_abstract_returns_text(self, mock_llm):
        mock_llm.return_value = "This is a generated abstract."
        resp = client.get(
            "/api/grant-abstract/Idebenone?disease=huntington disease"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "abstract" in data
        assert data["drug_name"] == "Idebenone"

    def test_grant_abstract_missing_disease_returns_404(self):
        resp = client.get("/api/grant-abstract/SomeDrug?disease=nonexistent")
        assert resp.status_code == 404


class TestRelatedDiseasesEndpoint:
    @patch("backend.endpoints.related_diseases.get_target_diseases", new_callable=AsyncMock)
    def test_related_diseases_returns_list(self, mock_targets):
        mock_targets.return_value = [
            {"name": "Parkinson Disease", "efo_id": "EFO_0002508", "score": 0.7},
        ]
        resp = client.get("/api/related-diseases/huntington disease")
        assert resp.status_code == 200
        data = resp.json()
        assert "related" in data
        assert data["query_disease"] == "huntington disease"

    def test_related_diseases_missing_returns_empty(self):
        resp = client.get("/api/related-diseases/nonexistent_xyz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["related"] == []


class TestEvaluateSSE:
    """Smoke test for the SSE streaming pipeline (mocked agents)."""

    @patch("backend.main.check_contradictions", new_callable=AsyncMock, return_value=[])
    @patch("backend.main.gather_evidence", new_callable=AsyncMock, return_value=[])
    @patch("backend.main.check_safety", new_callable=AsyncMock, return_value=[])
    @patch("backend.main.hunt_drugs", new_callable=AsyncMock, return_value=[])
    @patch("backend.main.analyze_disease", new_callable=AsyncMock, return_value=([], "", ""))
    def test_evaluate_streams_sse_events(self, *_mocks):
        resp = client.get("/api/evaluate/test_disease")
        assert resp.status_code == 200
        text = resp.text
        assert "disease_analyst" in text
        assert "drug_hunter" in text
        assert "safety_checker" in text
        assert "system" in text
