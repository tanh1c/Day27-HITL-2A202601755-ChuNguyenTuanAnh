from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from models import AuditEntry


def test_audit_entry_accepts_valid_data() -> None:
    entry = AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        agent_id="churn-risk-agent",
        action="increase_credit_limit",
        confidence=0.94,
        reviewer_id="operator_01",
        decision="approve",
    )

    assert entry.confidence == 0.94
    assert entry.decision == "approve"


def test_audit_entry_rejects_out_of_range_confidence() -> None:
    with pytest.raises(ValidationError):
        AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id="churn-risk-agent",
            action="send_email",
            confidence=1.2,
            reviewer_id="system",
            decision="auto_execute",
        )
