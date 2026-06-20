import os
from pathlib import Path


def get_default_db_path(
    platform_name: str | None = None,
    appdata: str | None = None,
    home: Path | None = None,
) -> Path:
    platform_name = platform_name or os.name
    home = home or Path.home()
    if platform_name == "nt":
        base = Path(appdata or os.environ.get("APPDATA") or home / "AppData" / "Roaming")
        return base / "osArchive" / "osint.sqlite3"
    return home / ".local" / "share" / "osint-tool" / "osint.sqlite3"


def main() -> None:
    from osint_tool.data.db import connect
    from osint_tool.ui.main_window import MainWindow

    db_path = get_default_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect(db_path)
    window = MainWindow(connection)
    window.run()
