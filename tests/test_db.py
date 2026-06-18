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
