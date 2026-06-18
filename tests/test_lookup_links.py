from osint_tool.lookups.links import build_lookup_links


def labels(links):
    return {link["label"] for link in links}


def test_domain_links_include_search_and_reputation_sources():
    links = build_lookup_links("domain", "example.com")
    assert {"Google", "DuckDuckGo", "VirusTotal", "Shodan", "DNSDumpster"}.issubset(labels(links))
    assert any("example.com" in link["url"] for link in links)


def test_username_links_include_profile_pivots():
    links = build_lookup_links("username", "alice")
    assert {"Google", "DuckDuckGo", "GitHub", "Reddit", "X/Twitter", "Instagram", "TikTok"}.issubset(labels(links))
    assert {"https://github.com/alice", "https://www.instagram.com/alice"}.issubset({link["url"] for link in links})


def test_email_uses_search_only():
    links = build_lookup_links("email", "a@example.com")
    assert labels(links) == {"Google", "DuckDuckGo"}
