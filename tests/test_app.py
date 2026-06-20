from pathlib import Path

from osint_tool.app import get_default_db_path


def test_default_db_path_uses_posix_local_share():
    path = get_default_db_path(platform_name="posix", home=Path("/home/tester"))

    assert path == Path("/home/tester/.local/share/osint-tool/osint.sqlite3")


def test_default_db_path_uses_windows_appdata():
    path = get_default_db_path(platform_name="nt", appdata="C:/Users/tester/AppData/Roaming")

    assert path == Path("C:/Users/tester/AppData/Roaming") / "osArchive" / "osint.sqlite3"
