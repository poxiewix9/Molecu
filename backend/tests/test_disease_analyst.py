"""Tests for the Disease Analyst agent — validates graceful handling of API responses.

Mocks Open Targets and LLM calls so tests run offline with no external dependencies.
"""

import pytest
from unittest.mock import patch, AsyncMock


class TestAnalyzeDisease:
    """Verify analyze_disease handles various Open Targets response scenarios."""

    @pytest.mark.asyncio
    @patch("backend.agents.disease_analyst.ask_llm", new_callable=AsyncMock, return_value="Test summary")
    @patch("backend.agents.disease_analyst.get_disease_targets", new_callable=AsyncMock)
    @patch("backend.agents.disease_analyst.search_disease", new_callable=AsyncMock)
    async def test_returns_targets_and_summary(self, mock_search, mock_targets, mock_llm):
        mock_search.return_value = {"efo_id": "EFO_001", "name": "Test Disease", "description": "A test"}
        mock_targets.return_value = [
            {"gene_name": "TP53", "protein_name": "Tumor protein p53", "target_id": "ENSG001", "association_score": 0.9},
        ]

        from backend.agents.disease_analyst import analyze_disease
        targets, summary, efo_id = await analyze_disease("Test Disease")

        assert len(targets) == 1
        assert targets[0].gene_name == "TP53"
        assert efo_id == "EFO_001"
        assert summary == "Test summary"

    @pytest.mark.asyncio
    @patch("backend.agents.disease_analyst.ask_llm", new_callable=AsyncMock, return_value="")
    @patch("backend.agents.disease_analyst.get_disease_targets", new_callable=AsyncMock, return_value=[])
    @patch("backend.agents.disease_analyst.search_disease", new_callable=AsyncMock, return_value=None)
    async def test_handles_no_results_gracefully(self, mock_search, mock_targets, mock_llm):
        from backend.agents.disease_analyst import analyze_disease
        targets, summary, efo_id = await analyze_disease("Unknown Disease XYZ")

        assert targets == []
        assert efo_id == ""
        assert "Unknown Disease XYZ" in summary

    @pytest.mark.asyncio
    @patch("backend.agents.disease_analyst.ask_llm", new_callable=AsyncMock, return_value="")
    @patch("backend.agents.disease_analyst.get_disease_targets", new_callable=AsyncMock)
    @patch("backend.agents.disease_analyst.search_disease", new_callable=AsyncMock)
    async def test_fallback_summary_when_llm_unavailable(self, mock_search, mock_targets, mock_llm):
        mock_search.return_value = {"efo_id": "EFO_001", "name": "ALS", "description": "Motor neuron disease"}
        mock_targets.return_value = [
            {"gene_name": "SOD1", "protein_name": "Superoxide dismutase", "target_id": "ENSG002", "association_score": 0.85},
        ]

        from backend.agents.disease_analyst import analyze_disease
        targets, summary, efo_id = await analyze_disease("ALS")

        assert len(targets) == 1
        assert "Motor neuron disease" in summary or "SOD1" in summary
