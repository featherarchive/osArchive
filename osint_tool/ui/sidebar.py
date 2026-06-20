from osint_tool.models import ENTITY_TYPES
from osint_tool.ui.tkcompat import ttk


class Sidebar(ttk.Frame):
    def __init__(self, parent, on_case_create, on_entity_create, on_targets_import, on_delete_all):
        super().__init__(parent, padding=8)
        self.on_case_create = on_case_create
        self.on_entity_create = on_entity_create
        self.on_targets_import = on_targets_import
        self.on_delete_all = on_delete_all
        ttk.Label(self, text="Cases").pack(anchor="w")
        ttk.Button(self, text="New Case", command=self.on_case_create).pack(fill="x", pady=(4, 12))
        ttk.Button(self, text="Import Targets", command=self.on_targets_import).pack(fill="x", pady=(0, 12))
        ttk.Button(self, text="Delete All", command=self.on_delete_all).pack(fill="x", pady=(0, 12))
        ttk.Label(self, text="Add Entity").pack(anchor="w")
        for entity_type in ENTITY_TYPES:
            ttk.Button(
                self,
                text=entity_type.replace("_", " ").title(),
                command=lambda value=entity_type: self.on_entity_create(value),
            ).pack(fill="x", pady=1)
