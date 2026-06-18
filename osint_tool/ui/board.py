from osint_tool.ui.tkcompat import tk


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
