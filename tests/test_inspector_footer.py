from pathlib import Path


def test_inspector_renders_archive_credit():
    inspector_source = Path("osint_tool/ui/inspector.py").read_text()

    assert "Made by <Archive3" in inspector_source
