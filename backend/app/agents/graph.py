"""
LangGraph Multi-Agent Orchestration Graph.
Runs specialty deliberation panel conditionally:
- Only when rules engine produced >= 1 alert at moderate+ severity OR rules from >= 2 domains fired.
- Gated by default: approved_for_patient=False (Rule S8).
- Single-call free-tier mode or multi-specialist graph nodes.
"""
import hashlib
import json
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from backend.app.agents.moderator import Moderator
from backend.app.agents.specialists import run_single_call_specialist_panel
from backend.app.config import get_settings
from backend.app.rag.retriever import RAGRetriever


class PanelState(TypedDict):
    patient_profile: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    evidence_chunks: List[Dict[str, Any]]
    specialist_outputs: List[Dict[str, Any]]
    moderator_output: Dict[str, Any]
    approved_for_patient: bool
    fallback_badge: Optional[str]


def should_trigger_panel(alerts: List[Dict[str, Any]]) -> bool:
    """
    Section 7.9 Trigger Condition:
    Runs only when rules produced at least one alert at severity 'moderate' or above,
    or when rules from two or more domains fired.
    """
    if not alerts:
        return False

    has_moderate_plus = any(a.get("severity") in ["critical", "high", "moderate"] for a in alerts)
    domains = {a.get("domain", "") for a in alerts if a.get("domain")}
    has_multiple_domains = len(domains) >= 2

    return has_moderate_plus or has_multiple_domains


def compute_panel_cache_key(patient_profile: Dict[str, Any], alerts: List[Dict[str, Any]]) -> str:
    h = hashlib.sha256()
    h.update(json.dumps(patient_profile, sort_keys=True).encode())
    rule_ids = sorted([a["rule_id"] for a in alerts])
    h.update(json.dumps(rule_ids).encode())
    return h.hexdigest()


# Memory cache for panel runs to avoid repeat calls on same profile
_panel_cache: Dict[str, Dict[str, Any]] = {}


def retrieve_evidence_node(state: PanelState) -> Dict[str, Any]:
    retriever = RAGRetriever.get_instance()
    all_chunks = []
    seen = set()

    for a in state["alerts"]:
        chunks = retriever.retrieve(
            query=a["mechanism_summary"],
            rule_id=a["rule_id"],
            top_k=2,
            threshold=0.5,
        )
        for c in chunks:
            if c["chunk_id"] not in seen:
                seen.add(c["chunk_id"])
                all_chunks.append(c)

    return {"evidence_chunks": all_chunks}


def specialist_deliberation_node(state: PanelState) -> Dict[str, Any]:
    res = run_single_call_specialist_panel(
        patient_profile=state["patient_profile"],
        alerts=state["alerts"],
        evidence_chunks=state.get("evidence_chunks", []),
    )
    return {
        "specialist_outputs": res.get("specialists", []),
        "moderator_output": res.get("moderator", {}),
        "fallback_badge": res.get("fallback_badge"),
        "approved_for_patient": False,  # S8: Gate AI commentary
    }


def build_panel_graph():
    builder = StateGraph(PanelState)
    builder.add_node("retrieve_evidence", retrieve_evidence_node)
    builder.add_node("specialist_deliberation", specialist_deliberation_node)

    builder.set_entry_point("retrieve_evidence")
    builder.add_edge("retrieve_evidence", "specialist_deliberation")
    builder.add_edge("specialist_deliberation", END)

    return builder.compile()


_compiled_graph = None


def run_specialty_agent_panel(
    patient_profile: Dict[str, Any],
    alerts: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Main entry point for specialty agent deliberation.
    Returns None if trigger condition is not met.
    """
    global _compiled_graph
    if not should_trigger_panel(alerts):
        return None

    # Check cache
    cache_key = compute_panel_cache_key(patient_profile, alerts)
    if cache_key in _panel_cache:
        return _panel_cache[cache_key]

    if _compiled_graph is None:
        _compiled_graph = build_panel_graph()

    initial_state: PanelState = {
        "patient_profile": patient_profile,
        "alerts": alerts,
        "evidence_chunks": [],
        "specialist_outputs": [],
        "moderator_output": {},
        "approved_for_patient": False,
        "fallback_badge": None,
    }

    final_state = _compiled_graph.invoke(initial_state)

    result = {
        "specialists": final_state["specialist_outputs"],
        "moderator": final_state["moderator_output"],
        "approved_for_patient": False,  # S8 Gate
        "fallback_badge": final_state.get("fallback_badge"),
    }
    _panel_cache[cache_key] = result
    return result

