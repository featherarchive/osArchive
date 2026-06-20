import ipaddress
import re
from dataclasses import dataclass

from osint_tool.models import ENTITY_TYPES


@dataclass(frozen=True)
class ImportedTarget:
    type: str
    title: str


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DOMAIN_RE = re.compile(r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$")


def parse_target_lines(text: str) -> list[ImportedTarget]:
    targets = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        target = _parse_line(line)
        if target:
            targets.append(target)
    return targets


def _parse_line(line: str) -> ImportedTarget | None:
    for separator in (":", ","):
        if separator in line:
            left, right = line.split(separator, 1)
            entity_type = left.strip().lower().replace(" ", "_")
            title = right.strip()
            if entity_type in ENTITY_TYPES and title:
                return ImportedTarget(entity_type, title)
            if separator == ",":
                return None
    inferred = _infer_type(line)
    return ImportedTarget(inferred, line) if inferred else None


def _infer_type(value: str) -> str | None:
    lowered = value.lower()
    if lowered.startswith(("http://", "https://")):
        return "url"
    if EMAIL_RE.match(value):
        return "email"
    try:
        ipaddress.ip_address(value)
        return "ip"
    except ValueError:
        pass
    if DOMAIN_RE.match(value):
        return "domain"
    return None
