import http.client
import socket
from urllib.parse import urlparse


def normalize_url(value: str) -> str:
    value = value.strip()
    if "://" not in value:
        return f"https://{value}"
    return value


def parse_url_metadata(value: str) -> dict[str, str | int | None]:
    normalized = normalize_url(value)
    parsed = urlparse(normalized)
    return {
        "normalized_url": normalized,
        "scheme": parsed.scheme,
        "hostname": parsed.hostname,
        "port": parsed.port,
        "path": parsed.path or "/",
        "query": parsed.query,
    }


def resolve_dns(hostname: str) -> dict[str, list[str] | str]:
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(hostname, None)})
        return {"status": "ok", "addresses": addresses}
    except OSError as exc:
        return {"status": "error", "error": str(exc)}


def fetch_http_headers(value: str, timeout: float = 5.0) -> dict[str, object]:
    metadata = parse_url_metadata(value)
    hostname = str(metadata["hostname"] or "")
    scheme = str(metadata["scheme"])
    path = str(metadata["path"])
    if metadata["query"]:
        path = f"{path}?{metadata['query']}"
    connection_class = http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection
    try:
        connection = connection_class(hostname, metadata["port"], timeout=timeout)
        connection.request("HEAD", path)
        response = connection.getresponse()
        return {
            "status": "ok",
            "status_code": response.status,
            "reason": response.reason,
            "headers": dict(response.getheaders()),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
    finally:
        try:
            connection.close()
        except Exception:
            pass
