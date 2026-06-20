# Maltego-Style Transforms Design

## Goal

Bring the local OSINT board closer to Maltego by adding right-click transforms, automatic result nodes, graph layout controls, and richer node/status presentation.

## Scope

This design builds a local, desktop-safe version of Maltego-style transforms. It uses installed local tools and local datasets where practical:

- Sherlock through the existing `archive` command.
- WhatsMyName through `/home/fthrarchv/.local/share/WhatsMyName/wmn-data.json`.
- SpiderFoot as a launchable external tool for larger scans.
- Existing Python DNS and HTTP helpers for technical transforms.

The first version does not try to reimplement the full Maltego transform marketplace. It keeps transforms explicit, visible, and tied to the selected entity type.

## Architecture

Add a small transform layer under `osint_tool/transforms/`. Transform functions return structured result objects, not UI objects. The main window converts those results into entities, relationships, and saved lookup results through the existing repository.

The Tk UI runs long transforms in background threads and applies database writes back on the main Tk thread. Fast graph layout actions remain synchronous because they only move board items.

## Transforms

Username entities get:

- WhatsMyName candidates: create URL/source nodes from local site templates.
- Sherlock scan: run `archive <username> --print-found --no-color --no-txt --timeout <n> --local`, parse found profile URLs, then create URL/source nodes.

Domain, IP, and URL entities get:

- DNS lookup: resolve hostnames and create IP nodes.
- HTTP headers: fetch status/header metadata and create a note node summarizing status/server signals.
- SpiderFoot launch: open or start SpiderFoot for the selected target, saving a lookup result that records the handoff.

## Graph Controls

Add graph actions to the node menu:

- Auto-arrange all visible nodes in a circle/grid hybrid.
- Radial layout around the selected node, placing directly connected nodes around it.
- Collapse or expand direct result nodes for the selected node in the current view.

Collapse is a view-level behavior first. It should not delete data.

## UI Polish

Cards show a small status badge based on entity metadata:

- `manual`
- `found`
- `candidate`
- `error`
- `tool`

The inspector gains a transform history/results section sourced from existing `lookup_results`. This keeps scan evidence visible after nodes are created.

## Error Handling

Each transform returns either result nodes or an error result. Tool failures should create a saved lookup result with status `error` and a readable message, not crash the app.

Sherlock and SpiderFoot paths are treated as optional at runtime. If a command is unavailable, the UI reports that in transform history.

## Testing

Unit tests cover:

- Transform result shaping.
- WhatsMyName template loading and URL creation from fixture data.
- Sherlock output parsing without running the real command.
- Technical transform conversion for DNS/HTTP helper results.
- Graph layout position calculations.

Repository persistence is covered through existing entity, relationship, and lookup-result tests, with new coverage for transform application if needed.
