from osint_tool.transforms.username import (
    build_sherlock_profile_node,
    build_whatsmyname_candidates,
    load_sherlock_sites,
    parse_sherlock_found_urls,
    scan_sherlock_sites,
)


def test_build_whatsmyname_candidates_uses_account_template():
    sites = [
        {
            "name": "Example Social",
            "uri_check": "https://example.test/{account}",
            "cat": "social",
        },
        {
            "name": "No Template",
            "uri_check": "https://example.test/static",
            "cat": "misc",
        },
    ]

    nodes = build_whatsmyname_candidates("nettihi", sites, limit=10)

    assert len(nodes) == 1
    assert nodes[0].type == "url"
    assert nodes[0].title == "Example Social"
    assert nodes[0].value == "https://example.test/nettihi"
    assert nodes[0].status == "candidate"
    assert nodes[0].source == "WhatsMyName"


def test_build_whatsmyname_candidates_respects_limit():
    sites = [
        {"name": f"Site {index}", "uri_check": "https://example.test/{account}", "cat": "social"}
        for index in range(5)
    ]

    nodes = build_whatsmyname_candidates("nettihi", sites, limit=2)

    assert [node.title for node in nodes] == ["Site 0", "Site 1"]


def test_parse_sherlock_found_urls_reads_found_lines():
    output = """
[+] GitHub: https://github.com/nettihi
[-] Reddit: Not Found!
[+] Roblox: https://www.roblox.com/user.aspx?username=nettihi
"""

    nodes = parse_sherlock_found_urls(output)

    assert [(node.title, node.value, node.status) for node in nodes] == [
        ("GitHub", "https://github.com/nettihi", "found"),
        ("Roblox", "https://www.roblox.com/user.aspx?username=nettihi", "found"),
    ]


def test_load_sherlock_sites_skips_metadata(tmp_path):
    path = tmp_path / "data.json"
    path.write_text(
        '{"$schema": "data.schema.json", "GitHub": {"url": "https://github.com/{}", "errorType": "status_code"}}'
    )

    sites = load_sherlock_sites(path)

    assert list(sites) == ["GitHub"]


def test_build_sherlock_profile_node_formats_url():
    node = build_sherlock_profile_node("GitHub", {"url": "https://github.com/{}"}, "nettihi")

    assert node.type == "url"
    assert node.title == "GitHub"
    assert node.value == "https://github.com/nettihi"
    assert node.source == "Sherlock built-in"


def test_scan_sherlock_sites_uses_status_code_error_type():
    sites = {
        "FoundSite": {"url": "https://example.test/{}", "errorType": "status_code", "errorCode": 404},
        "MissingSite": {"url": "https://missing.test/{}", "errorType": "status_code", "errorCode": 404},
    }

    def fetcher(url, timeout):
        if "missing" in url:
            return {"status_code": 404, "body": "", "url": url}
        return {"status_code": 200, "body": "ok", "url": url}

    nodes = scan_sherlock_sites("nettihi", sites, fetcher=fetcher)

    assert [(node.title, node.value) for node in nodes] == [("FoundSite", "https://example.test/nettihi")]
