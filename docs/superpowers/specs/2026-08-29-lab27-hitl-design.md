# Lab 27 HITL Design

## Goal

Implement the lab-required LangGraph Human-in-the-Loop workflow in a submission-ready repository without external API credentials.

## Architecture

`evaluate_customer` deterministically converts TOI + churn probability into an action, confidence, and reasoning. `route_action` applies a hard credit-limit policy first, then the 0.85 confidence threshold. Low-risk work executes immediately; high-risk/low-confidence work targets `execute_high_risk_action`, where the compiled graph pauses via `interrupt_before` and `MemorySaver` preserves the thread state. Streamlit reviews that state, writes a human decision with `update_state`, and resumes with `invoke(None, config)`.

Audit storage is isolated in `audit.py`. Every final path writes a Pydantic-validated `AuditEntry`; human-reviewed paths include the reviewer and decision, while low-risk auto-execution uses reviewer `system`.

## Safety and reliability

- Hard policy cannot be bypassed by high confidence.
- High-risk execution refuses to run without an explicit human decision even if called directly.
- Audit history is append-preserving and atomically replaced.
- No API key is needed or committed.
- CI runs only on PR/manual dispatch to avoid duplicate push+PR runs.

## Testing

Tests cover evaluator validation, all routing branches, checkpoint persistence, no pre-review execution, Approve/Reject/Edit resume semantics, auto-execution, audit preservation, and Pydantic bounds. CI adds lint, strict type checking, branch coverage >=90%, syntax compilation, and Streamlit health smoke testing.
