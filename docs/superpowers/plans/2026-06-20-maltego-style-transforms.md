# Maltego-Style Transforms Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Maltego-style transforms, automatic result nodes, graph layout controls, and node/status polish to the local OSINT board.

**Architecture:** Add pure transform and layout helpers with tests first. Wire them into `MainWindow` through right-click menu actions, persisting transform outputs as entities, relationships, and lookup results. Keep long-running tool execution outside the transform parsing code so tests do not invoke network tools.

**Tech Stack:** Python 3.14, Tkinter Canvas, SQLite, pytest, local `archive`/Sherlock command, local WhatsMyName JSON.

---

### Task 1: Transform Models and Parsers

**Files:**
- Create: `osint_tool/transforms/__init__.py`
- Create: `osint_tool/transforms/core.py`
- Create: `osint_tool/transforms/username.py`
- Create: `tests/test_transforms_username.py`

- [x] Add failing tests for WhatsMyName candidate URL generation from fixture site data.
- [x] Add failing tests for Sherlock found-output parsing.
- [x] Implement `TransformNode`, `TransformRun`, `build_whatsmyname_candidates`, and `parse_sherlock_found_urls`.
- [x] Run `pytest tests/test_transforms_username.py -q`.

### Task 2: Technical Transforms

**Files:**
- Create: `osint_tool/transforms/technical.py`
- Create: `tests/test_transforms_technical.py`

- [x] Add failing tests for converting DNS addresses into IP result nodes.
- [x] Add failing tests for converting HTTP status/header results into note result nodes.
- [x] Implement technical transform helpers using existing lookup output shapes.
- [x] Run `pytest tests/test_transforms_technical.py -q`.

### Task 3: Graph Layout and Collapse Helpers

**Files:**
- Modify: `osint_tool/ui/graph_layout.py`
- Modify: `tests/test_graph_layout.py`

- [x] Add failing tests for radial neighbor layout around a selected node.
- [x] Add failing tests for auto-arrange positions.
- [x] Implement `radial_positions` and `auto_arrange_positions`.
- [x] Run `pytest tests/test_graph_layout.py -q`.

### Task 4: Repository Support for Transform Application

**Files:**
- Modify: `osint_tool/data/repositories.py`
- Modify: `tests/test_repositories.py`

- [x] Add failing tests for finding an existing entity by type/title in a case.
- [x] Add failing tests for updating board item collapsed state.
- [x] Implement `find_entity`, `set_board_collapsed`, and `list_lookup_results_for_case`.
- [x] Run `pytest tests/test_repositories.py -q`.

### Task 5: Main Window Transform Workflow

**Files:**
- Modify: `osint_tool/ui/main_window.py`
- Modify: `osint_tool/ui/board.py`

- [x] Add right-click transform menu entries by entity type.
- [x] Apply transform nodes as entities and relationships around the source node.
- [x] Save transform run summaries into lookup results.
- [x] Add auto-arrange, radial layout, and collapse/expand actions.
- [x] Render status badges from entity custom metadata.

### Task 6: Inspector Transform History

**Files:**
- Modify: `osint_tool/ui/inspector.py`

- [x] Show recent lookup/transform results for the selected entity.
- [x] Keep existing lookup-link buttons available.

### Task 7: Verification

**Files:**
- Test: `tests/`

- [x] Run `pytest -q`.
- [x] Run `python -m py_compile osint_tool/ui/board.py osint_tool/ui/main_window.py osint_tool/ui/inspector.py osint_tool/transforms/core.py osint_tool/transforms/username.py osint_tool/transforms/technical.py`.
- [x] Restart the app if it is currently running.
