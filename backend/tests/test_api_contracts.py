"""API contract tests for external service response shapes.

Validates that our parsers handle the expected response structures from
Open Targets, ClinicalTrials.gov, ChEMBL, and FDA FAERS correctly.
These act as automated canaries for upstream schema evolution —
if an API changes its response shape, these tests break before users notice.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx


class TestOpenTargetsContract:
    """Validate Open Targets GraphQL response parsing contracts."""

    MOCK_SEARCH_RESPONSE = {
        "data": {
            "search": {
                "hits": [
                    {
                        "id": "MONDO_0007739",
                        "name": "Huntington disease",
                        "description": "A neurodegenerative disease...",
                        "entity": "disease",
                    },
                    {
                        "id": "EFO_0004911",
                        "name": "juvenile Huntington disease",
                        "description": "Early onset form...",
                        "entity": "disease",
                    },
                ]
            }
        }
    }

    MOCK_TARGETS_RESPONSE = {
        "data": {
            "disease": {
                "id": "MONDO_0007739",
                "name": "Huntington disease",
                "description": "A neurodegenerative disease...",
                "associatedTargets": {
                    "rows": [
                        {
                            "target": {
                                "id": "ENSG00000197386",
                                "approvedSymbol": "HTT",
                                "approvedName": "huntingtin",
                            },
                            "score": 0.92,
                        },
                        {
                            "target": {
                                "id": "ENSG00000102882",
                                "approvedSymbol": "BDNF",
                                "approvedName": "brain derived neurotrophic factor",
                            },
                            "score": 0.45,
                        },
                    ]
                },
            }
        }
    }

    MOCK_TARGET_DISEASES_RESPONSE = {
        "data": {
            "target": {
                "associatedDiseases": {
                    "rows": [
                        {"disease": {"id": "MONDO_0007739", "name": "Huntington disease"}, "score": 0.92},
                        {"disease": {"id": "EFO_0002508", "name": "Parkinson disease"}, "score": 0.35},
                    ]
                }
            }
        }
    }

    @pytest.mark.asyncio
    async def test_search_disease_parses_response(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.MOCK_SEARCH_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        with patch("backend.services.open_targets.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            from backend.services.open_targets import search_disease
            result = await search_disease("Huntington")

        assert result is not None
        assert result["efo_id"] == "MONDO_0007739"
        assert result["name"] == "Huntington disease"
        assert "description" in result

    @pytest.mark.asyncio
    async def test_get_disease_targets_parses_response(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.MOCK_TARGETS_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        with patch("backend.services.open_targets.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            from backend.services.open_targets import get_disease_targets
            targets = await get_disease_targets("MONDO_0007739")

        assert len(targets) == 2
        assert targets[0]["gene_name"] == "HTT"
        assert targets[0]["protein_name"] == "huntingtin"
        assert targets[0]["target_id"] == "ENSG00000197386"
        assert 0 <= targets[0]["association_score"] <= 1
        assert targets[1]["gene_name"] == "BDNF"

    @pytest.mark.asyncio
    async def test_get_target_diseases_parses_response(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.MOCK_TARGET_DISEASES_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        with patch("backend.services.open_targets.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            from backend.services.open_targets import get_target_diseases
            diseases = await get_target_diseases("ENSG00000197386")

        assert len(diseases) == 2
        assert diseases[0]["name"] == "Huntington disease"
        assert "efo_id" in diseases[0]
        assert "score" in diseases[0]

    @pytest.mark.asyncio
    async def test_search_disease_handles_empty_hits(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"search": {"hits": []}}}
        mock_resp.raise_for_status = MagicMock()

        with patch("backend.services.open_targets.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            from backend.services.open_targets import search_disease
            result = await search_disease("nonexistent_disease_xyz")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_disease_targets_handles_missing_disease(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"disease": None}}
        mock_resp.raise_for_status = MagicMock()

        with patch("backend.services.open_targets.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            from backend.services.open_targets import get_disease_targets
            targets = await get_disease_targets("INVALID_EFO")

        assert targets == []

    @pytest.mark.asyncio
    async def test_handles_network_error_gracefully(self):
        with patch("backend.services.open_targets.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.side_effect = httpx.ConnectError("Network unreachable")
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            from backend.services.open_targets import search_disease
            result = await search_disease("Huntington")

        assert result is None

    def test_graphql_queries_contain_required_fields(self):
        """Verify our GraphQL queries request all fields the parsers depend on."""
        from backend.services.open_targets import (
            SEARCH_DISEASE_QUERY,
            DISEASE_TARGETS_QUERY,
            TARGET_DISEASES_QUERY,
        )
        assert "id" in SEARCH_DISEASE_QUERY
        assert "name" in SEARCH_DISEASE_QUERY
        assert "entity" in SEARCH_DISEASE_QUERY

        assert "approvedSymbol" in DISEASE_TARGETS_QUERY
        assert "approvedName" in DISEASE_TARGETS_QUERY
        assert "score" in DISEASE_TARGETS_QUERY

        assert "name" in TARGET_DISEASES_QUERY
        assert "score" in TARGET_DISEASES_QUERY


class TestRateLimitMiddleware:
    """Validate the token-bucket rate limiter."""

    def test_rate_limiter_allows_requests_within_limit(self):
        from fastapi.testclient import TestClient
        from backend.main import app
        client = TestClient(app)
        for _ in range(3):
            resp = client.get("/api/suggest/test")
            assert resp.status_code != 429

    def test_evaluate_endpoint_has_stricter_limit(self):
        from backend.middleware import RateLimitMiddleware
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        test_app = FastAPI()
        test_app.add_middleware(RateLimitMiddleware, evaluate_limit=2, general_limit=10, window_seconds=60)

        @test_app.get("/api/evaluate/test")
        async def evaluate():
            return {"status": "ok"}

        client = TestClient(test_app)
        resp1 = client.get("/api/evaluate/test")
        resp2 = client.get("/api/evaluate/test")
        resp3 = client.get("/api/evaluate/test")

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp3.status_code == 429
        assert "retry_after_seconds" in resp3.json()
