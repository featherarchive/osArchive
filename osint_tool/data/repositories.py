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
        rows = self.connection.execute(
            "select * from cases order by updated_at desc, id desc"
        ).fetchall()
        return [
            Case(row["id"], row["name"], row["description"], row["created_at"], row["updated_at"])
            for row in rows
        ]

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
        return Entity(
            entity_id,
            case_id,
            entity_type,
            title,
            description,
            tags or [],
            confidence,
            source,
            custom or {},
            now,
            now,
        )

    def update_entity(
        self,
        entity_id: int,
        title: str,
        description: str,
        tags: list[str],
        confidence: str,
        source: str,
    ) -> None:
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
        rows = self.connection.execute(
            "select * from entities where case_id = ? order by id",
            (case_id,),
        ).fetchall()
        return [self._entity_from_row(row) for row in rows]

    def get_entity(self, entity_id: int) -> Entity | None:
        row = self.connection.execute(
            "select * from entities where id = ?",
            (entity_id,),
        ).fetchone()
        return self._entity_from_row(row) if row else None

    def update_board_position(self, entity_id: int, x: float, y: float) -> None:
        self.connection.execute(
            "update board_items set x = ?, y = ? where entity_id = ?",
            (x, y, entity_id),
        )
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

    def create_relationship(
        self,
        case_id: int,
        source_entity_id: int,
        target_entity_id: int,
        label: str,
    ) -> dict[str, Any]:
        now = utc_now_iso()
        cursor = self.connection.execute(
            """
            insert into relationships(case_id, source_entity_id, target_entity_id, label, created_at, updated_at)
            values (?, ?, ?, ?, ?, ?)
            """,
            (case_id, source_entity_id, target_entity_id, label, now, now),
        )
        self.connection.commit()
        return {
            "id": cursor.lastrowid,
            "case_id": case_id,
            "source_entity_id": source_entity_id,
            "target_entity_id": target_entity_id,
            "label": label,
        }

    def list_relationships(self, case_id: int) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "select * from relationships where case_id = ? order by id",
            (case_id,),
        ).fetchall()
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
            rows = self.connection.execute(
                "select * from notes where case_id = ? order by id",
                (case_id,),
            ).fetchall()
        else:
            rows = self.connection.execute(
                "select * from notes where case_id = ? and entity_id = ? order by id",
                (case_id, entity_id),
            ).fetchall()
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
            rows = self.connection.execute(
                "select * from sources where case_id = ? order by id",
                (case_id,),
            ).fetchall()
        else:
            rows = self.connection.execute(
                "select * from sources where case_id = ? and entity_id = ? order by id",
                (case_id, entity_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def add_lookup_result(
        self,
        entity_id: int,
        kind: str,
        title: str,
        url: str,
        result: dict[str, Any],
        status: str = "saved",
    ) -> None:
        self.connection.execute(
            "insert into lookup_results(entity_id, kind, title, url, result_json, status, created_at) values (?, ?, ?, ?, ?, ?, ?)",
            (entity_id, kind, title, url, json.dumps(result), status, utc_now_iso()),
        )
        self.connection.commit()

    def list_lookup_results(self, entity_id: int) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "select * from lookup_results where entity_id = ? order by id",
            (entity_id,),
        ).fetchall()
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
