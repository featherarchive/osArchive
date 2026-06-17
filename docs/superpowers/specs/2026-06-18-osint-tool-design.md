# OSINT Investigation Board Design

## Summary

Build a launchable local OSINT desktop application using Python, Tkinter, and SQLite. The first version is a canvas-first investigation board where users create cases, place entity cards on a board, connect them with relationships, attach notes/sources, and open curated public lookup links. All data is stored locally.

## Goals

- Provide a launchable desktop GUI, not only a command-line tool.
- Store case data locally in SQLite.
- Make the primary workspace a flexible investigation board.
- Support mixed OSINT entity types: person, username, email, phone, domain, IP address, URL, organization, location, note, and source.
- Keep automated collection conservative: curated public lookup links plus lightweight technical metadata helpers for DNS, URL parsing, and HTTP metadata.
- Preserve board state, including entity card positions and relationship lines.

## Non-Goals

- Do not scrape or probe many public websites automatically in v1.
- Do not build a full graph database or advanced layout engine in v1.
- Do not build cloud sync, multi-user collaboration, or remote storage.
- Do not package installers in the first implementation unless the base app is already stable.

## Product Shape

The app opens into a case workspace with three main regions:

- Left sidebar: case list, create/open case actions, entity creation shortcuts, and quick filters.
- Center canvas: draggable entity cards, relationship lines, and board navigation.
- Right inspector: selected entity details, notes, sources, relationship metadata, lookup links, and saved lookup results.

The visual style should feel like an investigation board rather than a plain form app. Tkinter limits how rich the interface can be, so the design should use a dark canvas, compact side panels, colored entity badges, crisp cards, and clear relationship lines instead of heavy animation or web-style effects.

## Core Workflow

1. User creates or opens a case.
2. User adds an entity card to the board.
3. User edits entity fields in the inspector.
4. User connects entities with labeled relationships.
5. User adds notes, source URLs, or file attachment metadata.
6. User opens curated lookup links or runs supported lightweight metadata helpers.
7. User saves findings back to the entity or case.
8. App persists the board and all data in SQLite.

## Entity Types

V1 supports these card types:

- Person
- Username
- Email
- Phone
- Domain
- IP address
- URL
- Organization
- Location
- Note
- Source

Each entity has a title, type, optional description, tags, confidence level, source fields, and board position. Type-specific fields can be stored as JSON until the schema needs more structure.

## Lookup Boundary

V1 uses curated lookup links for common OSINT pivots. Examples include search engine queries, username search links, domain/IP reputation pages, map searches, and social/profile search URLs. These links are generated from the selected entity but opened by the user.

Technical metadata helpers included in v1:

- DNS lookups for domains.
- URL parsing and normalization.
- HTTP status and headers for URLs.

WHOIS is not required for the first implementation. It can be added after the base lookup and storage workflow is stable.

Lookup results are stored as structured records linked to the originating entity. The app should clearly distinguish user-entered notes, generated lookup links, and saved metadata results.

## Data Model

Use SQLite with a small repository layer. Initial tables:

- `cases`: case identity and timestamps.
- `entities`: case-scoped entity records, including type, title, description, tags, confidence, source fields, and custom JSON.
- `board_items`: visual position, size, color, and collapsed/expanded state for each entity on a case board.
- `relationships`: source entity, target entity, label, description, confidence, and timestamps.
- `notes`: freeform notes linked to a case or entity.
- `sources`: source URLs, citations, and source metadata linked to a case or entity.
- `attachments`: local file path metadata, hash fields if available, and linkage to a case or entity.
- `lookup_results`: generated links and saved metadata results linked to an entity.

The schema keeps visual board layout separate from investigation data so future exports and alternate views can reuse the same records.

## Application Structure

Proposed package layout:

- `osint_tool/app.py`: application startup and main window.
- `osint_tool/ui/main_window.py`: top-level Tkinter layout.
- `osint_tool/ui/board.py`: canvas rendering, dragging, selection, and relationship line drawing.
- `osint_tool/ui/inspector.py`: selected entity editor.
- `osint_tool/ui/sidebar.py`: cases and creation controls.
- `osint_tool/data/db.py`: SQLite connection and migrations.
- `osint_tool/data/repositories.py`: persistence operations.
- `osint_tool/models.py`: dataclasses or typed model definitions.
- `osint_tool/lookups/links.py`: curated lookup link generation.
- `osint_tool/lookups/technical.py`: DNS, URL, HTTP, and optional WHOIS helpers.
- `tests/`: focused tests for persistence and lookup generation.

## Error Handling

- Database initialization errors should produce a clear startup error dialog and terminal message.
- Failed metadata lookups should be saved as failed lookup results only when useful, and shown non-destructively in the inspector.
- Invalid entity input should be rejected with inline feedback where feasible.
- Missing local attachment paths should not delete records; they should be marked unavailable.

## Testing

Automated tests should cover:

- Database initialization and migrations.
- Case creation.
- Entity creation, update, and deletion.
- Board position persistence.
- Relationship creation and retrieval.
- Lookup link generation for each supported entity type.
- URL parsing and DNS helper behavior where deterministic.

Manual verification should include launching the GUI, creating a case, adding cards, dragging cards, connecting entities, editing inspector fields, and restarting the app to confirm persistence.

## V1 Lookup Defaults

- Domains and IP addresses: generated links for Google, DuckDuckGo, VirusTotal search pages, Shodan search pages, and DNSDumpster.
- Usernames: generated links for Google, DuckDuckGo, GitHub, Reddit, X/Twitter search, Instagram profile URL, and TikTok profile URL.
- Emails and phones: generated search engine links only.
- URLs: generated search links plus local URL parsing and HTTP status/header metadata.
- Locations and organizations: generated search engine and map search links.
- Installer packaging remains out of scope for v1; the app only needs a reliable local launcher.
