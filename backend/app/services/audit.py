import enum
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def _serialize(data: Any) -> dict | list | None:
    if data is None:
        return None
    if hasattr(data, "model_dump"):
        return _json_safe(data.model_dump(mode="json"))
    if isinstance(data, dict):
        return _json_safe(data)
    return json.loads(json.dumps(data, default=str))


async def log_audit(
    db: AsyncSession,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int,
    old_data: Any = None,
    new_data: Any = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_data=_serialize(old_data),
        new_data=_serialize(new_data),
    )
    db.add(entry)
    return entry
