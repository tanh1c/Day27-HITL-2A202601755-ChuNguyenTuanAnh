from __future__ import annotations

import json
from pathlib import Path

from audit import append_audit_entry, load_audit_entries
from models import AuditEntry


def _entry(decision: str) -> AuditEntry:
    return AuditEntry(
        timestamp="2026-08-29T09:00:00+00:00",
        agent_id="churn-risk-agent",
        action="send_email",
        confidence=0.91,
        reviewer_id="operator_01",
        decision=decision,
    )


def test_append_audit_entry_preserves_existing_history(tmp_path: Path) -> None:
    path = tmp_path / "audit_log.json"
    append_audit_entry(_entry("approve"), path)
    append_audit_entry(_entry("reject"), path)

    entries = load_audit_entries(path)
    raw = json.loads(path.read_text(encoding="utf-8"))

    assert [entry.decision for entry in entries] == ["approve", "reject"]
    assert len(raw) == 2


def test_load_audit_entries_returns_empty_for_missing_file(tmp_path: Path) -> None:
    assert load_audit_entries(tmp_path / "missing.json") == []


def test_load_audit_entries_rejects_non_array_json(tmp_path: Path) -> None:
    path = tmp_path / "audit.json"
    path.write_text('{"decision": "approve"}', encoding="utf-8")

    try:
        load_audit_entries(path)
    except ValueError as exc:
        assert "JSON array" in str(exc)
    else:
        raise AssertionError("expected ValueError for non-array audit log")
