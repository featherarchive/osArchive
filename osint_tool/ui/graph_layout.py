import math


DEFAULT_CARD_WIDTH = 180
DEFAULT_CARD_HEIGHT = 96
MIN_ZOOM = 0.35
MAX_ZOOM = 2.5


def card_center(item: dict) -> tuple[float, float]:
    width = item.get("width", DEFAULT_CARD_WIDTH)
    height = item.get("height", DEFAULT_CARD_HEIGHT)
    return (item["x"] + width / 2, item["y"] + height / 2)


def relationship_label_position(source: dict, target: dict) -> tuple[float, float]:
    source_x, source_y = card_center(source)
    target_x, target_y = card_center(target)
    return ((source_x + target_x) / 2, (source_y + target_y) / 2)


def clamp_zoom(value: float) -> float:
    return max(MIN_ZOOM, min(MAX_ZOOM, value))


def auto_arrange_positions(
    entity_ids: list[int],
    center: tuple[float, float] = (600, 400),
    radius: float | None = None,
) -> dict[int, dict[str, float]]:
    if not entity_ids:
        return {}
    radius = radius if radius is not None else max(180, len(entity_ids) * 42)
    positions = {}
    for index, entity_id in enumerate(entity_ids):
        angle = (math.tau * index) / len(entity_ids)
        positions[entity_id] = {
            "x": round(center[0] + math.cos(angle) * radius),
            "y": round(center[1] + math.sin(angle) * radius),
        }
    return positions


def radial_positions(
    source_entity_id: int,
    relationships: list[dict],
    center: tuple[float, float] = (600, 400),
    radius: float = 220,
) -> dict[int, dict[str, float]]:
    neighbors = []
    for relationship in relationships:
        source = relationship["source_entity_id"]
        target = relationship["target_entity_id"]
        if source == source_entity_id:
            neighbors.append(target)
        elif target == source_entity_id:
            neighbors.append(source)

    positions = {source_entity_id: {"x": center[0], "y": center[1]}}
    unique_neighbors = list(dict.fromkeys(neighbors))
    positions.update(auto_arrange_positions(unique_neighbors, center=center, radius=radius))
    return positions


def orbit_positions(
    entity_ids: list[int],
    main_item: dict,
    angle_offset: float,
    radius: float = 220,
    width: float = DEFAULT_CARD_WIDTH,
    height: float = DEFAULT_CARD_HEIGHT,
) -> dict[int, dict[str, float]]:
    if not entity_ids:
        return {}
    center_x, center_y = card_center(main_item)
    positions = {}
    for index, entity_id in enumerate(entity_ids):
        angle = angle_offset + (math.tau * index) / len(entity_ids)
        orbit_center_x = center_x + math.cos(angle) * radius
        orbit_center_y = center_y + math.sin(angle) * radius
        positions[entity_id] = {
            "x": round(orbit_center_x - width / 2),
            "y": round(orbit_center_y - height / 2),
        }
    return positions
