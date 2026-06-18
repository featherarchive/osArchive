import webbrowser

from osint_tool.lookups.links import build_lookup_links
from osint_tool.ui.tkcompat import tk, ttk


class Inspector(ttk.Frame):
    def __init__(self, parent, on_save):
        super().__init__(parent, padding=8)
        self.on_save = on_save
        self.entity = None
        ttk.Label(self, text="Inspector").pack(anchor="w")
        self.title_var = tk.StringVar()
        self.description = tk.Text(self, height=6, width=32)
        ttk.Label(self, text="Title").pack(anchor="w", pady=(12, 0))
        ttk.Entry(self, textvariable=self.title_var).pack(fill="x")
        ttk.Label(self, text="Description").pack(anchor="w", pady=(8, 0))
        self.description.pack(fill="x")
        ttk.Button(self, text="Save", command=self._save).pack(fill="x", pady=(8, 12))
        self.lookup_frame = ttk.Frame(self)
        self.lookup_frame.pack(fill="both", expand=True)

    def show_entity(self, entity):
        self.entity = entity
        self.title_var.set(entity.title)
        self.description.delete("1.0", "end")
        self.description.insert("1.0", entity.description)
        self._render_links()

    def _render_links(self):
        for child in self.lookup_frame.winfo_children():
            child.destroy()
        if not self.entity:
            return
        ttk.Label(self.lookup_frame, text="Lookup Links").pack(anchor="w")
        for link in build_lookup_links(self.entity.type, self.entity.title):
            ttk.Button(
                self.lookup_frame,
                text=link["label"],
                command=lambda url=link["url"]: webbrowser.open(url),
            ).pack(fill="x", pady=1)

    def _save(self):
        if not self.entity:
            return
        self.on_save(
            self.entity.id,
            self.title_var.get().strip(),
            self.description.get("1.0", "end").strip(),
        )
