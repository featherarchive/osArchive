from osint_tool.ui.theme import COMMAND_THEME, STAR_POINTS, STATUS_COLORS, TYPE_COLORS


def test_command_theme_uses_command_map_palette():
    assert COMMAND_THEME["canvas"] == "#030607"
    assert COMMAND_THEME["panel"] == "#060a0b"
    assert COMMAND_THEME["accent"] == "#83df86"
    assert COMMAND_THEME["focus"] == "#f1d36d"
    assert COMMAND_THEME["danger"] == "#ff6670"


def test_entity_and_status_colors_match_command_direction():
    assert TYPE_COLORS["username"] == "#f1d36d"
    assert TYPE_COLORS["url"] == "#83df86"
    assert STATUS_COLORS["FOUND"] == ("#07180f", "#83df86")


def test_star_points_are_stable_canvas_markers():
    assert len(STAR_POINTS) >= 8
    assert STAR_POINTS[0] == (0.12, 0.18, "#f1d36d")
