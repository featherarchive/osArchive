import tomllib
from pathlib import Path


def test_pyproject_exposes_osarchive_script():
    data = tomllib.loads(Path("pyproject.toml").read_text())

    assert data["project"]["scripts"]["osarchive"] == "osint_tool.app:main"


def test_linux_release_launcher_exists():
    launcher = Path("linux/osArchive.sh")
    desktop_file = Path("linux/osArchive.desktop")

    assert launcher.exists()
    assert "osarchive" in launcher.read_text()
    assert desktop_file.exists()
    assert "Name=osArchive" in desktop_file.read_text()
