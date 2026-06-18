import osint_tool
from osint_tool.app import get_default_db_path


def test_package_imports():
    assert osint_tool.__version__ == "0.1.0"


def test_default_db_path_uses_home_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = get_default_db_path()
    assert db_path == tmp_path / ".local" / "share" / "osint-tool" / "osint.sqlite3"


def test_ui_modules_import_without_creating_window():
    from osint_tool.ui.board import BoardView
    from osint_tool.ui.inspector import Inspector
    from osint_tool.ui.main_window import MainWindow
    from osint_tool.ui.sidebar import Sidebar

    assert BoardView is not None
    assert Inspector is not None
    assert MainWindow is not None
    assert Sidebar is not None
