from osint_tool.lookups.technical import fetch_http_headers, parse_url_metadata, resolve_dns
from osint_tool.transforms.core import TransformNode, TransformRun


def dns_nodes_from_result(result: dict) -> list[TransformNode]:
    if result.get("status") != "ok":
        error = str(result.get("error", "DNS lookup failed."))
        return [
            TransformNode(
                type="note",
                title="DNS lookup failed",
                value=error,
                description=error,
                status="error",
                source="DNS",
                relationship="dns error",
                custom={"tool": "DNS"},
            )
        ]

    nodes = []
    for address in result.get("addresses", []):
        nodes.append(
            TransformNode(
                type="ip",
                title=str(address),
                value=str(address),
                description="Address returned by DNS resolution.",
                status="found",
                source="DNS",
                relationship="resolves to",
                custom={"tool": "DNS"},
            )
        )
    return nodes


def http_node_from_result(value: str, result: dict) -> TransformNode:
    if result.get("status") != "ok":
        error = str(result.get("error", "HTTP lookup failed."))
        return TransformNode(
            type="note",
            title="HTTP lookup failed",
            value=error,
            description=error,
            status="error",
            source="HTTP",
            relationship="http error",
            custom={"tool": "HTTP", "target": value},
        )

    status_code = result.get("status_code", "")
    reason = result.get("reason", "")
    headers = result.get("headers", {})
    lines = [f"Target: {value}", f"Status: {status_code} {reason}".strip()]
    for key in ("Server", "Content-Type", "Location"):
        if headers.get(key):
            lines.append(f"{key}: {headers[key]}")
    return TransformNode(
        type="note",
        title=f"HTTP {status_code} {reason}".strip(),
        value="\n".join(lines),
        description="\n".join(lines),
        status="found",
        source="HTTP",
        relationship="http metadata",
        custom={"tool": "HTTP", "target": value, "status_code": status_code},
    )


def run_dns_transform(value: str) -> TransformRun:
    metadata = parse_url_metadata(value)
    hostname = str(metadata.get("hostname") or value).strip()
    result = resolve_dns(hostname)
    nodes = dns_nodes_from_result(result)
    return TransformRun(
        name="DNS lookup",
        status="ok" if result.get("status") == "ok" else "error",
        nodes=nodes,
        message=f"Resolved {hostname}.",
        raw={"target": hostname, "result": result},
    )


def run_http_transform(value: str) -> TransformRun:
    result = fetch_http_headers(value)
    node = http_node_from_result(value, result)
    return TransformRun(
        name="HTTP headers",
        status="ok" if result.get("status") == "ok" else "error",
        nodes=[node],
        message=f"Fetched HTTP metadata for {value}.",
        raw={"target": value, "result": result},
    )
