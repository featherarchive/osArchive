import json
import os
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from importlib import resources
from pathlib import Path

from osint_tool.transforms.core import TransformNode, TransformRun


DEFAULT_WHATSMYNAME_PATH = Path.home() / ".local" / "share" / "WhatsMyName" / "wmn-data.json"
DEFAULT_SHERLOCK_PATH = (
    Path.home()
    / ".local"
    / "share"
    / "pipx"
    / "venvs"
    / "sherlock-project"
    / "lib"
    / "python3.14"
    / "site-packages"
    / "sherlock_project"
    / "resources"
    / "data.json"
)
USER_SHERLOCK_DATA_PATH = Path.home() / ".local" / "share" / "osArchive" / "sherlock-data.json"
FOUND_LINE_RE = re.compile(r"^\[\+\]\s*(?P<site>[^:]+):\s*(?P<url>https?://\S+)", re.MULTILINE)


def load_whatsmyname_sites(path: Path = DEFAULT_WHATSMYNAME_PATH) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return list(data.get("sites", []))


def load_sherlock_sites(path: Path | None = None) -> dict[str, dict]:
    data_path = _first_existing_sherlock_path(path)
    if data_path:
        data = json.loads(data_path.read_text())
    else:
        with resources.files("osint_tool.transforms").joinpath("sherlock_sites.json").open() as file:
            data = json.load(file)
    return {
        name: site
        for name, site in data.items()
        if isinstance(site, dict) and not name.startswith("$") and not site.get("isNSFW")
    }


def _first_existing_sherlock_path(path: Path | None = None) -> Path | None:
    candidates = []
    if path:
        candidates.append(path)
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(Path(appdata) / "osArchive" / "sherlock-data.json")
    candidates.extend([USER_SHERLOCK_DATA_PATH, DEFAULT_SHERLOCK_PATH])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def build_whatsmyname_candidates(username: str, sites: list[dict], limit: int = 30) -> list[TransformNode]:
    nodes = []
    username = username.strip()
    for site in sites:
        template = str(site.get("uri_check", ""))
        if "{account}" not in template:
            continue
        url = template.replace("{account}", username)
        nodes.append(
            TransformNode(
                type="url",
                title=str(site.get("name", url)),
                value=url,
                description=f"Candidate profile generated from WhatsMyName category: {site.get('cat', 'unknown')}",
                status="candidate",
                source="WhatsMyName",
                relationship="candidate profile",
                custom={"tool": "WhatsMyName", "category": site.get("cat", "")},
            )
        )
        if len(nodes) >= limit:
            break
    return nodes


def parse_sherlock_found_urls(output: str) -> list[TransformNode]:
    nodes = []
    for match in FOUND_LINE_RE.finditer(output):
        site = match.group("site").strip()
        url = match.group("url").strip()
        nodes.append(
            TransformNode(
                type="url",
                title=site,
                value=url,
                description="Profile found by Sherlock.",
                status="found",
                source="Sherlock",
                relationship="found profile",
                custom={"tool": "Sherlock"},
            )
        )
    return nodes


def build_sherlock_profile_node(site_name: str, site: dict, username: str) -> TransformNode:
    url = _format_sherlock_url(str(site["url"]), username)
    return TransformNode(
        type="url",
        title=site_name,
        value=url,
        description="Profile found by built-in Sherlock scan.",
        status="found",
        source="Sherlock built-in",
        relationship="found profile",
        custom={"tool": "Sherlock built-in"},
    )


def scan_sherlock_sites(
    username: str,
    sites: dict[str, dict],
    fetcher=None,
    timeout: float = 6.0,
    max_workers: int = 24,
) -> list[TransformNode]:
    username = username.strip()
    fetcher = fetcher or fetch_sherlock_url
    nodes = []
    candidates = [
        (site_name, site)
        for site_name, site in sites.items()
        if "url" in site and _username_matches(site, username)
    ]
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_scan_sherlock_site, site_name, site, username, fetcher, timeout): site_name
            for site_name, site in candidates
        }
        for future in as_completed(futures):
            node = future.result()
            if node:
                nodes.append(node)
    return sorted(nodes, key=lambda node: node.title.lower())


def fetch_sherlock_url(url: str, timeout: float) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; osArchive/0.1; +https://localhost)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(200_000).decode("utf-8", errors="replace")
            return {"status_code": response.status, "body": body, "url": response.geturl()}
    except urllib.error.HTTPError as exc:
        body = exc.read(200_000).decode("utf-8", errors="replace")
        return {"status_code": exc.code, "body": body, "url": exc.geturl()}
    except Exception as exc:
        return {"status_code": 0, "body": "", "url": url, "error": str(exc)}


def _scan_sherlock_site(site_name: str, site: dict, username: str, fetcher, timeout: float) -> TransformNode | None:
    url = _format_sherlock_url(str(site["url"]), username)
    response = fetcher(url, timeout)
    if _is_sherlock_found(site, response):
        return build_sherlock_profile_node(site_name, site, username)
    return None


def _is_sherlock_found(site: dict, response: dict) -> bool:
    error_type = site.get("errorType", "status_code")
    status_code = int(response.get("status_code", 0) or 0)
    body = str(response.get("body", ""))
    if error_type == "message":
        error_messages = site.get("errorMsg", [])
        if isinstance(error_messages, str):
            error_messages = [error_messages]
        return status_code not in {0, 404} and not any(message in body for message in error_messages)
    error_codes = site.get("errorCode", 404)
    if not isinstance(error_codes, list):
        error_codes = [error_codes]
    return status_code not in {0, *[int(code) for code in error_codes]}


def _username_matches(site: dict, username: str) -> bool:
    regex = site.get("regexCheck")
    if not regex:
        return True
    return re.match(str(regex), username) is not None


def _format_sherlock_url(template: str, username: str) -> str:
    if "{}" in template:
        return template.format(username)
    return template.replace("{account}", username)


def whatsmyname_candidates(username: str, limit: int = 30) -> TransformRun:
    sites = load_whatsmyname_sites()
    nodes = build_whatsmyname_candidates(username, sites, limit=limit)
    return TransformRun(
        name="WhatsMyName candidates",
        status="ok" if nodes else "empty",
        nodes=nodes,
        message=f"Generated {len(nodes)} candidate profile URLs.",
        raw={"site_count": len(sites), "node_count": len(nodes)},
    )


def run_sherlock(username: str, timeout_seconds: int = 6) -> TransformRun:
    sites = load_sherlock_sites()
    nodes = scan_sherlock_sites(username, sites, timeout=timeout_seconds)
    status = "ok" if nodes else "empty"
    return TransformRun(
        "Built-in Sherlock scan",
        status,
        nodes=nodes,
        message=f"Built-in Sherlock checked {len(sites)} sites and found {len(nodes)} profiles.",
        raw={"site_count": len(sites), "node_count": len(nodes), "mode": "built-in"},
    )
