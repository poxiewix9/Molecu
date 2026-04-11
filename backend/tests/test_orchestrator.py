"""Tests for the LangGraph molecule evaluation orchestrator.

Validates the separate molecular screening pipeline (orchestrator.py) which
uses LangGraph for BACE1 target binding evaluation with ZINC/ClinTox/BACE
datasets and DeBERTa NLI contradiction detection between agents.
"""

import pytest
from unittest.mock import patch, MagicMock

from backend.orchestrator import (
    MoleculeState,
    target_agent,
    generative_agent,
    admet_agent,
    evaluation_node,
    after_admet,
    after_evaluation,
    fail_node,
    approve_node,
    build_graph,
)


def _base_state(**overrides) -> MoleculeState:
    state: MoleculeState = {
        "current_smiles": "CCO",
        "target_affinity": 6.5,
        "toxicity_flags": [],
        "status": "active",
        "agent_logs": [],
        "contradiction_report": None,
        "past_failures": [],
        "cycle_count": 0,
    }
    state.update(overrides)
    return state


class TestMoleculeAgents:
    """Unit tests for individual pipeline agent nodes."""

    @patch("backend.orchestrator._ensure_data")
    @patch("backend.orchestrator._BACE_DATA", [
        {"smiles": "CC(=O)OC1=CC=CC=C1C(O)=O", "binding_label": "active", "pIC50": "7.2"},
    ])
    def test_target_agent_selects_binding_target(self, _):
        state = _base_state()
        result = target_agent(state)
        assert "target_affinity" in result
        assert result["target_affinity"] == 7.2
        assert len(result["agent_logs"]) == 1
        assert result["agent_logs"][0]["agent_name"] == "TargetAgent (Biology)"

    @patch("backend.orchestrator.retrieve_past_failures", return_value=[])
    @patch("backend.orchestrator._ensure_data")
    @patch("backend.orchestrator._ZINC_MOLECULES", [
        {"smiles": "CC(=O)O", "mwt": "60.05", "logp": "0.17"},
    ])
    def test_generative_agent_proposes_candidate(self, _, __):
        state = _base_state()
        result = generative_agent(state)
        assert result["current_smiles"] == "CC(=O)O"
        assert len(result["agent_logs"]) == 1
        assert "GenerativeAgent" in result["agent_logs"][0]["agent_name"]

    @patch("backend.orchestrator._ensure_data")
    @patch("backend.orchestrator._TOXIC_SMILES", {"TOXIC_SMILES"})
    def test_admet_flags_known_toxic(self, _):
        state = _base_state(current_smiles="TOXIC_SMILES")
        result = admet_agent(state)
        assert any("TOXIC" in f for f in result["toxicity_flags"])

    @patch("backend.orchestrator._ensure_data")
    @patch("backend.orchestrator._TOXIC_SMILES", set())
    @patch("backend.orchestrator._ZINC_MOLECULES", [{"smiles": "CCO", "logp": "1.0"}])
    def test_admet_passes_safe_compound(self, _):
        state = _base_state(current_smiles="CCO")
        result = admet_agent(state)
        flags = result["toxicity_flags"]
        assert not any("TOXIC" in f for f in flags)


class TestConditionalRouting:
    """Test pipeline routing logic."""

    def test_after_admet_routes_to_fail_on_toxicity(self):
        state = _base_state(toxicity_flags=["TOXIC: Known carcinogen"])
        assert after_admet(state) == "fail"

    def test_after_admet_routes_to_evaluate_when_clean(self):
        state = _base_state(toxicity_flags=[])
        assert after_admet(state) == "evaluate"

    def test_after_evaluation_routes_to_fail_on_conflict(self):
        state = _base_state(status="conflict")
        assert after_evaluation(state) == "fail"

    def test_after_evaluation_routes_to_approve_when_clean(self):
        state = _base_state(status="active")
        assert after_evaluation(state) == "approve"


class TestTerminalNodes:
    """Test pipeline terminal states."""

    @patch("backend.orchestrator.save_failed_molecule")
    def test_fail_node_saves_to_memory(self, mock_save):
        state = _base_state(toxicity_flags=["TOXIC: Hepatotoxic"])
        result = fail_node(state)
        assert result["status"] == "failed"
        mock_save.assert_called_once()

    def test_approve_node_marks_approved(self):
        state = _base_state()
        result = approve_node(state)
        assert result["status"] == "approved"
        assert any("APPROVED" in log["action"] for log in result["agent_logs"])


class TestEvaluationNode:
    """Test NLI contradiction detection integration."""

    @patch("backend.orchestrator.evaluate_claims")
    def test_detects_conflict(self, mock_nli):
        mock_nli.return_value = {
            "conflict_detected": True,
            "scores": {"contradiction": 0.95, "entailment": 0.02, "neutral": 0.03},
            "explanation": "Contradiction between safety and efficacy claims",
        }
        state = _base_state(agent_logs=[
            {"agent_name": "A", "action": "This drug is safe", "confidence": 0.9},
            {"agent_name": "B", "action": "This drug is toxic", "confidence": 0.95},
        ])
        result = evaluation_node(state)
        assert result["status"] == "conflict"
        assert result["contradiction_report"]["conflict_detected"] is True

    @patch("backend.orchestrator.evaluate_claims")
    def test_no_conflict_passes_through(self, mock_nli):
        mock_nli.return_value = {
            "conflict_detected": False,
            "scores": {"contradiction": 0.1, "entailment": 0.7, "neutral": 0.2},
        }
        state = _base_state(agent_logs=[
            {"agent_name": "A", "action": "Drug binds BACE1", "confidence": 0.85},
            {"agent_name": "B", "action": "Drug passes ADMET", "confidence": 0.9},
        ])
        result = evaluation_node(state)
        assert result.get("status") != "conflict"


class TestGraphConstruction:
    """Verify LangGraph graph structure."""

    def test_build_graph_creates_valid_graph(self):
        graph = build_graph()
        assert graph is not None

    @patch("backend.orchestrator.save_failed_molecule")
    @patch("backend.orchestrator.retrieve_past_failures", return_value=[])
    @patch("backend.orchestrator.evaluate_claims", return_value={
        "conflict_detected": False,
        "scores": {"contradiction": 0.1, "entailment": 0.6, "neutral": 0.3},
    })
    @patch("backend.orchestrator._ensure_data")
    @patch("backend.orchestrator._BACE_DATA", [{"smiles": "CC", "binding_label": "active", "pIC50": "6.0"}])
    @patch("backend.orchestrator._ZINC_MOLECULES", [{"smiles": "CCO", "mwt": "46", "logp": "0.5"}])
    @patch("backend.orchestrator._TOXIC_SMILES", set())
    def test_full_pipeline_approve_path(self, *_):
        from backend.orchestrator import compile_graph
        app = compile_graph()
        result = app.invoke({
            "current_smiles": "",
            "target_affinity": 0.0,
            "toxicity_flags": [],
            "status": "active",
            "agent_logs": [],
            "contradiction_report": None,
            "past_failures": [],
            "cycle_count": 0,
        })
        assert result["status"] == "approved"
