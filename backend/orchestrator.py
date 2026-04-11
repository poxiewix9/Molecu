"""
Phase 2 + 3 + 5: LangGraph Orchestrator
Wires TargetAgent → GenerativeAgent → ADMETAgent → EvaluationNode
with conditional edges, contradiction detection, and RAG memory.
"""

import csv
import os
import random
from typing import TypedDict
from langgraph.graph import StateGraph, END

from backend.contradiction_engine import evaluate_claims
from backend.memory_store import save_failed_molecule, retrieve_past_failures

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


# ---------------------------------------------------------------------------
# MoleculeState (Phase 2, Step 1)
# ---------------------------------------------------------------------------
class MoleculeState(TypedDict):
    current_smiles: str
    target_affinity: float
    toxicity_flags: list[str]
    status: str  # "active" | "failed" | "approved" | "conflict"
    agent_logs: list[dict]  # each: {"agent_name", "action", "confidence"}
    contradiction_report: dict | None
    past_failures: list[dict]
    cycle_count: int


# ---------------------------------------------------------------------------
# Dataset loaders
# ---------------------------------------------------------------------------
def _load_csv(filename: str) -> list[dict]:
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


_ZINC_MOLECULES: list[dict] = []
_TOXIC_SMILES: set[str] = set()
_BACE_DATA: list[dict] = []


def _ensure_data():
    global _ZINC_MOLECULES, _TOXIC_SMILES, _BACE_DATA
    if not _ZINC_MOLECULES:
        _ZINC_MOLECULES = _load_csv("zinc_subset.csv")
    if not _TOXIC_SMILES:
        rows = _load_csv("clintox_toxic.csv")
        _TOXIC_SMILES = {r["smiles"].strip() for r in rows}
    if not _BACE_DATA:
        _BACE_DATA = _load_csv("bace_binding.csv")


# ---------------------------------------------------------------------------
# Agent nodes (Phase 2, Steps 2-3)
# ---------------------------------------------------------------------------
def target_agent(state: MoleculeState) -> dict:
    """Biology / TargetAgent: picks a binding-affinity target from BACE data."""
    _ensure_data()
    active_binders = [r for r in _BACE_DATA if r.get("binding_label") == "active"]
    ref = random.choice(active_binders) if active_binders else _BACE_DATA[0]
    affinity = float(ref["pIC50"])

    log_entry = {
        "agent_name": "TargetAgent (Biology)",
        "action": f"Selected BACE1 target with reference pIC50={affinity}. "
                  f"Reference compound: {ref['smiles'][:40]}…",
        "confidence": round(random.uniform(0.75, 0.95), 2),
    }
    return {
        "target_affinity": affinity,
        "agent_logs": state["agent_logs"] + [log_entry],
    }


def generative_agent(state: MoleculeState) -> dict:
    """Chemistry / GenerativeAgent: proposes a SMILES string from ZINC subset."""
    _ensure_data()

    past = retrieve_past_failures(
        f"BACE1 inhibitor target affinity {state['target_affinity']}"
    )
    neg_examples = ""
    if past:
        neg_examples = " | Negative examples to avoid: " + "; ".join(
            f"{f['smiles']} ({f['failure_reason']})" for f in past
        )

    candidate = random.choice(_ZINC_MOLECULES)
    smiles = candidate["smiles"].strip()

    log_entry = {
        "agent_name": "GenerativeAgent (Chemistry)",
        "action": f"Generated candidate {smiles} with MW={candidate.get('mwt','?')} and "
                  f"logP={candidate.get('logp','?')}. This molecule is safe and suitable "
                  f"for BACE1 binding.{neg_examples}",
        "confidence": round(random.uniform(0.60, 0.92), 2),
    }
    return {
        "current_smiles": smiles,
        "agent_logs": state["agent_logs"] + [log_entry],
        "past_failures": past,
    }


def admet_agent(state: MoleculeState) -> dict:
    """Pharmacology / ADMETAgent: checks ClinTox for known toxicity."""
    _ensure_data()
    smiles = state["current_smiles"]
    flags: list[str] = list(state.get("toxicity_flags", []))

    if smiles in _TOXIC_SMILES:
        tox_rows = _load_csv("clintox_toxic.csv")
        reason = next(
            (r["toxicity_reason"] for r in tox_rows if r["smiles"].strip() == smiles),
            "Known toxic compound",
        )
        flags.append(f"TOXIC: {reason}")
        action = (f"This molecule is highly toxic and dangerous. {reason}. "
                  f"It must not be used in any drug development pipeline.")
        confidence = 0.98
    else:
        logp = next(
            (float(m["logp"]) for m in _ZINC_MOLECULES if m["smiles"].strip() == smiles),
            None,
        )
        if logp is not None and logp > 4.0:
            flags.append(f"WARNING: High logP ({logp}) — poor solubility risk")
            action = (f"This molecule has dangerously high lipophilicity (logP={logp}). "
                      f"It is toxic and should not proceed to clinical trials.")
            confidence = round(random.uniform(0.60, 0.80), 2)
        else:
            action = (f"ADMET screening passed. {smiles} shows acceptable toxicity "
                      f"profile and is safe for further development.")
            confidence = round(random.uniform(0.80, 0.95), 2)

    log_entry = {
        "agent_name": "ADMETAgent (Pharmacology)",
        "action": action,
        "confidence": confidence,
    }
    return {
        "toxicity_flags": flags,
        "agent_logs": state["agent_logs"] + [log_entry],
    }


# ---------------------------------------------------------------------------
# Evaluation node — contradiction engine (Phase 3)
# ---------------------------------------------------------------------------
def evaluation_node(state: MoleculeState) -> dict:
    """Runs NLI contradiction check between the last two agent claims."""
    logs = state["agent_logs"]
    if len(logs) < 2:
        return {"contradiction_report": None}

    claim_a = logs[-2]["action"]
    claim_b = logs[-1]["action"]
    result = evaluate_claims(claim_a, claim_b)

    if result["conflict_detected"]:
        return {
            "status": "conflict",
            "contradiction_report": result,
            "agent_logs": state["agent_logs"] + [{
                "agent_name": "ContradictionEngine (ML)",
                "action": result.get("explanation", "Contradiction detected between agents"),
                "confidence": result["scores"]["contradiction"],
            }],
        }
    return {"contradiction_report": result}


# ---------------------------------------------------------------------------
# Terminal nodes
# ---------------------------------------------------------------------------
def fail_node(state: MoleculeState) -> dict:
    """Terminal failure — persist to memory store."""
    reason_parts = state.get("toxicity_flags", [])
    cr = state.get("contradiction_report")
    if cr and cr.get("conflict_detected"):
        reason_parts.append(cr.get("explanation", "Contradiction detected"))

    reason = "; ".join(reason_parts) if reason_parts else "Unknown failure"
    save_failed_molecule(state["current_smiles"], reason)

    return {
        "status": "failed",
        "agent_logs": state["agent_logs"] + [{
            "agent_name": "System",
            "action": f"Pipeline FAILED. Molecule {state['current_smiles']} saved to memory. "
                      f"Reason: {reason}",
            "confidence": 1.0,
        }],
    }


def approve_node(state: MoleculeState) -> dict:
    return {
        "status": "approved",
        "agent_logs": state["agent_logs"] + [{
            "agent_name": "System",
            "action": f"Molecule {state['current_smiles']} APPROVED with target affinity "
                      f"{state['target_affinity']}. No toxicity or contradictions.",
            "confidence": 1.0,
        }],
    }


# ---------------------------------------------------------------------------
# Conditional routing (Phase 2, Step 4)
# ---------------------------------------------------------------------------
def after_admet(state: MoleculeState) -> str:
    if state.get("toxicity_flags"):
        return "fail"
    return "evaluate"


def after_evaluation(state: MoleculeState) -> str:
    if state.get("status") == "conflict":
        return "fail"
    return "approve"


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------
def build_graph() -> StateGraph:
    graph = StateGraph(MoleculeState)

    graph.add_node("target_agent", target_agent)
    graph.add_node("generative_agent", generative_agent)
    graph.add_node("admet_agent", admet_agent)
    graph.add_node("evaluation_node", evaluation_node)
    graph.add_node("fail_node", fail_node)
    graph.add_node("approve_node", approve_node)

    graph.set_entry_point("target_agent")
    graph.add_edge("target_agent", "generative_agent")
    graph.add_edge("generative_agent", "admet_agent")
    graph.add_conditional_edges("admet_agent", after_admet, {
        "fail": "fail_node",
        "evaluate": "evaluation_node",
    })
    graph.add_conditional_edges("evaluation_node", after_evaluation, {
        "fail": "fail_node",
        "approve": "approve_node",
    })
    graph.add_edge("fail_node", END)
    graph.add_edge("approve_node", END)

    return graph


def compile_graph():
    return build_graph().compile()


# ---------------------------------------------------------------------------
# Convenience runner
# ---------------------------------------------------------------------------
def run_pipeline() -> MoleculeState:
    app = compile_graph()
    initial_state: MoleculeState = {
        "current_smiles": "",
        "target_affinity": 0.0,
        "toxicity_flags": [],
        "status": "active",
        "agent_logs": [],
        "contradiction_report": None,
        "past_failures": [],
        "cycle_count": 0,
    }
    final = app.invoke(initial_state)
    return final
