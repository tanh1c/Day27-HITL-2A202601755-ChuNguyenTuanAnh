"""CLI demonstration of auto-execute and HITL resume paths."""

from __future__ import annotations

import argparse
from uuid import uuid4

from graph import GraphState, build_graph


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Lab 27 HITL workflow")
    parser.add_argument("--churn", type=float, default=0.91)
    parser.add_argument("--toi", type=float, default=20_000_000.0)
    parser.add_argument("--decision", choices=["approve", "reject"], default="approve")
    args = parser.parse_args()

    graph = build_graph()
    config = {"configurable": {"thread_id": str(uuid4())}}
    state: GraphState = {
        "customer_id": "CLI-CUSTOMER",
        "total_operating_income": args.toi,
        "churn_probability": args.churn,
        "proposed_action": "",
        "confidence_score": 0.0,
        "reasoning": "",
        "human_decision": None,
        "reviewer_id": "",
        "execution_result": "",
    }

    result = graph.invoke(state, config)
    snapshot = graph.get_state(config)
    if "execute_high_risk_action" in snapshot.next:
        print("PENDING HUMAN REVIEW")
        print(snapshot.values)
        graph.update_state(
            config,
            {"human_decision": args.decision, "reviewer_id": "cli_reviewer"},
        )
        result = graph.invoke(None, config)

    print("FINAL STATE")
    print(result)


if __name__ == "__main__":
    main()
