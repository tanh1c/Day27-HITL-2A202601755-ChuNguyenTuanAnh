"""Append-preserving JSON audit trail helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from models import AuditEntry

DEFAULT_AUDIT_LOG = Path("audit_log.json")


def resolve_audit_path(path: str | Path | None = None) -> Path:
    """Resolve an explicit path, then AUDIT_LOG_PATH, then the repo default."""

    if path is not None:
        return Path(path)
    return Path(os.environ.get("AUDIT_LOG_PATH", str(DEFAULT_AUDIT_LOG)))


def load_audit_entries(path: str | Path | None = None) -> list[AuditEntry]:
    """Load the complete audit history without mutating it."""

    audit_path = resolve_audit_path(path)
    if not audit_path.exists():
        return []

    raw = json.loads(audit_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("audit log must contain a JSON array")
    return [AuditEntry.model_validate(item) for item in raw]


def append_audit_entry(entry: AuditEntry, path: str | Path | None = None) -> None:
    """Append an entry while preserving all previous records.

    A temporary file + atomic replace prevents a partially-written JSON file if
    the process is interrupted during the write.
    """

    audit_path = resolve_audit_path(path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    entries = load_audit_entries(audit_path)
    entries.append(entry)
    payload = [item.model_dump(mode="json") for item in entries]

    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=audit_path.parent,
        prefix=f".{audit_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temp_path = Path(handle.name)

    temp_path.replace(audit_path)
