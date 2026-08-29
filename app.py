"""Streamlit approval dashboard for the Lab 27 HITL workflow."""

from __future__ import annotations

from typing import Any, cast
from uuid import uuid4

import streamlit as st

from audit import load_audit_entries
from graph import CONFIDENCE_THRESHOLD, GraphState, build_graph

st.set_page_config(page_title="Lab 27 · HITL", page_icon="🧑‍⚖️", layout="wide")


@st.cache_resource
def _new_graph():
    return build_graph()


def _config() -> dict[str, dict[str, str]]:
    return {"configurable": {"thread_id": st.session_state.thread_id}}


def _resume(decision: str, reviewer_id: str, edited_action: str | None = None) -> None:
    update: dict[str, object] = {
        "human_decision": decision,
        "reviewer_id": reviewer_id.strip() or "operator_01",
    }
    if edited_action is not None:
        update["proposed_action"] = edited_action.strip()

    st.session_state.graph.update_state(_config(), update)
    st.session_state.last_result = st.session_state.graph.invoke(None, _config())
    st.rerun()


if "graph" not in st.session_state:
    st.session_state.graph = _new_graph()
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid4())
if "started" not in st.session_state:
    st.session_state.started = False
if "last_result" not in st.session_state:
    st.session_state.last_result = None

st.title("Human-in-the-Loop · Churn Risk Agent")
st.caption(
    "Hard policy overrides confidence. Low-risk actions auto-execute only when "
    f"confidence ≥ {CONFIDENCE_THRESHOLD:.2f}."
)

with st.sidebar:
    st.header("Customer input")
    customer_id = st.text_input("Customer ID", value="CUST001")
    total_operating_income = st.number_input(
        "Total Operating Income (TOI)",
        min_value=0.0,
        value=20_000_000.0,
        step=1_000_000.0,
    )
    churn_probability = st.slider(
        "Churn probability",
        min_value=0.0,
        max_value=1.0,
        value=0.91,
        step=0.01,
    )
    reviewer_id = st.text_input("Reviewer ID", value="operator_01")

    if st.button("Start evaluation", type="primary", use_container_width=True):
        st.session_state.thread_id = str(uuid4())
        initial_state: GraphState = {
            "customer_id": customer_id.strip() or "CUST001",
            "total_operating_income": float(total_operating_income),
            "churn_probability": float(churn_probability),
            "proposed_action": "",
            "confidence_score": 0.0,
            "reasoning": "",
            "human_decision": None,
            "reviewer_id": "",
            "execution_result": "",
        }
        st.session_state.last_result = st.session_state.graph.invoke(initial_state, _config())
        st.session_state.started = True
        st.rerun()

if not st.session_state.started:
    st.info("Nhập dữ liệu ở sidebar và bấm **Start evaluation** để chạy workflow.")
else:
    snapshot = st.session_state.graph.get_state(_config())
    values = cast(dict[str, Any], snapshot.values)

    st.subheader("Action card")
    c1, c2, c3 = st.columns(3)
    c1.metric("Customer", values.get("customer_id", "—"))
    c2.metric("Confidence", f"{float(values.get('confidence_score', 0.0)):.2f}")
    c3.metric("Status", "Pending review" if snapshot.next else "Completed")

    st.markdown(f"**Proposed action:** `{values.get('proposed_action', '—')}`")
    st.markdown(f"**Reasoning:** {values.get('reasoning', '—')}")

    pending_review = "execute_high_risk_action" in snapshot.next
    if pending_review:
        st.warning("Graph is interrupted before the high-risk execution node.")
        edited_action = st.text_input(
            "Edited action",
            value=str(values.get("proposed_action", "")),
            help="Edit the proposed action before resuming the graph.",
        )
        approve_col, reject_col, edit_col = st.columns(3)
        if approve_col.button("Approve", type="primary", use_container_width=True):
            _resume("approve", reviewer_id)
        if reject_col.button("Reject", use_container_width=True):
            _resume("reject", reviewer_id)
        if edit_col.button("Edit", use_container_width=True):
            if edited_action.strip():
                _resume("edit", reviewer_id, edited_action)
            else:
                st.error("Edited action cannot be empty.")
    else:
        result = values.get("execution_result") or (
            st.session_state.last_result or {}
        ).get("execution_result")
        st.success(f"Workflow completed: `{result}`")

st.divider()
st.subheader("Audit trail")
entries = load_audit_entries()
if entries:
    st.dataframe(
        [entry.model_dump(mode="json") for entry in reversed(entries)],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.caption("No audit entries yet.")
