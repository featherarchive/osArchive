from osint_tool.ui.graph_layout import card_center, clamp_zoom, relationship_label_position
from osint_tool.ui.theme import COMMAND_THEME, STAR_POINTS, STATUS_COLORS, TYPE_COLORS
from osint_tool.ui.tkcompat import tk


DEFAULT_ITEM = {"x": 100, "y": 100, "width": 180, "height": 96}
GRID_STEP = 32


class BoardView(tk.Canvas):
    def __init__(self, parent, on_select, on_move, on_context_menu=None):
        super().__init__(parent, bg=COMMAND_THEME["canvas"], highlightthickness=0)
        self.on_select = on_select
        self.on_move = on_move
        self.on_context_menu = on_context_menu
        self.entities = []
        self.board_items = {}
        self.relationships = []
        self.selected_entity_id = None
        self.relationship_source_id = None
        self._drag_entity_id = None
        self._drag_offset = (0, 0)
        self._zoom = 1.0
        self._pan = (0.0, 0.0)
        self._pan_start = None

        self.bind("<MouseWheel>", self._zoom_wheel)
        self.bind("<Button-4>", self._zoom_wheel)
        self.bind("<Button-5>", self._zoom_wheel)
        self.bind("<ButtonPress-2>", self._start_pan)
        self.bind("<B2-Motion>", self._pan_motion)
        self.bind("<ButtonRelease-2>", self._end_pan)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<ButtonRelease-1>", self._end_drag)

    def render(
        self,
        entities,
        board_items,
        relationships,
        selected_entity_id=None,
        relationship_source_id=None,
    ):
        self.entities = entities
        self.board_items = {entity_id: dict(item) for entity_id, item in board_items.items()}
        self.relationships = relationships
        self.selected_entity_id = selected_entity_id
        self.relationship_source_id = relationship_source_id
        self.hidden_entity_ids = self._hidden_entity_ids()
        self.delete("all")
        self._draw_grid()
        self._draw_stars()
        self._draw_relationships()
        for entity in entities:
            if entity.id in self.hidden_entity_ids:
                continue
            self._draw_card(entity)

    def _draw_grid(self):
        width = max(self.winfo_width(), 1)
        height = max(self.winfo_height(), 1)
        step = self._scale(GRID_STEP)
        if step < 12:
            step = self._scale(GRID_STEP * 2)

        offset_x = self._pan[0] % step
        offset_y = self._pan[1] % step
        x = offset_x
        while x < width:
            fill = COMMAND_THEME["grid"] if int((x - offset_x) / step) % 4 else COMMAND_THEME["grid_major"]
            self.create_line(x, 0, x, height, fill=fill)
            x += step

        y = offset_y
        while y < height:
            fill = COMMAND_THEME["grid"] if int((y - offset_y) / step) % 4 else COMMAND_THEME["grid_major"]
            self.create_line(0, y, width, y, fill=fill)
            y += step

    def _draw_stars(self):
        width = max(self.winfo_width(), 1)
        height = max(self.winfo_height(), 1)
        for index, (x_ratio, y_ratio, color) in enumerate(STAR_POINTS):
            x = x_ratio * width + (self._pan[0] * 0.03)
            y = y_ratio * height + (self._pan[1] * 0.03)
            radius = max(1, int(self._scale(1 if index % 3 else 2)))
            self.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                fill=color,
                outline="",
            )

    def _draw_relationships(self):
        for relationship in self.relationships:
            source = self.board_items.get(relationship["source_entity_id"])
            target = self.board_items.get(relationship["target_entity_id"])
            if not source or not target:
                continue
            if relationship["source_entity_id"] in self.hidden_entity_ids or relationship["target_entity_id"] in self.hidden_entity_ids:
                continue

            source_x, source_y = self._to_screen(*card_center(source))
            target_x, target_y = self._to_screen(*card_center(target))
            label_x, label_y = self._to_screen(*relationship_label_position(source, target))

            self.create_line(
                source_x,
                source_y,
                target_x,
                target_y,
                fill=COMMAND_THEME["accent"],
                width=max(1, int(self._scale(2))),
                arrow=tk.LAST,
                arrowshape=(
                    max(8, int(self._scale(12))),
                    max(10, int(self._scale(15))),
                    max(4, int(self._scale(5))),
                ),
            )
            label = relationship.get("label", "")
            if label:
                text_id = self.create_text(
                    label_x,
                    label_y,
                    text=label,
                    fill=COMMAND_THEME["text"],
                    font=("TkDefaultFont", max(7, int(self._scale(9))), "bold"),
                )
                bbox = self.bbox(text_id)
                if bbox:
                    pad_x = max(5, int(self._scale(7)))
                    pad_y = max(3, int(self._scale(4)))
                    bg_id = self.create_rectangle(
                        bbox[0] - pad_x,
                        bbox[1] - pad_y,
                        bbox[2] + pad_x,
                        bbox[3] + pad_y,
                        fill=COMMAND_THEME["panel"],
                        outline=COMMAND_THEME["border"],
                    )
                    self.tag_lower(bg_id, text_id)

    def _draw_card(self, entity):
        item = self._item_for(entity.id)
        x, y = self._to_screen(item["x"], item["y"])
        width = self._scale(item["width"])
        height = self._scale(item["height"])
        color = TYPE_COLORS.get(entity.type, "#9aa7b2")
        tag = f"entity:{entity.id}"
        is_selected = entity.id == self.selected_entity_id
        is_source = entity.id == self.relationship_source_id
        is_main = int(item.get("is_main", 0)) == 1
        outline = (
            COMMAND_THEME["focus"]
            if is_source
            else COMMAND_THEME["selection"]
            if is_selected
            else COMMAND_THEME["border"]
        )
        outline_width = max(2, int(self._scale(3 if is_selected or is_source else 2)))
        header_height = self._scale(24)

        if is_main:
            self.create_rectangle(
                x - self._scale(9),
                y - self._scale(9),
                x + width + self._scale(9),
                y + height + self._scale(9),
                outline=COMMAND_THEME["focus"],
                width=max(2, int(self._scale(4))),
                tags=(tag,),
            )

        if is_source:
            self.create_rectangle(
                x - self._scale(6),
                y - self._scale(6),
                x + width + self._scale(6),
                y + height + self._scale(6),
                outline=COMMAND_THEME["focus"],
                width=max(1, int(self._scale(1))),
                dash=(5, 4),
            )

        self.create_rectangle(
            x,
            y,
            x + width,
            y + height,
            fill=COMMAND_THEME["panel_alt"],
            outline=outline,
            width=outline_width,
            tags=(tag,),
        )
        self.create_rectangle(
            x,
            y,
            x + width,
            y + header_height,
            fill=color,
            outline=color,
            tags=(tag,),
        )
        self.create_oval(
            x + self._scale(9),
            y + self._scale(34),
            x + self._scale(29),
            y + self._scale(54),
            fill=color,
            outline=COMMAND_THEME["canvas"],
            width=max(1, int(self._scale(2))),
            tags=(tag,),
        )
        self.create_text(
            x + self._scale(10),
            y + self._scale(12),
            text=entity.type.upper(),
            fill=COMMAND_THEME["canvas"],
            anchor="w",
            font=("TkDefaultFont", max(7, int(self._scale(8))), "bold"),
            tags=(tag,),
        )
        self.create_text(
            x + self._scale(38),
            y + self._scale(43),
            text=entity.title,
            fill=COMMAND_THEME["text"],
            anchor="w",
            width=max(40, int(width - self._scale(48))),
            font=("TkDefaultFont", max(8, int(self._scale(10))), "bold"),
            tags=(tag,),
        )
        self.create_text(
            x + self._scale(10),
            y + self._scale(72),
            text=entity.description[:80],
            fill=COMMAND_THEME["muted"],
            anchor="w",
            width=max(40, int(width - self._scale(20))),
            font=("TkDefaultFont", max(7, int(self._scale(9)))),
            tags=(tag,),
        )
        self._draw_status_badge(entity, x, y, width)
        self.tag_bind(tag, "<Button-1>", lambda event, entity_id=entity.id: self._start_drag(event, entity_id))
        self.tag_bind(tag, "<B1-Motion>", self._drag)
        self.tag_bind(tag, "<ButtonRelease-1>", self._end_drag)
        self.tag_bind(tag, "<Button-3>", lambda event, entity_id=entity.id: self._show_context_menu(event, entity_id))

    def _item_for(self, entity_id):
        if entity_id not in self.board_items:
            self.board_items[entity_id] = dict(DEFAULT_ITEM)
        item = self.board_items[entity_id]
        item.setdefault("width", DEFAULT_ITEM["width"])
        item.setdefault("height", DEFAULT_ITEM["height"])
        return item

    def _draw_status_badge(self, entity, x, y, width):
        status = entity.custom.get("status") if getattr(entity, "custom", None) else None
        if not status:
            return
        label = str(status).upper()
        fill, text = STATUS_COLORS.get(label, (COMMAND_THEME["panel_raised"], COMMAND_THEME["muted"]))
        badge_width = max(self._scale(52), self._scale(len(label) * 7))
        badge_height = self._scale(16)
        left = x + width - badge_width - self._scale(8)
        top = y + self._scale(4)
        self.create_rectangle(left, top, left + badge_width, top + badge_height, fill=fill, outline=text)
        self.create_text(
            left + badge_width / 2,
            top + badge_height / 2,
            text=label,
            fill=text,
            font=("TkDefaultFont", max(6, int(self._scale(7))), "bold"),
        )

    def _hidden_entity_ids(self):
        hidden = set()
        collapsed_sources = {
            entity_id for entity_id, item in self.board_items.items() if int(item.get("collapsed", 0)) == 1
        }
        for relationship in self.relationships:
            if relationship["source_entity_id"] in collapsed_sources:
                hidden.add(relationship["target_entity_id"])
        return hidden

    def _start_drag(self, event, entity_id):
        self._drag_entity_id = entity_id
        item = self._item_for(entity_id)
        world_x, world_y = self._to_world(event.x, event.y)
        self._drag_offset = (world_x - item["x"], world_y - item["y"])
        self.on_select(entity_id)

    def _drag(self, event):
        if self._drag_entity_id is None:
            return
        item = self._item_for(self._drag_entity_id)
        world_x, world_y = self._to_world(event.x, event.y)
        item["x"] = world_x - self._drag_offset[0]
        item["y"] = world_y - self._drag_offset[1]
        self.render(
            self.entities,
            self.board_items,
            self.relationships,
            self.selected_entity_id,
            self.relationship_source_id,
        )

    def _end_drag(self, event):
        if self._drag_entity_id is None:
            return
        item = self._item_for(self._drag_entity_id)
        self.on_move(self._drag_entity_id, item["x"], item["y"])
        self._drag_entity_id = None

    def _show_context_menu(self, event, entity_id):
        if self.on_context_menu:
            self.on_context_menu(event, entity_id)

    def pulse_entities(self, entity_ids):
        for entity_id in entity_ids:
            self._pulse_entity(entity_id, 0)

    def animate_remove(self, entity_id, on_complete):
        item = self.board_items.get(entity_id)
        if not item:
            on_complete()
            return
        self._animate_remove_frame(entity_id, on_complete, 0)

    def _pulse_entity(self, entity_id, frame):
        item = self.board_items.get(entity_id)
        if not item or frame > 8:
            self.delete(f"pulse:{entity_id}")
            return
        self.delete(f"pulse:{entity_id}")
        x, y = self._to_screen(item["x"], item["y"])
        width = self._scale(item.get("width", DEFAULT_ITEM["width"]))
        height = self._scale(item.get("height", DEFAULT_ITEM["height"]))
        grow = self._scale(4 + frame * 2)
        colors = [
            COMMAND_THEME["focus"],
            "#d8c15e",
            "#a9b95a",
            COMMAND_THEME["accent"],
            "#4b8658",
            "#315b40",
            "#22382b",
            COMMAND_THEME["border_muted"],
            COMMAND_THEME["panel_raised"],
        ]
        self.create_rectangle(
            x - grow,
            y - grow,
            x + width + grow,
            y + height + grow,
            outline=colors[min(frame, len(colors) - 1)],
            width=max(1, int(self._scale(2))),
            tags=(f"pulse:{entity_id}",),
        )
        self.after(35, lambda: self._pulse_entity(entity_id, frame + 1))

    def _animate_remove_frame(self, entity_id, on_complete, frame):
        item = self.board_items.get(entity_id)
        if not item or frame > 7:
            self.delete(f"remove:{entity_id}")
            on_complete()
            return
        self.delete(f"remove:{entity_id}")
        x, y = self._to_screen(item["x"], item["y"])
        width = self._scale(item.get("width", DEFAULT_ITEM["width"]))
        height = self._scale(item.get("height", DEFAULT_ITEM["height"]))
        inset = self._scale(frame * 8)
        self.create_rectangle(
            x + inset,
            y + inset,
            x + width - inset,
            y + height - inset,
            fill="#230b10",
            outline=COMMAND_THEME["danger"],
            width=max(1, int(self._scale(2))),
            tags=(f"remove:{entity_id}",),
        )
        self.after(28, lambda: self._animate_remove_frame(entity_id, on_complete, frame + 1))

    def _zoom_wheel(self, event):
        direction = 1
        if getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
            direction = -1

        previous_zoom = self._zoom
        world_x, world_y = self._to_world(event.x, event.y)
        self._zoom = clamp_zoom(self._zoom * (1.12 if direction > 0 else 0.88))
        if self._zoom == previous_zoom:
            return

        self._pan = (
            event.x - world_x * self._zoom,
            event.y - world_y * self._zoom,
        )
        self.render(
            self.entities,
            self.board_items,
            self.relationships,
            self.selected_entity_id,
            self.relationship_source_id,
        )

    def _start_pan(self, event):
        self._pan_start = (event.x, event.y, self._pan[0], self._pan[1])

    def _pan_motion(self, event):
        if self._pan_start is None:
            return
        start_x, start_y, pan_x, pan_y = self._pan_start
        self._pan = (pan_x + event.x - start_x, pan_y + event.y - start_y)
        self.render(
            self.entities,
            self.board_items,
            self.relationships,
            self.selected_entity_id,
            self.relationship_source_id,
        )

    def _end_pan(self, event):
        self._pan_start = None

    def _to_screen(self, x, y):
        return (x * self._zoom + self._pan[0], y * self._zoom + self._pan[1])

    def _to_world(self, x, y):
        return ((x - self._pan[0]) / self._zoom, (y - self._pan[1]) / self._zoom)

    def _scale(self, value):
        return value * self._zoom
