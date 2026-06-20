# Maltego-Style Graph View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the existing OSINT board into a Maltego-inspired graph workspace with better relationship rendering and node actions.

**Architecture:** Keep the Tkinter/SQLite app structure. Add pure geometry helpers for testable graph calculations, then use them from `BoardView`; keep persistence in `Repository` unchanged except for using existing relationship APIs.

**Tech Stack:** Python 3.11+, Tkinter Canvas, SQLite, pytest.

---

### Task 1: Testable Graph Geometry

**Files:**
- Create: `osint_tool/ui/graph_layout.py`
- Create: `tests/test_graph_layout.py`

- [x] Write failing tests for card centers, zoom clamping, and relationship label positions.
- [x] Implement `card_center`, `clamp_zoom`, and `relationship_label_position`.
- [x] Run `pytest tests/test_graph_layout.py`.

### Task 2: Board Rendering Upgrade

**Files:**
- Modify: `osint_tool/ui/board.py`

- [x] Track selected entity id and selected-source relationship state.
- [x] Render relationships with arrows and centered labels.
- [x] Render selected nodes with a brighter outline.
- [x] Add mouse-wheel zoom and middle-button pan.
- [x] Add node context menu callback support.

### Task 3: Main Window Relationship Workflow

**Files:**
- Modify: `osint_tool/ui/main_window.py`

- [x] Pass selected entity state into `BoardView.render`.
- [x] Add context menu actions for creating a relationship source and linking a selected target.
- [x] Prompt for relationship label and persist via `Repository.create_relationship`.
- [x] Refresh the board and preserve selection after relationship creation.

### Task 4: Verification

**Files:**
- Test: `tests/`

- [x] Run `pytest`.
- [x] Run a short import smoke check for `python -m osint_tool`.
