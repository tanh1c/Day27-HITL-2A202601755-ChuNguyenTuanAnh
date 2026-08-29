from __future__ import annotations

import json
from pathlib import Path

from graph import build_graph


def _config(thread_id: str) -> dict[str, dict[str, str]]:
    return {"configurable": {"thread_id": thread_id}}


def _high_risk_input() -> dict[str, object]:
    return {
        "customer_id": "CUST-HIGH",
        "total_operating_income": 20_000_000.0,
        "churn_probability": 0.95,
        "proposed_action": "",
        "confidence_score": 0.0,
        "reasoning": "",
        "human_decision": None,
        "reviewer_id": "",
        "execution_result": "",
    }


def _low_risk_input() -> dict[str, object]:
    return {
        "customer_id": "CUST-LOW",
        "total_operating_income": 50_000_000.0,
        "churn_probability": 0.15,
        "proposed_action": "",
        "confidence_score": 0.0,
        "reasoning": "",
        "human_decision": None,
        "reviewer_id": "",
        "execution_result": "",
    }


def test_high_risk_graph_interrupts_before_execution_and_preserves_state(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("AUDIT_LOG_PATH", str(tmp_path / "audit.json"))
    graph = build_graph()
    config = _config("interrupt-test")

    graph.invoke(_high_risk_input(), config)
    snapshot = graph.get_state(config)

    assert snapshot.next == ("execute_high_risk_action",)
    assert snapshot.values["customer_id"] == "CUST-HIGH"
    assert snapshot.values["execution_result"] == ""
    assert not (tmp_path / "audit.json").exists()


def test_approve_resumes_and_executes_high_risk_action(tmp_path: Path, monkeypatch) -> None:
    audit_path = tmp_path / "audit.json"
    monkeypatch.setenv("AUDIT_LOG_PATH", str(audit_path))
    graph = build_graph()
    config = _config("approve-test")

    graph.invoke(_high_risk_input(), config)
    graph.update_state(
        config,
        {"human_decision": "approve", "reviewer_id": "operator_01"},
    )
    final = graph.invoke(None, config)

    assert final["execution_result"] == "executed:increase_credit_limit"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit[-1]["decision"] == "approve"


def test_reject_resumes_and_aborts_high_risk_action(tmp_path: Path, monkeypatch) -> None:
    audit_path = tmp_path / "audit.json"
    monkeypatch.setenv("AUDIT_LOG_PATH", str(audit_path))
    graph = build_graph()
    config = _config("reject-test")

    graph.invoke(_high_risk_input(), config)
    graph.update_state(
        config,
        {"human_decision": "reject", "reviewer_id": "operator_02"},
    )
    final = graph.invoke(None, config)

    assert final["execution_result"] == "aborted:increase_credit_limit"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit[-1]["decision"] == "reject"


def test_edit_updates_action_then_resumes(tmp_path: Path, monkeypatch) -> None:
    audit_path = tmp_path / "audit.json"
    monkeypatch.setenv("AUDIT_LOG_PATH", str(audit_path))
    graph = build_graph()
    config = _config("edit-test")

    graph.invoke(_high_risk_input(), config)
    graph.update_state(
        config,
        {
            "human_decision": "edit",
            "reviewer_id": "operator_03",
            "proposed_action": "increase_credit_limit:20000000",
        },
    )
    final = graph.invoke(None, config)

    assert final["execution_result"] == "executed:increase_credit_limit:20000000"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit[-1]["decision"] == "edit"
    assert audit[-1]["action"] == "increase_credit_limit:20000000"


def test_low_risk_action_auto_executes_without_interrupt(tmp_path: Path, monkeypatch) -> None:
    audit_path = tmp_path / "audit.json"
    monkeypatch.setenv("AUDIT_LOG_PATH", str(audit_path))
    graph = build_graph()
    config = _config("low-risk-test")

    final = graph.invoke(_low_risk_input(), config)
    snapshot = graph.get_state(config)

    assert snapshot.next == ()
    assert final["execution_result"] == "executed:send_email"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit[-1]["decision"] == "auto_execute"
    assert audit[-1]["reviewer_id"] == "system"
