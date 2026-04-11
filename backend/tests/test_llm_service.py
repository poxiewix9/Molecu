"""Tests for the LLM service wrapper — validates graceful fallback behavior.

These tests ensure the LLM service never blocks or crashes the pipeline,
even when the API key is missing or the service returns errors.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestAskLlm:
    """Verify ask_llm returns empty string on any failure."""

    @pytest.mark.asyncio
    @patch("backend.services.llm._get_client", return_value=None)
    async def test_returns_empty_when_no_client(self, _mock):
        from backend.services.llm import ask_llm
        result = await ask_llm("system", "user")
        assert result == ""

    @pytest.mark.asyncio
    @patch("backend.services.llm._get_client")
    async def test_returns_empty_on_exception(self, mock_client):
        mock_client.return_value = MagicMock()
        mock_client.return_value.models.generate_content.side_effect = Exception("Rate limited")
        from backend.services.llm import ask_llm
        result = await ask_llm("system", "user")
        assert result == ""


class TestAskLlmJson:
    """Verify ask_llm_json parses JSON or returns None on failure."""

    @pytest.mark.asyncio
    @patch("backend.services.llm.ask_llm")
    async def test_parses_valid_json(self, mock_llm):
        mock_llm.return_value = '[{"drug": "Aspirin"}]'
        from backend.services.llm import ask_llm_json
        result = await ask_llm_json("system", "user")
        assert isinstance(result, list)
        assert result[0]["drug"] == "Aspirin"

    @pytest.mark.asyncio
    @patch("backend.services.llm.ask_llm")
    async def test_strips_markdown_fences(self, mock_llm):
        mock_llm.return_value = '```json\n[{"a": 1}]\n```'
        from backend.services.llm import ask_llm_json
        result = await ask_llm_json("system", "user")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    @patch("backend.services.llm.ask_llm")
    async def test_returns_none_on_empty(self, mock_llm):
        mock_llm.return_value = ""
        from backend.services.llm import ask_llm_json
        result = await ask_llm_json("system", "user")
        assert result is None

    @pytest.mark.asyncio
    @patch("backend.services.llm.ask_llm")
    async def test_returns_none_on_invalid_json(self, mock_llm):
        mock_llm.return_value = "not json at all"
        from backend.services.llm import ask_llm_json
        result = await ask_llm_json("system", "user")
        assert result is None
