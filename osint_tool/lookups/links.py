from urllib.parse import quote_plus


def _search_links(value: str) -> list[dict[str, str]]:
    query = quote_plus(value)
    return [
        {"label": "Google", "url": f"https://www.google.com/search?q={query}"},
        {"label": "DuckDuckGo", "url": f"https://duckduckgo.com/?q={query}"},
    ]


def build_lookup_links(entity_type: str, value: str) -> list[dict[str, str]]:
    value = value.strip()
    links = _search_links(value)
    encoded = quote_plus(value)

    if entity_type in {"domain", "ip"}:
        links.extend(
            [
                {"label": "VirusTotal", "url": f"https://www.virustotal.com/gui/search/{encoded}"},
                {"label": "Shodan", "url": f"https://www.shodan.io/search?query={encoded}"},
                {"label": "DNSDumpster", "url": "https://dnsdumpster.com/"},
            ]
        )
    elif entity_type == "username":
        links.extend(
            [
                {"label": "GitHub", "url": f"https://github.com/{value}"},
                {"label": "Reddit", "url": f"https://www.reddit.com/user/{value}"},
                {"label": "X/Twitter", "url": f"https://x.com/search?q={encoded}"},
                {"label": "Instagram", "url": f"https://www.instagram.com/{value}"},
                {"label": "TikTok", "url": f"https://www.tiktok.com/@{value}"},
            ]
        )
    elif entity_type == "organization":
        links.append({"label": "Google Maps", "url": f"https://www.google.com/maps/search/{encoded}"})
    elif entity_type == "location":
        links.append({"label": "Google Maps", "url": f"https://www.google.com/maps/search/{encoded}"})

    return links
