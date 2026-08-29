# Lab 27 Rubric / Evidence Checklist

| Lab requirement | Implementation evidence | Automated evidence |
|---|---|---|
| `GraphState` has required five fields | `graph.py::GraphState` | graph integration tests preserve state across interrupt |
| `AuditEntry` has six required fields | `models.py::AuditEntry` | `tests/test_models.py` |
| `evaluate_customer(state)` returns action/confidence/reasoning | `graph.py` | routing tests cover high/moderate/low and invalid inputs |
| Confidence in `[0, 1]` | deterministic evaluator + Pydantic audit constraint | model/routing tests |
| Hard rule overrides confidence | `route_action()` checks credit-limit action first | test at confidence `0.99` |
| Low-risk `>= 0.85` auto-executes | `route_action()` | threshold + graph auto-execute tests |
| `< 0.85` escalates | `route_action()` | moderate churn / low confidence tests |
| `MemorySaver()` | `build_graph()` | HITL state persistence test |
| `interrupt_before=["execute_high_risk_action"]` | `build_graph()` | verifies pending `snapshot.next` and no audit/execution before review |
| Streamlit shows action/confidence/reasoning | `app.py` | CI Streamlit health smoke test |
| Approve | `app.py::_resume()` + high-risk node | integration test |
| Reject | `app.py::_resume()` + high-risk node | integration test |
| Edit | UI updates `proposed_action` + resumes | integration test confirms edited action in audit |
| Resume same graph/thread | `graph.update_state()` then `graph.invoke(None, config)` | approve/reject/edit integration tests |
| Audit append, no overwrite | `audit.py::append_audit_entry()` | append-history test |
| README install/run/policy/UI/audit instructions | `README.md` | documentation review |
| No real secrets | deterministic mock reasoning + `.gitignore` | no secret needed by CI |

## Bonus-quality evidence

- Branch-aware coverage gate (`>= 90%`) on core modules.
- Ruff + strict mypy + syntax compilation.
- Streamlit HTTP health smoke test in CI.
- CI evidence artifact with JUnit, pytest output, coverage XML, and Streamlit log.
- Atomic audit-file replacement to reduce corruption risk.
- `REFLECTION.md` answers all three reflection questions.
- CI only runs on PR/manual dispatch, with concurrency cancellation, to avoid duplicate/spam runs.
