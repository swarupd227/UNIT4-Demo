"""Append-only audit trail. Each event hashes the one before it, so a change is detectable."""

import hashlib
import json
from datetime import datetime
from typing import Any

from sqlalchemy import Connection, text

GENESIS = "0" * 64


def event_hash(
    prev_hash: str, at: datetime, actor: str, role: str, action: str, item_id: str, detail: Any
) -> str:
    body = json.dumps(
        {
            "prev": prev_hash,
            "at": at.isoformat(),
            "actor": actor,
            "role": role,
            "action": action,
            "item": item_id,
            "detail": detail,
        },
        sort_keys=True,
    )
    return hashlib.sha256(body.encode()).hexdigest()


def record(
    db: Connection, at: datetime, actor: str, role: str, action: str, item_id: str, detail: dict[str, Any]
) -> None:
    db.execute(text("LOCK TABLE studio.audit_event IN SHARE ROW EXCLUSIVE MODE"))
    prev = db.execute(text("SELECT hash FROM studio.audit_event ORDER BY seq DESC LIMIT 1")).scalar()
    prev_hash = prev or GENESIS
    db.execute(
        text("""
            INSERT INTO studio.audit_event (at, actor, role, action, item_id, detail, prev_hash, hash)
            VALUES (:at, :actor, :role, :action, :item_id, CAST(:detail AS jsonb), :prev_hash, :hash)
        """),
        {
            "at": at,
            "actor": actor,
            "role": role,
            "action": action,
            "item_id": item_id,
            "detail": json.dumps(detail, sort_keys=True),
            "prev_hash": prev_hash,
            "hash": event_hash(prev_hash, at, actor, role, action, item_id, detail),
        },
    )


def verify_chain(db: Connection) -> bool:
    prev_hash = GENESIS
    rows = db.execute(
        text("""
            SELECT at, actor, role, action, item_id, detail, prev_hash, hash
            FROM studio.audit_event ORDER BY seq
        """)
    ).mappings()
    for row in rows:
        expected = event_hash(
            prev_hash, row["at"], row["actor"], row["role"], row["action"], row["item_id"], row["detail"]
        )
        if row["prev_hash"] != prev_hash or row["hash"] != expected:
            return False
        prev_hash = row["hash"]
    return True
