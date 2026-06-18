from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


ENTITY_TYPES = (
    "person",
    "username",
    "email",
    "phone",
    "domain",
    "ip",
    "url",
    "organization",
    "location",
    "note",
    "source",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Case:
    id: int | None
    name: str
    description: str = ""
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class Entity:
    id: int | None
    case_id: int
    type: str
    title: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    confidence: str = "unknown"
    source: str = ""
    custom: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
