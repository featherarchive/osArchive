from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TransformNode:
    type: str
    title: str
    value: str
    description: str = ""
    status: str = "found"
    source: str = ""
    relationship: str = "found"
    custom: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TransformRun:
    name: str
    status: str
    nodes: list[TransformNode] = field(default_factory=list)
    message: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
