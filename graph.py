"""LangGraph churn-risk workflow with Human-in-the-Loop control."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, cast

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import NotRequired, TypedDict

from audit import append_audit_entry
from models import AuditDecision, AuditEntry

CONFIDENCE_THRESHOLD = 0.85
HIGH_RISK_ACTION = "increase_credit_limit"
AGENT_ID = "churn-risk-agent"

RouteName = Literal["low_risk", "high_risk"]
HumanDecision = Literal["approve", "reject", "edit"]


class GraphState(TypedDict):
    """Persistent state shared by every node in the workflow."""

    customer_id: str
    proposed_action: str
    confidence_score: float
    reasoning: str
    human_decision: HumanDecision | None
    total_operating_income: NotRequired[float]
    churn_probability: NotRequired[float]
    reviewer_id: NotRequired[str]
    execution_result: NotRequired[str]


def evaluate_customer(state: GraphState) -> dict[str, object]:
    """Deterministically mock an agent's churn reasoning.

    The lab explicitly permits a hard-coded/mock LLM output. Keeping this node
    deterministic makes the routing policy testable and avoids requiring API
    credentials in student code or GitHub Actions.
    """

    churn_probability = float(state.get("churn_probability", 0.50))
    total_operating_income = float(state.get("total_operating_income", 0.0))

    if not 0.0 <= churn_probability <= 1.0:
        raise ValueError("churn_probability must be between 0.0 and 1.0")
    if total_operating_income < 0:
        raise ValueError("total_operating_income must be non-negative")

    if churn_probability >= 0.75:
        proposed_action = HIGH_RISK_ACTION
        confidence_score = min(0.99, 0.88 + (churn_probability - 0.75) * 0.40)
        reasoning = (
            f"High churn probability ({churn_probability:.2f}) with TOI "
            f"{total_operating_income:,.0f}; retention may benefit from a credit-limit review."
        )
    elif churn_probability >= 0.40:
        proposed_action = "send_email"
        confidence_score = 0.82
        reasoning = (
            f"Moderate churn probability ({churn_probability:.2f}); a retention email is low-risk, "
            "but confidence is below the auto-execute threshold."
        )
    else:
        proposed_action = "send_email"
        confidence_score = 0.92
        reasoning = (
            f"Low churn probability ({churn_probability:.2f}); a routine retention email is a "
            "low-risk action with high confidence."
        )

    return {
        "proposed_action": proposed_action,
        "confidence_score": round(confidence_score, 4),
        "reasoning": reasoning,
    }


def route_action(state: GraphState) -> RouteName:
    """Apply hard policy first, then confidence-based routing."""

    action = state["proposed_action"]
    confidence = float(state["confidence_score"])

    # Rule 1: policy override always wins over model confidence.
    if action == HIGH_RISK_ACTION or action.startswith(f"{HIGH_RISK_ACTION}:"):
        return "high_risk"

    # Rule 2: high-confidence low-risk actions may auto-execute.
    if confidence >= CONFIDENCE_THRESHOLD:
        return "low_risk"

    # Rule 3: low confidence is escalated to a human.
    return "high_risk"


def _record_audit(
    state: GraphState,
    *,
    reviewer_id: str,
    decision: AuditDecision,
) -> None:
    entry = AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        agent_id=AGENT_ID,
        action=state["proposed_action"],
        confidence=float(state["confidence_score"]),
        reviewer_id=reviewer_id,
        decision=decision,
    )
    append_audit_entry(entry)


def execute_low_risk_action(state: GraphState) -> dict[str, object]:
    """Auto-execute an allowed low-risk action and audit it."""

    action = state["proposed_action"]
    _record_audit(state, reviewer_id="system", decision="auto_execute")
    return {"execution_result": f"executed:{action}"}


def execute_high_risk_action(state: GraphState) -> dict[str, object]:
    """Execute, abort, or execute an edited action after human review."""

    decision = state.get("human_decision")
    if decision not in {"approve", "reject", "edit"}:
        raise RuntimeError("high-risk action requires approve, reject, or edit decision")

    typed_decision = cast(HumanDecision, decision)
    reviewer_id = state.get("reviewer_id") or "unknown-reviewer"
    action = state["proposed_action"]

    if typed_decision == "reject":
        execution_result = f"aborted:{action}"
    else:
        execution_result = f"executed:{action}"

    _record_audit(
        state,
        reviewer_id=reviewer_id,
        decision=cast(AuditDecision, typed_decision),
    )
    return {"execution_result": execution_result}


def build_graph() -> Any:
    """Build a fresh compiled graph with thread-level in-memory checkpoints."""

    builder = StateGraph(GraphState)
    builder.add_node("evaluate_customer", evaluate_customer)
    builder.add_node("execute_low_risk_action", execute_low_risk_action)
    builder.add_node("execute_high_risk_action", execute_high_risk_action)

    builder.add_edge(START, "evaluate_customer")
    builder.add_conditional_edges(
        "evaluate_customer",
        route_action,
        {
            "low_risk": "execute_low_risk_action",
            "high_risk": "execute_high_risk_action",
        },
    )
    builder.add_edge("execute_low_risk_action", END)
    builder.add_edge("execute_high_risk_action", END)

    memory = MemorySaver()
    return builder.compile(
        checkpointer=memory,
        interrupt_before=["execute_high_risk_action"],
    )
