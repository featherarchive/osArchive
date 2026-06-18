import osint_tool
from osint_tool.app import get_default_db_path


def test_package_imports():
    assert osint_tool.__version__ == "0.1.0"


def test_default_db_path_uses_home_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = get_default_db_path()
    assert db_path == tmp_path / ".local" / "share" / "osint-tool" / "osint.sqlite3"
