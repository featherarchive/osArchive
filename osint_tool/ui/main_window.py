import subprocess
import threading
import time
import webbrowser

from osint_tool.data.repositories import Repository
from osint_tool.imports.targets import parse_target_lines
from osint_tool.transforms.core import TransformRun
from osint_tool.transforms.technical import run_dns_transform, run_http_transform
from osint_tool.transforms.username import run_sherlock, whatsmyname_candidates
from osint_tool.ui.board import BoardView
from osint_tool.ui.graph_layout import auto_arrange_positions, orbit_positions, radial_positions
from osint_tool.ui.inspector import Inspector
from osint_tool.ui.sidebar import Sidebar
from osint_tool.ui.theme import COMMAND_THEME
from osint_tool.ui.tkcompat import messagebox, simpledialog, tk, ttk


class MainWindow:
    def __init__(self, connection):
        self.root = tk.Tk()
        self.root.title("osArchive")
        self.root.geometry("1280x780")
        self.repo = Repository(connection)
        self.current_case = None
        self.entities = []
        self.board_items = {}
        self.relationships = []
        self.selected_entity_id = None
        self.relationship_source_id = None
        self._idle_delay_seconds = 300
        self._last_activity_at = time.monotonic()
        self._orbit_active = False
        self._orbit_after_id = None
        self._orbit_angle = 0.0
        self._configure_style()
        self.sidebar = Sidebar(self.root, self.create_case, self.create_entity, self.open_import_targets, self.delete_all)
        self.sidebar.pack(side="left", fill="y")
        self.board = BoardView(self.root, self.select_entity, self.move_entity, self.show_node_menu)
        self.board.pack(side="left", fill="both", expand=True)
        self.inspector = Inspector(self.root, self.save_entity, self.repo.list_lookup_results)
        self.inspector.pack(side="right", fill="y")
        self._bind_activity_tracking()
        self._ensure_case()
        self._schedule_idle_check()

    def run(self):
        self.root.mainloop()

    def _configure_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        self.root.configure(bg=COMMAND_THEME["panel"])
        style.configure(".", background=COMMAND_THEME["panel"], foreground=COMMAND_THEME["text"])
        style.configure("TFrame", background=COMMAND_THEME["panel"])
        style.configure("TLabel", background=COMMAND_THEME["panel"], foreground=COMMAND_THEME["text"])
        style.configure(
            "TButton",
            background=COMMAND_THEME["panel_raised"],
            foreground=COMMAND_THEME["text"],
            bordercolor=COMMAND_THEME["border"],
            lightcolor=COMMAND_THEME["border"],
            darkcolor=COMMAND_THEME["canvas"],
            padding=5,
        )
        style.map(
            "TButton",
            background=[("active", COMMAND_THEME["menu_active"])],
            foreground=[("active", COMMAND_THEME["focus"])],
        )
        style.configure(
            "TEntry",
            fieldbackground=COMMAND_THEME["canvas"],
            foreground=COMMAND_THEME["text"],
            bordercolor=COMMAND_THEME["border"],
            insertcolor=COMMAND_THEME["focus"],
        )

    def _ensure_case(self):
        cases = self.repo.list_cases()
        self.current_case = cases[0] if cases else self.repo.create_case("First Case")
        self.refresh()

    def refresh(self):
        self.entities = self.repo.list_entities(self.current_case.id)
        self.board_items = self.repo.get_board_items(self.current_case.id)
        self.relationships = self.repo.list_relationships(self.current_case.id)
        self.board.render(
            self.entities,
            self.board_items,
            self.relationships,
            self.selected_entity_id,
            self.relationship_source_id,
        )

    def create_case(self):
        name = simpledialog.askstring("New Case", "Case name:")
        if name:
            self.current_case = self.repo.create_case(name)
            self.selected_entity_id = None
            self.relationship_source_id = None
            self.refresh()

    def create_entity(self, entity_type):
        title = simpledialog.askstring("New Entity", f"{entity_type.title()} title:")
        if title:
            entity = self.repo.create_entity(
                self.current_case.id,
                entity_type,
                title,
                custom={"status": "manual"},
            )
            self.refresh()
            self.board.pulse_entities([entity.id])

    def open_import_targets(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Import Targets")
        dialog.geometry("520x420")
        dialog.configure(bg=COMMAND_THEME["panel"])
        ttk.Label(dialog, text="Paste targets").pack(anchor="w", padx=10, pady=(10, 4))
        text = tk.Text(
            dialog,
            height=16,
            width=62,
            bg=COMMAND_THEME["canvas"],
            fg=COMMAND_THEME["text"],
            insertbackground=COMMAND_THEME["focus"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=COMMAND_THEME["border"],
            highlightcolor=COMMAND_THEME["accent"],
        )
        text.pack(fill="both", expand=True, padx=10)
        text.insert(
            "1.0",
            "username: nettihi\n"
            "domain: example.com\n"
            "email: test@example.com\n"
            "https://example.com/profile\n",
        )
        controls = ttk.Frame(dialog)
        controls.pack(fill="x", padx=10, pady=10)
        ttk.Button(controls, text="Import", command=lambda: self.import_targets(text.get("1.0", "end"), dialog)).pack(
            side="right"
        )
        ttk.Button(controls, text="Cancel", command=dialog.destroy).pack(side="right", padx=(0, 8))

    def import_targets(self, text, dialog=None):
        targets = parse_target_lines(text)
        if not targets:
            messagebox.showinfo("Import Targets", "No valid targets found.")
            return
        center = (520, 360)
        positions = auto_arrange_positions(list(range(len(targets))), center=center, radius=max(180, len(targets) * 44))
        created_ids = []
        for index, target in enumerate(targets):
            existing = self.repo.find_entity(self.current_case.id, target.type, target.title)
            if existing:
                created_ids.append(existing.id)
                continue
            position = positions[index]
            entity = self.repo.create_entity(
                self.current_case.id,
                target.type,
                target.title,
                description="Imported target.",
                source="import",
                custom={"status": "manual", "imported": True},
                x=position["x"],
                y=position["y"],
            )
            created_ids.append(entity.id)
        if dialog:
            dialog.destroy()
        self.refresh()
        self.board.pulse_entities(created_ids)
        messagebox.showinfo("Import Targets", f"Imported {len(created_ids)} targets.")

    def select_entity(self, entity_id):
        self.selected_entity_id = entity_id
        entity = self.repo.get_entity(entity_id)
        if entity:
            self.inspector.show_entity(entity)
            self.refresh()

    def move_entity(self, entity_id, x, y):
        self.repo.update_board_position(entity_id, x, y)

    def save_entity(self, entity_id, title, description):
        entity = self.repo.get_entity(entity_id)
        if entity:
            self.repo.update_entity(entity_id, title, description, entity.tags, entity.confidence, entity.source)
            self.refresh()
            self.select_entity(entity_id)

    def delete_entity(self, entity_id):
        entity = self.repo.get_entity(entity_id)
        if not entity:
            return
        if not messagebox.askyesno("Remove from board", f"Remove {entity.title} from this board?"):
            return

        def remove_after_animation():
            self.repo.delete_entity(entity_id)
            if self.selected_entity_id == entity_id:
                self.selected_entity_id = None
            if self.relationship_source_id == entity_id:
                self.relationship_source_id = None
            self.refresh()

        self.board.animate_remove(entity_id, remove_after_animation)

    def delete_all(self):
        if not self.entities:
            messagebox.showinfo("Delete All", "The board is already empty.")
            return
        if not messagebox.askyesno("Delete All", "Delete every node and relationship in this case?"):
            return
        self.repo.delete_case_entities(self.current_case.id)
        self.selected_entity_id = None
        self.relationship_source_id = None
        self._stop_orbit(refresh=False)
        self.refresh()

    def show_node_menu(self, event, entity_id):
        self.selected_entity_id = entity_id
        entity = self.repo.get_entity(entity_id)
        if entity:
            self.inspector.show_entity(entity)

        menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=COMMAND_THEME["panel"],
            fg=COMMAND_THEME["text"],
            activebackground=COMMAND_THEME["menu_active"],
            activeforeground=COMMAND_THEME["focus"],
        )
        menu.add_command(label="Start relationship", command=lambda: self.start_relationship(entity_id))
        if self.relationship_source_id and self.relationship_source_id != entity_id:
            source_title = self._entity_title(self.relationship_source_id)
            menu.add_command(label=f"Link from {source_title}", command=lambda: self.finish_relationship(entity_id))
        if self.relationship_source_id:
            menu.add_separator()
            menu.add_command(label="Cancel relationship", command=self.cancel_relationship)
        menu.add_separator()
        if entity and entity.type == "username":
            menu.add_command(
                label="Run built-in Sherlock scan",
                command=lambda: self.run_transform(entity_id, "Built-in Sherlock scan", run_sherlock),
            )
        menu.add_command(label="Set as Main Node", command=lambda: self.set_main_node(entity_id))
        self._add_transform_menu(menu, entity_id)
        self._add_graph_menu(menu, entity_id)
        menu.add_separator()
        menu.add_command(label="Remove from board", command=lambda: self.delete_entity(entity_id))
        menu.tk_popup(event.x_root, event.y_root)
        menu.grab_release()
        self.refresh()

    def start_relationship(self, entity_id):
        self.relationship_source_id = entity_id
        self.selected_entity_id = entity_id
        self.refresh()

    def cancel_relationship(self):
        self.relationship_source_id = None
        self.refresh()

    def set_main_node(self, entity_id):
        self.repo.set_main_entity(self.current_case.id, entity_id)
        self.selected_entity_id = entity_id
        self._stop_orbit(refresh=False)
        self.refresh()
        self.board.pulse_entities([entity_id])

    def finish_relationship(self, target_entity_id):
        source_entity_id = self.relationship_source_id
        if not source_entity_id or source_entity_id == target_entity_id:
            return
        label = simpledialog.askstring("New Relationship", "Relationship label:", initialvalue="related to")
        if label:
            self.repo.create_relationship(self.current_case.id, source_entity_id, target_entity_id, label)
            self.relationship_source_id = None
            self.selected_entity_id = target_entity_id
            self.refresh()

    def _entity_title(self, entity_id):
        entity = self.repo.get_entity(entity_id)
        return entity.title if entity else "selected node"

    def _add_transform_menu(self, menu, entity_id):
        entity = self.repo.get_entity(entity_id)
        transform_menu = tk.Menu(
            menu,
            tearoff=0,
            bg=COMMAND_THEME["panel"],
            fg=COMMAND_THEME["text"],
            activebackground=COMMAND_THEME["menu_active"],
            activeforeground=COMMAND_THEME["focus"],
        )
        if entity and entity.type == "username":
            transform_menu.add_command(
                label="WhatsMyName candidates",
                command=lambda: self.run_transform(entity_id, "WhatsMyName candidates", whatsmyname_candidates),
            )
            transform_menu.add_command(
                label="Built-in Sherlock scan",
                command=lambda: self.run_transform(entity_id, "Built-in Sherlock scan", run_sherlock),
            )
        if entity and entity.type in {"domain", "ip", "url"}:
            transform_menu.add_command(
                label="DNS lookup",
                command=lambda: self.run_transform(entity_id, "DNS lookup", run_dns_transform),
            )
            transform_menu.add_command(
                label="HTTP headers",
                command=lambda: self.run_transform(entity_id, "HTTP headers", run_http_transform),
            )
            transform_menu.add_command(label="Open SpiderFoot", command=lambda: self.open_spiderfoot(entity_id))
        if transform_menu.index("end") is None:
            transform_menu.add_command(label="No transforms for this type", state="disabled")
        menu.add_cascade(label="Run Transform", menu=transform_menu)

    def _add_graph_menu(self, menu, entity_id):
        graph_menu = tk.Menu(
            menu,
            tearoff=0,
            bg=COMMAND_THEME["panel"],
            fg=COMMAND_THEME["text"],
            activebackground=COMMAND_THEME["menu_active"],
            activeforeground=COMMAND_THEME["focus"],
        )
        graph_menu.add_command(label="Auto arrange all", command=self.auto_arrange_graph)
        graph_menu.add_command(label="Radial layout here", command=lambda: self.radial_layout(entity_id))
        collapsed = int(self.board_items.get(entity_id, {}).get("collapsed", 0)) == 1
        graph_menu.add_command(
            label="Expand neighbors" if collapsed else "Collapse neighbors",
            command=lambda: self.toggle_collapse(entity_id),
        )
        menu.add_cascade(label="Graph", menu=graph_menu)

    def run_transform(self, entity_id, name, runner):
        entity = self.repo.get_entity(entity_id)
        if not entity:
            return

        def work():
            try:
                result = runner(entity.title)
            except Exception as exc:
                result = TransformRun(name=name, status="error", message=str(exc), raw={"error": str(exc)})
            self.root.after(0, lambda: self.apply_transform_run(entity_id, result))

        threading.Thread(target=work, daemon=True).start()

    def apply_transform_run(self, source_entity_id, run):
        source_item = self.board_items.get(source_entity_id, {"x": 100, "y": 100, "width": 180, "height": 96})
        center = (source_item["x"] + 320, source_item["y"] + 120)
        positions = auto_arrange_positions(list(range(len(run.nodes))), center=center, radius=max(180, len(run.nodes) * 18))
        created_ids = []

        for index, node in enumerate(run.nodes):
            title = node.value if node.type == "url" else node.title
            existing = self.repo.find_entity(self.current_case.id, node.type, title)
            position = positions.get(index, {"x": source_item["x"] + 260, "y": source_item["y"] + 140})
            description = node.description
            if node.type == "url" and node.title != node.value:
                description = f"{node.title}\n{node.value}\n{node.description}".strip()
            if existing:
                target = existing
            else:
                target = self.repo.create_entity(
                    self.current_case.id,
                    node.type,
                    title,
                    description=description,
                    confidence="unknown",
                    source=node.source,
                    custom={"status": node.status, **node.custom},
                    x=position["x"],
                    y=position["y"],
                )
            created_ids.append(target.id)
            self.repo.create_relationship(self.current_case.id, source_entity_id, target.id, node.relationship)

        self.repo.add_lookup_result(
            source_entity_id,
            "transform",
            run.name,
            "",
            {
                "status": run.status,
                "message": run.message,
                "nodes": [
                    {"type": node.type, "title": node.title, "value": node.value, "status": node.status}
                    for node in run.nodes
                ],
                "raw": run.raw,
            },
            status=run.status,
        )
        self.select_entity(source_entity_id)
        self.board.pulse_entities(created_ids)

    def open_spiderfoot(self, entity_id):
        entity = self.repo.get_entity(entity_id)
        if not entity:
            return
        try:
            subprocess.Popen(
                ["spiderfoot", "-l", "127.0.0.1:7331"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
            status = "ok"
            message = "Opened SpiderFoot at http://127.0.0.1:7331/."
        except FileNotFoundError:
            status = "error"
            message = "SpiderFoot command was not found."
        self.repo.add_lookup_result(
            entity_id,
            "transform",
            "SpiderFoot launch",
            "http://127.0.0.1:7331/",
            {"status": status, "message": message, "target": entity.title},
            status=status,
        )
        if status == "ok":
            webbrowser.open("http://127.0.0.1:7331/")
        self.refresh()
        self.select_entity(entity_id)

    def auto_arrange_graph(self):
        positions = auto_arrange_positions([entity.id for entity in self.entities])
        for entity_id, position in positions.items():
            self.repo.update_board_position(entity_id, position["x"], position["y"])
        self.refresh()

    def radial_layout(self, entity_id):
        source_item = self.board_items.get(entity_id, {"x": 600, "y": 400, "width": 180, "height": 96})
        center = (source_item["x"], source_item["y"])
        positions = radial_positions(entity_id, self.relationships, center=center)
        for target_id, position in positions.items():
            self.repo.update_board_position(target_id, position["x"], position["y"])
        self.refresh()

    def toggle_collapse(self, entity_id):
        collapsed = int(self.board_items.get(entity_id, {}).get("collapsed", 0)) == 1
        self.repo.set_board_collapsed(entity_id, not collapsed)
        self.refresh()

    def _bind_activity_tracking(self):
        for sequence in ("<KeyPress>", "<ButtonPress>", "<Motion>", "<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.root.bind_all(sequence, self._record_activity, add="+")

    def _record_activity(self, event=None):
        self._last_activity_at = time.monotonic()
        if self._orbit_active:
            self._stop_orbit(refresh=True)

    def _schedule_idle_check(self):
        if not self._orbit_active and time.monotonic() - self._last_activity_at >= self._idle_delay_seconds:
            self._start_orbit()
        self.root.after(1000, self._schedule_idle_check)

    def _start_orbit(self):
        main_entity_id = self.repo.get_main_entity_id(self.current_case.id)
        if not main_entity_id or not self._related_entity_ids(main_entity_id):
            return
        self._orbit_active = True
        self._orbit_angle = 0.0
        self._animate_orbit()

    def _stop_orbit(self, refresh=True):
        self._orbit_active = False
        if self._orbit_after_id is not None:
            try:
                self.root.after_cancel(self._orbit_after_id)
            except tk.TclError:
                pass
            self._orbit_after_id = None
        if refresh:
            self.refresh()

    def _animate_orbit(self):
        if not self._orbit_active:
            return
        main_entity_id = self.repo.get_main_entity_id(self.current_case.id)
        if not main_entity_id or main_entity_id not in self.board_items:
            self._stop_orbit(refresh=True)
            return
        related_entity_ids = self._related_entity_ids(main_entity_id)
        if not related_entity_ids:
            self._stop_orbit(refresh=True)
            return
        radius = max(220, len(related_entity_ids) * 42)
        positions = orbit_positions(
            related_entity_ids,
            self.board_items[main_entity_id],
            self._orbit_angle,
            radius=radius,
        )
        for entity_id, position in positions.items():
            if entity_id in self.board_items:
                self.board_items[entity_id]["x"] = position["x"]
                self.board_items[entity_id]["y"] = position["y"]
        self._orbit_angle += 0.035
        self.board.render(
            self.entities,
            self.board_items,
            self.relationships,
            self.selected_entity_id,
            self.relationship_source_id,
        )
        self._orbit_after_id = self.root.after(50, self._animate_orbit)

    def _related_entity_ids(self, main_entity_id):
        related = []
        hidden_ids = self.board._hidden_entity_ids() if hasattr(self.board, "_hidden_entity_ids") else set()
        for relationship in self.relationships:
            source = relationship["source_entity_id"]
            target = relationship["target_entity_id"]
            if source == main_entity_id and target not in hidden_ids:
                related.append(target)
            elif target == main_entity_id and source not in hidden_ids:
                related.append(source)
        return list(dict.fromkeys(related))
