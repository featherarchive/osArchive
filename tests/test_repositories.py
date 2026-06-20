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


def test_find_entity_by_case_type_and_title(tmp_path):
    repo = Repository(connect(tmp_path / "test.sqlite3"))
    case = repo.create_case("Gamma")
    entity = repo.create_entity(case.id, "username", "nettihi")

    found = repo.find_entity(case.id, "username", "nettihi")

    assert found == entity
    assert repo.find_entity(case.id, "username", "missing") is None


def test_board_collapsed_state_round_trip(tmp_path):
    repo = Repository(connect(tmp_path / "test.sqlite3"))
    case = repo.create_case("Delta")
    entity = repo.create_entity(case.id, "domain", "example.com")

    repo.set_board_collapsed(entity.id, True)
    board = repo.get_board_items(case.id)

    assert board[entity.id]["collapsed"] == 1


def test_set_main_entity_keeps_one_main_node_per_case(tmp_path):
    repo = Repository(connect(tmp_path / "test.sqlite3"))
    case = repo.create_case("Main")
    first = repo.create_entity(case.id, "username", "nettihi")
    second = repo.create_entity(case.id, "domain", "example.com")

    repo.set_main_entity(case.id, first.id)
    repo.set_main_entity(case.id, second.id)
    board = repo.get_board_items(case.id)

    assert board[first.id]["is_main"] == 0
    assert board[second.id]["is_main"] == 1
    assert repo.get_main_entity_id(case.id) == second.id


def test_list_lookup_results_for_case(tmp_path):
    repo = Repository(connect(tmp_path / "test.sqlite3"))
    case = repo.create_case("Epsilon")
    entity = repo.create_entity(case.id, "domain", "example.com")
    repo.add_lookup_result(entity.id, "transform", "DNS lookup", "", {"status": "ok"})

    results = repo.list_lookup_results_for_case(case.id)

    assert results[0]["entity_id"] == entity.id
    assert results[0]["title"] == "DNS lookup"


def test_delete_entity_removes_board_item_relationships_and_lookup_results(tmp_path):
    repo = Repository(connect(tmp_path / "test.sqlite3"))
    case = repo.create_case("Zeta")
    username = repo.create_entity(case.id, "username", "nettihi")
    profile = repo.create_entity(case.id, "url", "https://example.test/nettihi")
    repo.create_relationship(case.id, username.id, profile.id, "found profile")
    repo.add_lookup_result(username.id, "transform", "archive scan", "", {"status": "ok"})

    repo.delete_entity(username.id)

    assert repo.get_entity(username.id) is None
    assert username.id not in repo.get_board_items(case.id)
    assert repo.list_relationships(case.id) == []
    assert repo.list_lookup_results_for_case(case.id) == []


def test_delete_case_entities_clears_board_relationships_and_lookup_results(tmp_path):
    repo = Repository(connect(tmp_path / "test.sqlite3"))
    case = repo.create_case("Eta")
    username = repo.create_entity(case.id, "username", "nettihi")
    domain = repo.create_entity(case.id, "domain", "example.com")
    repo.create_relationship(case.id, username.id, domain.id, "mentions")
    repo.add_lookup_result(username.id, "transform", "archive scan", "", {"status": "ok"})

    repo.delete_case_entities(case.id)

    assert repo.list_entities(case.id) == []
    assert repo.get_board_items(case.id) == {}
    assert repo.list_relationships(case.id) == []
    assert repo.list_lookup_results_for_case(case.id) == []
