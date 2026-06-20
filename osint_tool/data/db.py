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
    collapsed integer not null default 0,
    is_main integer not null default 0
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


def _ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {
        row["name"]
        for row in connection.execute(f"pragma table_info({table})").fetchall()
    }
    if column not in columns:
        connection.execute(f"alter table {table} add column {column} {definition}")


def connect(path: str | Path) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("pragma foreign_keys = on")
    connection.executescript(SCHEMA)
    _ensure_column(connection, "board_items", "is_main", "integer not null default 0")
    connection.execute(
        "insert or ignore into schema_migrations(version, applied_at) values (?, datetime('now'))",
        (SCHEMA_VERSION,),
    )
    connection.commit()
    return connection
