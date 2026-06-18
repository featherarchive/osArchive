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
