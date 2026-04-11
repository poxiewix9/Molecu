"""Tests for the DeBERTa NLI contradiction engine.

These tests validate the interface contract and thread-pool executor
without requiring the full model download (mocked for CI speed).
"""

import pytest
from unittest.mock import patch, MagicMock
import torch


class TestEvaluateClaimsContract:
    """Verify evaluate_claims returns the expected structure."""

    @patch("backend.contradiction_engine._load_model")
    def test_returns_required_keys(self, mock_load):
        mock_tok = MagicMock()
        mock_tok.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        mock_model = MagicMock()
        logits = torch.tensor([[2.0, 0.1, 0.5]])
        mock_model.return_value = MagicMock(logits=logits)
        mock_load.return_value = (mock_tok, mock_model)

        from backend.contradiction_engine import evaluate_claims
        result = evaluate_claims("Drug X is safe", "Drug X causes liver failure")

        assert "scores" in result
        assert "predicted_label" in result
        assert "conflict_detected" in result
        assert "claim_a" in result
        assert "claim_b" in result

    @patch("backend.contradiction_engine._load_model")
    def test_high_contradiction_flags_conflict(self, mock_load):
        mock_tok = MagicMock()
        mock_tok.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        mock_model = MagicMock()
        logits = torch.tensor([[5.0, -1.0, -1.0]])  # strong contradiction
        mock_model.return_value = MagicMock(logits=logits)
        mock_load.return_value = (mock_tok, mock_model)

        from backend.contradiction_engine import evaluate_claims
        result = evaluate_claims("A", "B")
        assert result["conflict_detected"] is True
        assert result["predicted_label"] == "contradiction"
        assert "explanation" in result

    @patch("backend.contradiction_engine._load_model")
    def test_low_contradiction_no_conflict(self, mock_load):
        mock_tok = MagicMock()
        mock_tok.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        mock_model = MagicMock()
        logits = torch.tensor([[-1.0, 5.0, 0.0]])  # strong entailment
        mock_model.return_value = MagicMock(logits=logits)
        mock_load.return_value = (mock_tok, mock_model)

        from backend.contradiction_engine import evaluate_claims
        result = evaluate_claims("Drug is safe", "Drug has no side effects")
        assert result["conflict_detected"] is False
        assert result["predicted_label"] == "entailment"

    @patch("backend.contradiction_engine._load_model")
    def test_scores_sum_to_one(self, mock_load):
        mock_tok = MagicMock()
        mock_tok.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        mock_model = MagicMock()
        logits = torch.tensor([[1.0, 1.0, 1.0]])
        mock_model.return_value = MagicMock(logits=logits)
        mock_load.return_value = (mock_tok, mock_model)

        from backend.contradiction_engine import evaluate_claims
        result = evaluate_claims("A", "B")
        total = sum(result["scores"].values())
        assert abs(total - 1.0) < 0.01


class TestEvaluateClaimsAsync:
    """Verify the async wrapper delegates to the thread pool."""

    @pytest.mark.asyncio
    @patch("backend.contradiction_engine._evaluate_sync")
    async def test_async_returns_result(self, mock_sync):
        mock_sync.return_value = {"conflict_detected": False, "scores": {}}

        from backend.contradiction_engine import evaluate_claims_async
        result = await evaluate_claims_async("A", "B")
        assert result["conflict_detected"] is False
        mock_sync.assert_called_once_with("A", "B")
