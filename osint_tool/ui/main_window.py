from osint_tool.data.repositories import Repository
from osint_tool.ui.board import BoardView
from osint_tool.ui.inspector import Inspector
from osint_tool.ui.sidebar import Sidebar
from osint_tool.ui.tkcompat import simpledialog, tk, ttk


class MainWindow:
    def __init__(self, connection):
        self.root = tk.Tk()
        self.root.title("OSINT Investigation Board")
        self.root.geometry("1280x780")
        self.repo = Repository(connection)
        self.current_case = None
        self.entities = []
        self.board_items = {}
        self.relationships = []
        self._configure_style()
        self.sidebar = Sidebar(self.root, self.create_case, self.create_entity)
        self.sidebar.pack(side="left", fill="y")
        self.board = BoardView(self.root, self.select_entity, self.move_entity)
        self.board.pack(side="left", fill="both", expand=True)
        self.inspector = Inspector(self.root, self.save_entity)
        self.inspector.pack(side="right", fill="y")
        self._ensure_case()

    def run(self):
        self.root.mainloop()

    def _configure_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background="#1a2026", foreground="#e8ecef")
        style.configure("TFrame", background="#1a2026")
        style.configure("TLabel", background="#1a2026", foreground="#e8ecef")
        style.configure("TButton", background="#26313b", foreground="#e8ecef", padding=5)
        style.configure("TEntry", fieldbackground="#111417", foreground="#e8ecef")

    def _ensure_case(self):
        cases = self.repo.list_cases()
        self.current_case = cases[0] if cases else self.repo.create_case("First Case")
        self.refresh()

    def refresh(self):
        self.entities = self.repo.list_entities(self.current_case.id)
        self.board_items = self.repo.get_board_items(self.current_case.id)
        self.relationships = self.repo.list_relationships(self.current_case.id)
        self.board.render(self.entities, self.board_items, self.relationships)

    def create_case(self):
        name = simpledialog.askstring("New Case", "Case name:")
        if name:
            self.current_case = self.repo.create_case(name)
            self.refresh()

    def create_entity(self, entity_type):
        title = simpledialog.askstring("New Entity", f"{entity_type.title()} title:")
        if title:
            self.repo.create_entity(self.current_case.id, entity_type, title)
            self.refresh()

    def select_entity(self, entity_id):
        entity = self.repo.get_entity(entity_id)
        if entity:
            self.inspector.show_entity(entity)

    def move_entity(self, entity_id, x, y):
        self.repo.update_board_position(entity_id, x, y)

    def save_entity(self, entity_id, title, description):
        entity = self.repo.get_entity(entity_id)
        if entity:
            self.repo.update_entity(entity_id, title, description, entity.tags, entity.confidence, entity.source)
            self.refresh()
            self.select_entity(entity_id)
