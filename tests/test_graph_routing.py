from __future__ import annotations

import pytest

from graph import (
    CONFIDENCE_THRESHOLD,
    evaluate_customer,
    route_action,
)


def _state(action: str, confidence: float) -> dict[str, object]:
    return {
        "customer_id": "CUST001",
        "proposed_action": action,
        "confidence_score": confidence,
        "reasoning": "test",
        "human_decision": None,
    }


def test_hard_rule_overrides_even_very_high_confidence() -> None:
    assert route_action(_state("increase_credit_limit", 0.99)) == "high_risk"


def test_low_risk_high_confidence_auto_executes() -> None:
    assert route_action(_state("send_email", CONFIDENCE_THRESHOLD)) == "low_risk"


def test_low_risk_below_threshold_escalates() -> None:
    assert route_action(_state("send_email", CONFIDENCE_THRESHOLD - 0.01)) == "high_risk"


def test_evaluate_customer_returns_required_agent_fields() -> None:
    result = evaluate_customer(
        {
            "customer_id": "CUST001",
            "total_operating_income": 12_000_000.0,
            "churn_probability": 0.91,
            "proposed_action": "",
            "confidence_score": 0.0,
            "reasoning": "",
            "human_decision": None,
        }
    )

    assert result["proposed_action"] == "increase_credit_limit"
    assert 0.0 <= result["confidence_score"] <= 1.0
    assert result["reasoning"]


def test_evaluate_customer_rejects_invalid_churn_probability() -> None:
    with pytest.raises(ValueError, match="churn_probability"):
        evaluate_customer(
            {
                "customer_id": "CUST001",
                "total_operating_income": 12_000_000.0,
                "churn_probability": 1.4,
                "proposed_action": "",
                "confidence_score": 0.0,
                "reasoning": "",
                "human_decision": None,
            }
        )


def test_edited_credit_limit_action_still_matches_hard_rule() -> None:
    assert route_action(_state("increase_credit_limit:20000000", 0.99)) == "high_risk"


def test_evaluate_customer_moderate_churn_escalates_by_confidence() -> None:
    result = evaluate_customer(
        {
            "customer_id": "CUST-MID",
            "total_operating_income": 10_000_000.0,
            "churn_probability": 0.55,
            "proposed_action": "",
            "confidence_score": 0.0,
            "reasoning": "",
            "human_decision": None,
        }
    )

    assert result["proposed_action"] == "send_email"
    assert result["confidence_score"] < CONFIDENCE_THRESHOLD


def test_evaluate_customer_rejects_negative_toi() -> None:
    with pytest.raises(ValueError, match="total_operating_income"):
        evaluate_customer(
            {
                "customer_id": "CUST001",
                "total_operating_income": -1.0,
                "churn_probability": 0.5,
                "proposed_action": "",
                "confidence_score": 0.0,
                "reasoning": "",
                "human_decision": None,
            }
        )
