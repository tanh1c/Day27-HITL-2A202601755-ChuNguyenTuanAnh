"""Pydantic models used by the HITL workflow."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AuditDecision = Literal["approve", "reject", "edit", "auto_execute"]


class AuditEntry(BaseModel):
    """One immutable-style record describing an agent/human decision."""

    timestamp: str
    agent_id: str
    action: str
    confidence: float = Field(ge=0.0, le=1.0)
    reviewer_id: str
    decision: AuditDecision
