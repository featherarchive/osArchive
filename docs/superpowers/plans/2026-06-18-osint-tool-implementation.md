# OSINT Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a launchable Tkinter + SQLite OSINT investigation board that stores local cases, mixed entity cards, relationships, notes, sources, board positions, lookup links, and basic technical metadata.

**Architecture:** Use a small Python package with a repository layer over SQLite, pure functions for lookup link generation and technical metadata, and a Tkinter UI split into main window, sidebar, canvas board, and inspector. Keep the board layout stored separately from entity data so persistence can be tested without GUI tests.

**Tech Stack:** Python 3.11+, Tkinter, SQLite, pytest, stdlib `urllib`, `http.client`, `socket`, `json`, and `dataclasses`.

---

## File Structure

- Create `pyproject.toml`: package metadata and pytest config.
- Create `launch.py`: development launcher for the desktop app.
- Create `osint_tool/__init__.py`: package marker.
- Create `osint_tool/__main__.py`: `python -m osint_tool` entry point.
- Create `osint_tool/app.py`: app startup and database path selection.
- Create `osint_tool/models.py`: dataclasses and entity type constants.
- Create `osint_tool/data/__init__.py`: data package marker.
- Create `osint_tool/data/db.py`: SQLite connection setup and schema migrations.
- Create `osint_tool/data/repositories.py`: case, entity, board, relationship, notes, sources, and lookup persistence.
- Create `osint_tool/lookups/__init__.py`: lookup package marker.
- Create `osint_tool/lookups/links.py`: curated public lookup link generation.
- Create `osint_tool/lookups/technical.py`: URL parsing, DNS, and HTTP metadata helpers.
- Create `osint_tool/ui/__init__.py`: UI package marker.
- Create `osint_tool/ui/main_window.py`: top-level Tkinter layout and UI orchestration.
- Create `osint_tool/ui/sidebar.py`: case list and entity creation controls.
- Create `osint_tool/ui/board.py`: canvas cards, dragging, selection, and relationship line rendering.
- Create `osint_tool/ui/inspector.py`: selected entity editor and lookup display.
- Create `tests/test_db.py`: database migration tests.
- Create `tests/test_repositories.py`: persistence tests.
- Create `tests/test_lookup_links.py`: curated link generation tests.
- Create `tests/test_technical_lookup.py`: deterministic technical helper tests.

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `launch.py`
- Create: `osint_tool/__init__.py`
- Create: `osint_tool/__main__.py`
- Create: `osint_tool/app.py`
- Create: `tests/test_imports.py`

- [ ] **Step 1: Write the failing import and entry-point tests**

Create `tests/test_imports.py`:

```python
import osint_tool
from osint_tool.app import get_default_db_path


def test_package_imports():
    assert osint_tool.__version__ == "0.1.0"


def test_default_db_path_uses_home_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = get_default_db_path()
    assert db_path == tmp_path / ".local" / "share" / "osint-tool" / "osint.sqlite3"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_imports.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'osint_tool'`.

- [ ] **Step 3: Add the package scaffold**

Create `pyproject.toml`:

```toml
[project]
name = "osint-tool"
version = "0.1.0"
description = "Local OSINT investigation board"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

Create `osint_tool/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `osint_tool/app.py`:

```python
from pathlib import Path


def get_default_db_path() -> Path:
    return Path.home() / ".local" / "share" / "osint-tool" / "osint.sqlite3"


def main() -> None:
    from osint_tool.data.db import connect
    from osint_tool.ui.main_window import MainWindow

    db_path = get_default_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect(db_path)
    window = MainWindow(connection)
    window.run()
```

Create `osint_tool/__main__.py`:

```python
from osint_tool.app import main


if __name__ == "__main__":
    main()
```

Create `launch.py`:

```python
from osint_tool.app import main


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_imports.py -v`

Expected: PASS with 2 tests.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml launch.py osint_tool/__init__.py osint_tool/__main__.py osint_tool/app.py tests/test_imports.py
git commit -m "feat: scaffold desktop app package"
```

## Task 2: Models and SQLite Schema

**Files:**
- Create: `osint_tool/models.py`
- Create: `osint_tool/data/__init__.py`
- Create: `osint_tool/data/db.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Write failing schema tests**

Create `tests/test_db.py`:

```python
from osint_tool.data.db import connect


def test_connect_creates_expected_tables(tmp_path):
    connection = connect(tmp_path / "test.sqlite3")
    table_names = {
        row[0]
        for row in connection.execute(
            "select name from sqlite_master where type = 'table'"
        )
    }
    assert {
        "schema_migrations",
        "cases",
        "entities",
        "board_items",
        "relationships",
        "notes",
        "sources",
        "attachments",
        "lookup_results",
    }.issubset(table_names)


def test_foreign_keys_are_enabled(tmp_path):
    connection = connect(tmp_path / "test.sqlite3")
    enabled = connection.execute("pragma foreign_keys").fetchone()[0]
    assert enabled == 1
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_db.py -v`

Expected: FAIL with `ModuleNotFoundError` or missing `connect`.

- [ ] **Step 3: Add models and database migration**

Create `osint_tool/models.py`:

```python
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
```

Create `osint_tool/data/__init__.py`:

```python
```

Create `osint_tool/data/db.py`:

```python
import sqlite3
from pathlib import Path


SCHEMA_VERSION = 1


SCHEMA = """
create table if not exists schema_migrations (
    version integer primary key,
    applied_at text not null
);

create table if not exists cases (
    id integer primary key autoincrement,
    name text not null,
    description text not null default '',
    created_at text not null,
    updated_at text not null
);

create table if not exists entities (
    id integer primary key autoincrement,
    case_id integer not null references cases(id) on delete cascade,
    type text not null,
    title text not null,
    description text not null default '',
    tags_json text not null default '[]',
    confidence text not null default 'unknown',
    source text not null default '',
    custom_json text not null default '{}',
    created_at text not null,
    updated_at text not null
);

create table if not exists board_items (
    entity_id integer primary key references entities(id) on delete cascade,
    x real not null,
    y real not null,
    width real not null default 180,
    height real not null default 96,
    color text not null default '#26313b',
    collapsed integer not null default 0
);

create table if not exists relationships (
    id integer primary key autoincrement,
    case_id integer not null references cases(id) on delete cascade,
    source_entity_id integer not null references entities(id) on delete cascade,
    target_entity_id integer not null references entities(id) on delete cascade,
    label text not null,
    description text not null default '',
    confidence text not null default 'unknown',
    created_at text not null,
    updated_at text not null
);

create table if not exists notes (
    id integer primary key autoincrement,
    case_id integer not null references cases(id) on delete cascade,
    entity_id integer references entities(id) on delete cascade,
    body text not null,
    created_at text not null,
    updated_at text not null
);

create table if not exists sources (
    id integer primary key autoincrement,
    case_id integer not null references cases(id) on delete cascade,
    entity_id integer references entities(id) on delete cascade,
    url text not null,
    title text not null default '',
    citation text not null default '',
    created_at text not null,
    updated_at text not null
);

create table if not exists attachments (
    id integer primary key autoincrement,
    case_id integer not null references cases(id) on delete cascade,
    entity_id integer references entities(id) on delete cascade,
    path text not null,
    sha256 text not null default '',
    available integer not null default 1,
    created_at text not null,
    updated_at text not null
);

create table if not exists lookup_results (
    id integer primary key autoincrement,
    entity_id integer not null references entities(id) on delete cascade,
    kind text not null,
    title text not null,
    url text not null default '',
    result_json text not null default '{}',
    status text not null default 'saved',
    created_at text not null
);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("pragma foreign_keys = on")
    connection.executescript(SCHEMA)
    connection.execute(
        "insert or ignore into schema_migrations(version, applied_at) values (?, datetime('now'))",
        (SCHEMA_VERSION,),
    )
    connection.commit()
    return connection
```

- [ ] **Step 4: Run the schema tests**

Run: `pytest tests/test_db.py -v`

Expected: PASS with 2 tests.

- [ ] **Step 5: Commit**

```bash
git add osint_tool/models.py osint_tool/data/__init__.py osint_tool/data/db.py tests/test_db.py
git commit -m "feat: add sqlite schema"
```

## Task 3: Repository Persistence

**Files:**
- Create: `osint_tool/data/repositories.py`
- Create: `tests/test_repositories.py`

- [ ] **Step 1: Write failing repository tests**

Create `tests/test_repositories.py`:

```python
from osint_tool.data.db import connect
from osint_tool.data.repositories import Repository


def test_case_entity_board_and_relationship_round_trip(tmp_path):
    repo = Repository(connect(tmp_path / "test.sqlite3"))
    case = repo.create_case("Alpha", "first case")
    domain = repo.create_entity(case.id, "domain", "example.com", x=120, y=80)
    person = repo.create_entity(case.id, "person", "Jane Example", x=360, y=160)
    relationship = repo.create_relationship(case.id, domain.id, person.id, "connected to")

    cases = repo.list_cases()
    entities = repo.list_entities(case.id)
    board = repo.get_board_items(case.id)
    relationships = repo.list_relationships(case.id)

    assert cases[0].name == "Alpha"
    assert [entity.title for entity in entities] == ["example.com", "Jane Example"]
    assert board[domain.id]["x"] == 120
    assert board[person.id]["y"] == 160
    assert relationships[0]["id"] == relationship["id"]
    assert relationships[0]["label"] == "connected to"


def test_notes_sources_and_lookup_results_round_trip(tmp_path):
    repo = Repository(connect(tmp_path / "test.sqlite3"))
    case = repo.create_case("Beta")
    entity = repo.create_entity(case.id, "url", "https://example.com")
    repo.add_note(case.id, entity.id, "Observed on public profile.")
    repo.add_source(case.id, entity.id, "https://example.com/source", "Example Source")
    repo.add_lookup_result(entity.id, "link", "Google", "https://google.com/search?q=example.com", {"query": "example.com"})

    assert repo.list_notes(case.id, entity.id)[0]["body"] == "Observed on public profile."
    assert repo.list_sources(case.id, entity.id)[0]["title"] == "Example Source"
    result = repo.list_lookup_results(entity.id)[0]
    assert result["title"] == "Google"
    assert result["result"]["query"] == "example.com"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_repositories.py -v`

Expected: FAIL with missing `Repository`.

- [ ] **Step 3: Implement repository methods**

Create `osint_tool/data/repositories.py`:

```python
import json
import sqlite3
from typing import Any

from osint_tool.models import Case, Entity, utc_now_iso


class Repository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create_case(self, name: str, description: str = "") -> Case:
        now = utc_now_iso()
        cursor = self.connection.execute(
            "insert into cases(name, description, created_at, updated_at) values (?, ?, ?, ?)",
            (name, description, now, now),
        )
        self.connection.commit()
        return Case(cursor.lastrowid, name, description, now, now)

    def list_cases(self) -> list[Case]:
        rows = self.connection.execute("select * from cases order by updated_at desc, id desc").fetchall()
        return [Case(row["id"], row["name"], row["description"], row["created_at"], row["updated_at"]) for row in rows]

    def create_entity(
        self,
        case_id: int,
        entity_type: str,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        confidence: str = "unknown",
        source: str = "",
        custom: dict[str, Any] | None = None,
        x: float = 100,
        y: float = 100,
    ) -> Entity:
        now = utc_now_iso()
        cursor = self.connection.execute(
            """
            insert into entities(case_id, type, title, description, tags_json, confidence, source, custom_json, created_at, updated_at)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case_id,
                entity_type,
                title,
                description,
                json.dumps(tags or []),
                confidence,
                source,
                json.dumps(custom or {}),
                now,
                now,
            ),
        )
        entity_id = cursor.lastrowid
        self.connection.execute(
            "insert into board_items(entity_id, x, y) values (?, ?, ?)",
            (entity_id, x, y),
        )
        self.connection.commit()
        return Entity(entity_id, case_id, entity_type, title, description, tags or [], confidence, source, custom or {}, now, now)

    def update_entity(self, entity_id: int, title: str, description: str, tags: list[str], confidence: str, source: str) -> None:
        self.connection.execute(
            """
            update entities
            set title = ?, description = ?, tags_json = ?, confidence = ?, source = ?, updated_at = ?
            where id = ?
            """,
            (title, description, json.dumps(tags), confidence, source, utc_now_iso(), entity_id),
        )
        self.connection.commit()

    def list_entities(self, case_id: int) -> list[Entity]:
        rows = self.connection.execute("select * from entities where case_id = ? order by id", (case_id,)).fetchall()
        return [self._entity_from_row(row) for row in rows]

    def get_entity(self, entity_id: int) -> Entity | None:
        row = self.connection.execute("select * from entities where id = ?", (entity_id,)).fetchone()
        return self._entity_from_row(row) if row else None

    def update_board_position(self, entity_id: int, x: float, y: float) -> None:
        self.connection.execute("update board_items set x = ?, y = ? where entity_id = ?", (x, y, entity_id))
        self.connection.commit()

    def get_board_items(self, case_id: int) -> dict[int, dict[str, Any]]:
        rows = self.connection.execute(
            """
            select board_items.* from board_items
            join entities on entities.id = board_items.entity_id
            where entities.case_id = ?
            """,
            (case_id,),
        ).fetchall()
        return {row["entity_id"]: dict(row) for row in rows}

    def create_relationship(self, case_id: int, source_entity_id: int, target_entity_id: int, label: str) -> dict[str, Any]:
        now = utc_now_iso()
        cursor = self.connection.execute(
            """
            insert into relationships(case_id, source_entity_id, target_entity_id, label, created_at, updated_at)
            values (?, ?, ?, ?, ?, ?)
            """,
            (case_id, source_entity_id, target_entity_id, label, now, now),
        )
        self.connection.commit()
        return {"id": cursor.lastrowid, "case_id": case_id, "source_entity_id": source_entity_id, "target_entity_id": target_entity_id, "label": label}

    def list_relationships(self, case_id: int) -> list[dict[str, Any]]:
        rows = self.connection.execute("select * from relationships where case_id = ? order by id", (case_id,)).fetchall()
        return [dict(row) for row in rows]

    def add_note(self, case_id: int, entity_id: int | None, body: str) -> None:
        now = utc_now_iso()
        self.connection.execute(
            "insert into notes(case_id, entity_id, body, created_at, updated_at) values (?, ?, ?, ?, ?)",
            (case_id, entity_id, body, now, now),
        )
        self.connection.commit()

    def list_notes(self, case_id: int, entity_id: int | None = None) -> list[dict[str, Any]]:
        if entity_id is None:
            rows = self.connection.execute("select * from notes where case_id = ? order by id", (case_id,)).fetchall()
        else:
            rows = self.connection.execute("select * from notes where case_id = ? and entity_id = ? order by id", (case_id, entity_id)).fetchall()
        return [dict(row) for row in rows]

    def add_source(self, case_id: int, entity_id: int | None, url: str, title: str = "") -> None:
        now = utc_now_iso()
        self.connection.execute(
            "insert into sources(case_id, entity_id, url, title, created_at, updated_at) values (?, ?, ?, ?, ?, ?)",
            (case_id, entity_id, url, title, now, now),
        )
        self.connection.commit()

    def list_sources(self, case_id: int, entity_id: int | None = None) -> list[dict[str, Any]]:
        if entity_id is None:
            rows = self.connection.execute("select * from sources where case_id = ? order by id", (case_id,)).fetchall()
        else:
            rows = self.connection.execute("select * from sources where case_id = ? and entity_id = ? order by id", (case_id, entity_id)).fetchall()
        return [dict(row) for row in rows]

    def add_lookup_result(self, entity_id: int, kind: str, title: str, url: str, result: dict[str, Any], status: str = "saved") -> None:
        self.connection.execute(
            "insert into lookup_results(entity_id, kind, title, url, result_json, status, created_at) values (?, ?, ?, ?, ?, ?, ?)",
            (entity_id, kind, title, url, json.dumps(result), status, utc_now_iso()),
        )
        self.connection.commit()

    def list_lookup_results(self, entity_id: int) -> list[dict[str, Any]]:
        rows = self.connection.execute("select * from lookup_results where entity_id = ? order by id", (entity_id,)).fetchall()
        results = []
        for row in rows:
            item = dict(row)
            item["result"] = json.loads(item.pop("result_json"))
            results.append(item)
        return results

    def _entity_from_row(self, row: sqlite3.Row) -> Entity:
        return Entity(
            row["id"],
            row["case_id"],
            row["type"],
            row["title"],
            row["description"],
            json.loads(row["tags_json"]),
            row["confidence"],
            row["source"],
            json.loads(row["custom_json"]),
            row["created_at"],
            row["updated_at"],
        )
```

- [ ] **Step 4: Run repository tests**

Run: `pytest tests/test_repositories.py -v`

Expected: PASS with 2 tests.

- [ ] **Step 5: Commit**

```bash
git add osint_tool/data/repositories.py tests/test_repositories.py
git commit -m "feat: add sqlite repositories"
```

## Task 4: Curated Lookup Link Generation

**Files:**
- Create: `osint_tool/lookups/__init__.py`
- Create: `osint_tool/lookups/links.py`
- Create: `tests/test_lookup_links.py`

- [ ] **Step 1: Write failing lookup link tests**

Create `tests/test_lookup_links.py`:

```python
from osint_tool.lookups.links import build_lookup_links


def labels(links):
    return {link["label"] for link in links}


def test_domain_links_include_search_and_reputation_sources():
    links = build_lookup_links("domain", "example.com")
    assert {"Google", "DuckDuckGo", "VirusTotal", "Shodan", "DNSDumpster"}.issubset(labels(links))
    assert any("example.com" in link["url"] for link in links)


def test_username_links_include_profile_pivots():
    links = build_lookup_links("username", "alice")
    assert {"Google", "DuckDuckGo", "GitHub", "Reddit", "X/Twitter", "Instagram", "TikTok"}.issubset(labels(links))
    assert {"https://github.com/alice", "https://www.instagram.com/alice"}.issubset({link["url"] for link in links})


def test_email_uses_search_only():
    links = build_lookup_links("email", "a@example.com")
    assert labels(links) == {"Google", "DuckDuckGo"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_lookup_links.py -v`

Expected: FAIL with missing `osint_tool.lookups`.

- [ ] **Step 3: Implement curated links**

Create `osint_tool/lookups/__init__.py`:

```python
```

Create `osint_tool/lookups/links.py`:

```python
from urllib.parse import quote_plus


def _search_links(value: str) -> list[dict[str, str]]:
    query = quote_plus(value)
    return [
        {"label": "Google", "url": f"https://www.google.com/search?q={query}"},
        {"label": "DuckDuckGo", "url": f"https://duckduckgo.com/?q={query}"},
    ]


def build_lookup_links(entity_type: str, value: str) -> list[dict[str, str]]:
    value = value.strip()
    links = _search_links(value)
    encoded = quote_plus(value)

    if entity_type in {"domain", "ip"}:
        links.extend(
            [
                {"label": "VirusTotal", "url": f"https://www.virustotal.com/gui/search/{encoded}"},
                {"label": "Shodan", "url": f"https://www.shodan.io/search?query={encoded}"},
                {"label": "DNSDumpster", "url": "https://dnsdumpster.com/"},
            ]
        )
    elif entity_type == "username":
        links.extend(
            [
                {"label": "GitHub", "url": f"https://github.com/{value}"},
                {"label": "Reddit", "url": f"https://www.reddit.com/user/{value}"},
                {"label": "X/Twitter", "url": f"https://x.com/search?q={encoded}"},
                {"label": "Instagram", "url": f"https://www.instagram.com/{value}"},
                {"label": "TikTok", "url": f"https://www.tiktok.com/@{value}"},
            ]
        )
    elif entity_type == "organization":
        links.append({"label": "Google Maps", "url": f"https://www.google.com/maps/search/{encoded}"})
    elif entity_type == "location":
        links.append({"label": "Google Maps", "url": f"https://www.google.com/maps/search/{encoded}"})

    return links
```

- [ ] **Step 4: Run lookup link tests**

Run: `pytest tests/test_lookup_links.py -v`

Expected: PASS with 3 tests.

- [ ] **Step 5: Commit**

```bash
git add osint_tool/lookups/__init__.py osint_tool/lookups/links.py tests/test_lookup_links.py
git commit -m "feat: add curated lookup links"
```

## Task 5: Technical Metadata Helpers

**Files:**
- Create: `osint_tool/lookups/technical.py`
- Create: `tests/test_technical_lookup.py`

- [ ] **Step 1: Write deterministic technical helper tests**

Create `tests/test_technical_lookup.py`:

```python
from osint_tool.lookups.technical import normalize_url, parse_url_metadata


def test_normalize_url_adds_scheme():
    assert normalize_url("example.com/path") == "https://example.com/path"


def test_parse_url_metadata_extracts_parts():
    metadata = parse_url_metadata("https://example.com:8443/path?q=1")
    assert metadata == {
        "normalized_url": "https://example.com:8443/path?q=1",
        "scheme": "https",
        "hostname": "example.com",
        "port": 8443,
        "path": "/path",
        "query": "q=1",
    }
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_technical_lookup.py -v`

Expected: FAIL with missing `technical`.

- [ ] **Step 3: Implement URL parsing plus safe network helpers**

Create `osint_tool/lookups/technical.py`:

```python
import http.client
import socket
from urllib.parse import urlparse


def normalize_url(value: str) -> str:
    value = value.strip()
    if "://" not in value:
        return f"https://{value}"
    return value


def parse_url_metadata(value: str) -> dict[str, str | int | None]:
    normalized = normalize_url(value)
    parsed = urlparse(normalized)
    return {
        "normalized_url": normalized,
        "scheme": parsed.scheme,
        "hostname": parsed.hostname,
        "port": parsed.port,
        "path": parsed.path or "/",
        "query": parsed.query,
    }


def resolve_dns(hostname: str) -> dict[str, list[str] | str]:
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(hostname, None)})
        return {"status": "ok", "addresses": addresses}
    except OSError as exc:
        return {"status": "error", "error": str(exc)}


def fetch_http_headers(value: str, timeout: float = 5.0) -> dict[str, object]:
    metadata = parse_url_metadata(value)
    hostname = str(metadata["hostname"] or "")
    scheme = str(metadata["scheme"])
    path = str(metadata["path"])
    if metadata["query"]:
        path = f"{path}?{metadata['query']}"
    connection_class = http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection
    try:
        connection = connection_class(hostname, metadata["port"], timeout=timeout)
        connection.request("HEAD", path)
        response = connection.getresponse()
        return {
            "status": "ok",
            "status_code": response.status,
            "reason": response.reason,
            "headers": dict(response.getheaders()),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
    finally:
        try:
            connection.close()
        except Exception:
            pass
```

- [ ] **Step 4: Run technical helper tests**

Run: `pytest tests/test_technical_lookup.py -v`

Expected: PASS with 2 tests.

- [ ] **Step 5: Commit**

```bash
git add osint_tool/lookups/technical.py tests/test_technical_lookup.py
git commit -m "feat: add technical metadata helpers"
```

## Task 6: Tkinter Main Window Skeleton

**Files:**
- Create: `osint_tool/ui/__init__.py`
- Create: `osint_tool/ui/main_window.py`
- Create: `osint_tool/ui/sidebar.py`
- Create: `osint_tool/ui/board.py`
- Create: `osint_tool/ui/inspector.py`
- Modify: `osint_tool/app.py`

- [ ] **Step 1: Add a no-display import smoke test**

Append to `tests/test_imports.py`:

```python
def test_ui_modules_import_without_creating_window():
    from osint_tool.ui.board import BoardView
    from osint_tool.ui.inspector import Inspector
    from osint_tool.ui.main_window import MainWindow
    from osint_tool.ui.sidebar import Sidebar

    assert BoardView is not None
    assert Inspector is not None
    assert MainWindow is not None
    assert Sidebar is not None
```

- [ ] **Step 2: Run the smoke test to verify it fails**

Run: `pytest tests/test_imports.py::test_ui_modules_import_without_creating_window -v`

Expected: FAIL with missing `osint_tool.ui`.

- [ ] **Step 3: Add UI module skeletons**

Create `osint_tool/ui/__init__.py`:

```python
```

Create `osint_tool/ui/sidebar.py`:

```python
import tkinter as tk
from tkinter import ttk

from osint_tool.models import ENTITY_TYPES


class Sidebar(ttk.Frame):
    def __init__(self, parent, on_case_create, on_entity_create):
        super().__init__(parent, padding=8)
        self.on_case_create = on_case_create
        self.on_entity_create = on_entity_create
        ttk.Label(self, text="Cases").pack(anchor="w")
        ttk.Button(self, text="New Case", command=self.on_case_create).pack(fill="x", pady=(4, 12))
        ttk.Label(self, text="Add Entity").pack(anchor="w")
        for entity_type in ENTITY_TYPES:
            ttk.Button(
                self,
                text=entity_type.replace("_", " ").title(),
                command=lambda value=entity_type: self.on_entity_create(value),
            ).pack(fill="x", pady=1)
```

Create `osint_tool/ui/board.py`:

```python
import tkinter as tk


TYPE_COLORS = {
    "person": "#4fb3d8",
    "username": "#8d78d8",
    "email": "#77c66e",
    "phone": "#d8904f",
    "domain": "#e6b450",
    "ip": "#da5b63",
    "url": "#5fbfaf",
    "organization": "#9aa7b2",
    "location": "#c884d8",
    "note": "#d8c56d",
    "source": "#6d8fd8",
}


class BoardView(tk.Canvas):
    def __init__(self, parent, on_select, on_move):
        super().__init__(parent, bg="#111417", highlightthickness=0)
        self.on_select = on_select
        self.on_move = on_move
        self.entities = []
        self.board_items = {}
        self.relationships = []
        self._drag_entity_id = None
        self._drag_offset = (0, 0)

    def render(self, entities, board_items, relationships):
        self.entities = entities
        self.board_items = board_items
        self.relationships = relationships
        self.delete("all")
        self._draw_grid()
        self._draw_relationships()
        for entity in entities:
            self._draw_card(entity)

    def _draw_grid(self):
        for x in range(0, 2400, 32):
            self.create_line(x, 0, x, 1600, fill="#1c232a")
        for y in range(0, 1600, 32):
            self.create_line(0, y, 2400, y, fill="#1c232a")

    def _draw_relationships(self):
        for relationship in self.relationships:
            source = self.board_items.get(relationship["source_entity_id"])
            target = self.board_items.get(relationship["target_entity_id"])
            if not source or not target:
                continue
            self.create_line(
                source["x"] + 90,
                source["y"] + 48,
                target["x"] + 90,
                target["y"] + 48,
                fill="#697887",
                width=2,
            )

    def _draw_card(self, entity):
        item = self.board_items.get(entity.id, {"x": 100, "y": 100, "width": 180, "height": 96})
        x = item["x"]
        y = item["y"]
        width = item["width"]
        height = item["height"]
        color = TYPE_COLORS.get(entity.type, "#26313b")
        tag = f"entity:{entity.id}"
        self.create_rectangle(x, y, x + width, y + height, fill="#1a2026", outline="#465564", width=2, tags=(tag,))
        self.create_rectangle(x, y, x + width, y + 24, fill=color, outline=color, tags=(tag,))
        self.create_text(x + 10, y + 12, text=entity.type.upper(), fill="#111417", anchor="w", font=("TkDefaultFont", 8, "bold"), tags=(tag,))
        self.create_text(x + 10, y + 44, text=entity.title, fill="#e8ecef", anchor="w", width=width - 20, font=("TkDefaultFont", 10, "bold"), tags=(tag,))
        self.create_text(x + 10, y + 70, text=entity.description[:60], fill="#9aa7b2", anchor="w", width=width - 20, tags=(tag,))
        self.tag_bind(tag, "<Button-1>", lambda event, entity_id=entity.id: self._start_drag(event, entity_id))
        self.tag_bind(tag, "<B1-Motion>", self._drag)
        self.tag_bind(tag, "<ButtonRelease-1>", self._end_drag)

    def _start_drag(self, event, entity_id):
        self._drag_entity_id = entity_id
        item = self.board_items[entity_id]
        self._drag_offset = (event.x - item["x"], event.y - item["y"])
        self.on_select(entity_id)

    def _drag(self, event):
        if self._drag_entity_id is None:
            return
        item = self.board_items[self._drag_entity_id]
        item["x"] = event.x - self._drag_offset[0]
        item["y"] = event.y - self._drag_offset[1]
        self.render(self.entities, self.board_items, self.relationships)

    def _end_drag(self, event):
        if self._drag_entity_id is None:
            return
        item = self.board_items[self._drag_entity_id]
        self.on_move(self._drag_entity_id, item["x"], item["y"])
        self._drag_entity_id = None
```

Create `osint_tool/ui/inspector.py`:

```python
import tkinter as tk
from tkinter import ttk
import webbrowser

from osint_tool.lookups.links import build_lookup_links


class Inspector(ttk.Frame):
    def __init__(self, parent, on_save):
        super().__init__(parent, padding=8)
        self.on_save = on_save
        self.entity = None
        ttk.Label(self, text="Inspector").pack(anchor="w")
        self.title_var = tk.StringVar()
        self.description = tk.Text(self, height=6, width=32)
        ttk.Label(self, text="Title").pack(anchor="w", pady=(12, 0))
        ttk.Entry(self, textvariable=self.title_var).pack(fill="x")
        ttk.Label(self, text="Description").pack(anchor="w", pady=(8, 0))
        self.description.pack(fill="x")
        ttk.Button(self, text="Save", command=self._save).pack(fill="x", pady=(8, 12))
        self.lookup_frame = ttk.Frame(self)
        self.lookup_frame.pack(fill="both", expand=True)

    def show_entity(self, entity):
        self.entity = entity
        self.title_var.set(entity.title)
        self.description.delete("1.0", "end")
        self.description.insert("1.0", entity.description)
        self._render_links()

    def _render_links(self):
        for child in self.lookup_frame.winfo_children():
            child.destroy()
        if not self.entity:
            return
        ttk.Label(self.lookup_frame, text="Lookup Links").pack(anchor="w")
        for link in build_lookup_links(self.entity.type, self.entity.title):
            ttk.Button(
                self.lookup_frame,
                text=link["label"],
                command=lambda url=link["url"]: webbrowser.open(url),
            ).pack(fill="x", pady=1)

    def _save(self):
        if not self.entity:
            return
        self.on_save(
            self.entity.id,
            self.title_var.get().strip(),
            self.description.get("1.0", "end").strip(),
        )
```

Create `osint_tool/ui/main_window.py`:

```python
import tkinter as tk
from tkinter import simpledialog, ttk

from osint_tool.data.repositories import Repository
from osint_tool.ui.board import BoardView
from osint_tool.ui.inspector import Inspector
from osint_tool.ui.sidebar import Sidebar


class MainWindow:
    def __init__(self, connection):
        self.root = tk.Tk()
        self.root.title("OSINT Investigation Board")
        self.root.geometry("1280x780")
        self.repo = Repository(connection)
        self.current_case = None
        self.entities = []
        self.board_items = {}
        self.relationships = []
        self._configure_style()
        self.sidebar = Sidebar(self.root, self.create_case, self.create_entity)
        self.sidebar.pack(side="left", fill="y")
        self.board = BoardView(self.root, self.select_entity, self.move_entity)
        self.board.pack(side="left", fill="both", expand=True)
        self.inspector = Inspector(self.root, self.save_entity)
        self.inspector.pack(side="right", fill="y")
        self._ensure_case()

    def run(self):
        self.root.mainloop()

    def _configure_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background="#1a2026", foreground="#e8ecef")
        style.configure("TFrame", background="#1a2026")
        style.configure("TLabel", background="#1a2026", foreground="#e8ecef")
        style.configure("TButton", background="#26313b", foreground="#e8ecef", padding=5)
        style.configure("TEntry", fieldbackground="#111417", foreground="#e8ecef")

    def _ensure_case(self):
        cases = self.repo.list_cases()
        self.current_case = cases[0] if cases else self.repo.create_case("First Case")
        self.refresh()

    def refresh(self):
        self.entities = self.repo.list_entities(self.current_case.id)
        self.board_items = self.repo.get_board_items(self.current_case.id)
        self.relationships = self.repo.list_relationships(self.current_case.id)
        self.board.render(self.entities, self.board_items, self.relationships)

    def create_case(self):
        name = simpledialog.askstring("New Case", "Case name:")
        if name:
            self.current_case = self.repo.create_case(name)
            self.refresh()

    def create_entity(self, entity_type):
        title = simpledialog.askstring("New Entity", f"{entity_type.title()} title:")
        if title:
            self.repo.create_entity(self.current_case.id, entity_type, title)
            self.refresh()

    def select_entity(self, entity_id):
        entity = self.repo.get_entity(entity_id)
        if entity:
            self.inspector.show_entity(entity)

    def move_entity(self, entity_id, x, y):
        self.repo.update_board_position(entity_id, x, y)

    def save_entity(self, entity_id, title, description):
        entity = self.repo.get_entity(entity_id)
        if entity:
            self.repo.update_entity(entity_id, title, description, entity.tags, entity.confidence, entity.source)
            self.refresh()
            self.select_entity(entity_id)
```

- [ ] **Step 4: Run the import smoke test**

Run: `pytest tests/test_imports.py::test_ui_modules_import_without_creating_window -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add osint_tool/ui tests/test_imports.py osint_tool/app.py
git commit -m "feat: add tkinter board shell"
```

## Task 7: Launch and Persistence Verification

**Files:**
- Modify: `README.md`
- Modify: `.gitignore`

- [ ] **Step 1: Add launch documentation**

Create `README.md`:

````markdown
# OSINT Investigation Board

Local desktop OSINT investigation board built with Python, Tkinter, and SQLite.

## Run

```bash
python -m osint_tool
```

or:

```bash
python launch.py
```

The app stores its default database at `~/.local/share/osint-tool/osint.sqlite3`.

## Test

```bash
pytest
```

## V1 Scope

- Local cases
- Canvas-first entity board
- Entity cards for people, usernames, emails, phones, domains, IPs, URLs, organizations, locations, notes, and sources
- Relationship storage
- Notes, sources, attachments metadata, and lookup result storage
- Curated public lookup links
- URL parsing, DNS lookup, and HTTP header/status helpers
````

- [ ] **Step 2: Run all automated tests**

Run: `pytest -v`

Expected: PASS for all tests.

- [ ] **Step 3: Launch the app manually**

Run: `python -m osint_tool`

Expected: A Tkinter window titled `OSINT Investigation Board` opens with a left sidebar, dark canvas board, and right inspector. Close it after confirming the window appears.

- [ ] **Step 4: Verify persistence manually**

Run: `python -m osint_tool`, create a domain entity named `example.com`, drag it to a new position, close the app, run `python -m osint_tool` again.

Expected: The `example.com` card appears after restart in the moved position.

- [ ] **Step 5: Commit**

```bash
git add README.md .gitignore
git commit -m "docs: add launch instructions"
```

## Self-Review Checklist

- Spec coverage: Tasks cover local launcher, Tkinter GUI, SQLite storage, canvas-first board, entity cards, relationship lines, curated lookup links, DNS/URL/HTTP helpers, and tests.
- Deferred scope: installer packaging, full graph database, cloud sync, scraping, and WHOIS are intentionally excluded from v1.
- Type consistency: repository methods use `Case`, `Entity`, integer IDs, and dictionaries consistently across tests and UI.
- Test path: persistence and lookup behavior are tested automatically; GUI is covered by import smoke tests and manual launch checks.
