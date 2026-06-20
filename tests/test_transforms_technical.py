from osint_tool.transforms.technical import dns_nodes_from_result, http_node_from_result


def test_dns_nodes_from_result_creates_ip_nodes():
    result = {"status": "ok", "addresses": ["192.0.2.10", "2001:db8::1"]}

    nodes = dns_nodes_from_result(result)

    assert [(node.type, node.title, node.status, node.relationship) for node in nodes] == [
        ("ip", "192.0.2.10", "found", "resolves to"),
        ("ip", "2001:db8::1", "found", "resolves to"),
    ]


def test_dns_nodes_from_result_creates_error_note():
    result = {"status": "error", "error": "Name or service not known"}

    nodes = dns_nodes_from_result(result)

    assert len(nodes) == 1
    assert nodes[0].type == "note"
    assert nodes[0].status == "error"
    assert "Name or service not known" in nodes[0].description


def test_http_node_from_result_summarizes_status_and_server():
    result = {"status": "ok", "status_code": 200, "reason": "OK", "headers": {"Server": "nginx"}}

    node = http_node_from_result("https://example.com", result)

    assert node.type == "note"
    assert node.title == "HTTP 200 OK"
    assert node.status == "found"
    assert "Server: nginx" in node.description
    assert node.relationship == "http metadata"
