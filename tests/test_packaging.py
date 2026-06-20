import tomllib
from pathlib import Path


def test_pyproject_exposes_osarchive_script():
    data = tomllib.loads(Path("pyproject.toml").read_text())

    assert data["project"]["scripts"]["osarchive"] == "osint_tool.app:main"


def test_project_declares_noncommercial_public_license():
    data = tomllib.loads(Path("pyproject.toml").read_text())
    license_text = Path("LICENSE").read_text()

    assert data["project"]["license"] == "LicenseRef-osArchive-NonCommercial"
    assert license_text.startswith("osArchive Non-Commercial Public License")
    assert "Copyright (c) 2026 Archive3" in license_text
    assert "You may not sell the Software or any modified version" in license_text
    assert "commercial use is not permitted" in license_text
    assert "publicly available, free of charge" in license_text


def test_linux_release_launcher_exists():
    launcher = Path("linux/osArchive.sh")
    desktop_file = Path("linux/osArchive.desktop")

    assert launcher.exists()
    assert "osarchive" in launcher.read_text()
    assert desktop_file.exists()
    assert "Name=osArchive" in desktop_file.read_text()
