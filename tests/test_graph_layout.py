from osint_tool.ui.graph_layout import (
    auto_arrange_positions,
    card_center,
    clamp_zoom,
    orbit_positions,
    radial_positions,
    relationship_label_position,
)


def test_card_center_uses_board_item_dimensions():
    item = {"x": 120, "y": 80, "width": 180, "height": 96}

    assert card_center(item) == (210, 128)


def test_card_center_uses_default_dimensions():
    item = {"x": 20, "y": 40}

    assert card_center(item) == (110, 88)


def test_clamp_zoom_keeps_scale_usable():
    assert clamp_zoom(0.1) == 0.35
    assert clamp_zoom(1.5) == 1.5
    assert clamp_zoom(4.0) == 2.5


def test_relationship_label_position_is_midpoint():
    source = {"x": 100, "y": 100, "width": 200, "height": 80}
    target = {"x": 500, "y": 300, "width": 100, "height": 120}

    assert relationship_label_position(source, target) == (375, 250)


def test_auto_arrange_positions_returns_stable_circle():
    positions = auto_arrange_positions([1, 2, 3, 4], center=(500, 400), radius=200)

    assert positions[1] == {"x": 700, "y": 400}
    assert positions[3] == {"x": 300, "y": 400}


def test_radial_positions_places_neighbors_around_source():
    relationships = [
        {"source_entity_id": 1, "target_entity_id": 2},
        {"source_entity_id": 1, "target_entity_id": 3},
        {"source_entity_id": 4, "target_entity_id": 1},
    ]

    positions = radial_positions(1, relationships, center=(400, 300), radius=160)

    assert set(positions) == {1, 2, 3, 4}
    assert positions[1] == {"x": 400, "y": 300}
    assert positions[2]["x"] > 400


def test_orbit_positions_places_related_nodes_around_main_center():
    main_item = {"x": 300, "y": 200, "width": 180, "height": 96}

    positions = orbit_positions([2, 3, 4, 5], main_item, angle_offset=0, radius=180)

    assert positions[2] == {"x": 480, "y": 200}
    assert positions[4] == {"x": 120, "y": 200}
