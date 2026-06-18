from osint_tool.lookups.technical import normalize_url, parse_url_metadata


def test_normalize_url_adds_scheme():
    assert normalize_url("example.com/path") == "https://example.com/path"


def test_parse_url_metadata_extracts_parts():
    metadata = parse_url_metadata("https://example.com:8443/path?q=1")
    assert metadata == {
        "normalized_url": "https://example.com:8443/path?q=1",
        "scheme": "https",
        "hostname": "example.com",
        "port": 8443,
        "path": "/path",
        "query": "q=1",
    }
