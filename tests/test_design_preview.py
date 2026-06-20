from pathlib import Path


PREVIEW_DIR = Path("design-preview")


def test_design_preview_has_three_concepts():
    html = (PREVIEW_DIR / "index.html").read_text()

    assert html.count('class="concept-panel') == 3
    assert 'data-theme="tactical"' in html
    assert 'data-theme="forensic"' in html
    assert 'data-theme="command"' in html


def test_design_preview_links_assets():
    html = (PREVIEW_DIR / "index.html").read_text()

    assert 'href="styles.css"' in html
    assert 'src="script.js"' in html
    assert (PREVIEW_DIR / "styles.css").exists()
    assert (PREVIEW_DIR / "script.js").exists()
