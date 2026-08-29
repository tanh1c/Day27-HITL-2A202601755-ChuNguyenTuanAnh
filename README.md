# Lab 27 — Agent Human-in-the-Loop (HITL)

## Student information

- **Họ và tên:** Chu Nguyễn Tuấn Anh
- **MSSV:** 2A202601755
- **Bài:** Lab 27 — Xây dựng hệ thống Agent Human-in-the-Loop (HITL)

A deterministic LangGraph workflow for churn-risk evaluation with confidence routing, hard policy rules, human approval in Streamlit, checkpointed state, and an append-preserving audit trail.

## What is implemented

- `GraphState` (`TypedDict`) persists `customer_id`, `proposed_action`, `confidence_score`, `reasoning`, and `human_decision` across the graph.
- `AuditEntry` (`Pydantic BaseModel`) records `timestamp`, `agent_id`, `action`, `confidence`, `reviewer_id`, and `decision`.
- `evaluate_customer(state)` returns the proposed action, confidence score, and reasoning from mock churn/TOI inputs.
- `route_action(state)` applies the hard policy **before** the confidence threshold.
- `MemorySaver()` checkpoints state.
- `interrupt_before=["execute_high_risk_action"]` pauses before high-risk execution.
- Streamlit exposes **Approve**, **Reject**, and **Edit** controls and resumes the same `thread_id`.
- `audit_log.json` preserves decision history; writes use a temporary file + atomic replace.
- Pytest covers policy override, auto-execute, escalation, interrupt persistence, approve/reject/edit, and audit history.
- GitHub Actions runs lint, mypy, pytest + branch coverage, syntax compilation, and a Streamlit health check.

## Routing policy

| Condition | Route | Result |
|---|---|---|
| `proposed_action == increase_credit_limit` (including edited payload form) | high risk | Human review, regardless of confidence |
| low-risk action and `confidence_score >= 0.85` | low risk | Auto-execute |
| any action below `0.85` | high risk | Human review |

**Confidence threshold:** `0.85`.

The hard rule is intentionally evaluated first, so `increase_credit_limit` at `0.99` confidence still cannot bypass review.

## Project structure

```text
.
├── app.py                    # Streamlit approval UI + resume logic
├── graph.py                  # GraphState, nodes, routing, graph compilation
├── models.py                 # AuditEntry schema
├── audit.py                  # Append-preserving audit storage
├── demo.py                   # CLI workflow demo
├── audit_log.json            # Local audit trail
├── tests/                    # Unit + HITL integration tests
├── REFLECTION.md             # Answers to the three lab reflection questions
├── RUBRIC_CHECKLIST.md       # Requirement-to-evidence mapping
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── Makefile
└── .github/workflows/ci.yml
```

## Install

Python 3.10+ is required.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

For development/verification:

```bash
python -m pip install -r requirements-dev.txt
```

No API key is required. The lab allows mock agent output, so the reasoning node is deterministic and CI does not need secrets.

## Run the LangGraph workflow

High-risk example (pauses, then the CLI applies a human decision and resumes):

```bash
python demo.py --churn 0.91 --toi 20000000 --decision approve
```

Low-risk auto-execute example:

```bash
python demo.py --churn 0.15 --toi 50000000
```

## Run the Streamlit approval UI

```bash
streamlit run app.py
```

1. Enter customer ID, TOI, churn probability, and reviewer ID.
2. Click **Start evaluation**.
3. A safe/high-confidence `send_email` completes automatically.
4. A high-risk or low-confidence path remains pending before `execute_high_risk_action`.
5. Choose **Approve**, **Reject**, or edit the action and choose **Edit**.
6. The UI calls `graph.update_state(...)` and then `graph.invoke(None, config)` using the same `thread_id`.
7. Review the appended record in the **Audit trail** table or `audit_log.json`.

## Audit semantics

- `approve` → action executes and is logged with the reviewer ID.
- `reject` → action is aborted and the rejection is logged.
- `edit` → the edited action executes after human authorization and is logged.
- `auto_execute` → allowed low-risk action is logged with reviewer `system`.

`audit_log.json` starts as an empty JSON array. Tests redirect audit output to temporary files through `AUDIT_LOG_PATH`, so test runs never pollute the submitted audit file.

## Verification

Run everything locally:

```bash
make check
```

Equivalent commands:

```bash
ruff check .
mypy
python -m pytest --cov --cov-report=term-missing --cov-report=xml
python -m compileall -q app.py audit.py demo.py graph.py models.py
```

Coverage is configured to fail below **90% branch-aware coverage** for the core `audit`, `graph`, and `models` modules.

## GitHub Actions / CI policy

CI is intentionally configured for:

- `pull_request` targeting `main` (only when code/config paths change), and
- manual `workflow_dispatch`.

There is **no push trigger**, which avoids duplicate runs when a PR is merged. Concurrency also cancels superseded runs for the same PR.

The CI artifact `lab27-ci-evidence` contains JUnit output, pytest console output, Streamlit startup logs, and `coverage.xml`.

## Security

Do not commit API keys, access tokens, passwords, private keys, or a real `.env`. `.gitignore` excludes `.env`/`*.env`, and this project does not require credentials.
