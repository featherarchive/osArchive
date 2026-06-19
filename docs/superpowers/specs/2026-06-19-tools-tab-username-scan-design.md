# Tools Tab Username Scan Design

## Summary

Add a controlled Tools tab to the local OSINT desktop app. The tab starts with a "Choose Tool" launcher, then switches to a terminal-style run screen for a Sherlock-style username scan. The app prefers the real `sherlock` command when it is installed and falls back to a small built-in username checker when Sherlock is unavailable.

## Goals

- Add a top-level tab layout with `Board` and `Tools`.
- Keep the existing board workflow intact.
- Provide a terminal-like tool runner screen without exposing arbitrary shell access.
- Add one first tool: `Username Scan`.
- Prefer real Sherlock CLI execution when `sherlock` is available on `PATH`.
- Provide a built-in fallback checker against a small curated set of public profile/search URLs.
- Stream tool output into the UI as timestamped terminal-style lines.
- Store completed scan output as case-level tool runs.

## Non-Goals

- Do not add raw command entry or an unrestricted embedded shell.
- Do not add port scanners, DNS brute force, service fingerprinting, or other active recon tools.
- Do not package Sherlock with the application in this slice.
- Do not attempt to support every Sherlock output format in v1.
- Do not create matched profile entities automatically in v1.

## Product Behavior

The main window uses a top-level `ttk.Notebook`:

- `Board` tab contains the existing sidebar, canvas board, and inspector.
- `Tools` tab contains the new tool launcher and terminal-style runner.

The Tools tab starts on a simple launcher view:

- Header: `Choose Tool`
- Tool option: `Username Scan`
- Short status text describing whether Sherlock is detected.

When the user selects `Username Scan`, the tab shows a run form:

- Username input.
- Run button.
- Stop button for an active subprocess.
- Back button to return to the tool chooser.
- Terminal output area using a dark `Text` widget.

When the user clicks Run:

1. The app validates that the username is non-empty and contains no whitespace.
2. The app checks for `sherlock` on `PATH`.
3. If Sherlock exists, the app runs it as a subprocess with a controlled argument list.
4. If Sherlock does not exist, the app runs the built-in fallback scanner.
5. Output is appended to the terminal pane while the tool runs.
6. At completion, the app stores a case-level tool run.

## Sherlock Mode

Sherlock mode uses `shutil.which("sherlock")` to detect the command. The app constructs the command as a list, not a shell string:

```text
sherlock <username> --print-found
```

The subprocess runner streams stdout and stderr line by line into the UI. The app never accepts arbitrary command text from the user.

The saved lookup result records:

- Tool name: `sherlock`
- Target username.
- Exit code.
- Full captured output.
- Start and finish timestamps.

## Fallback Mode

Fallback mode checks a curated set of profile/search URLs for the username:

- GitHub profile URL.
- Reddit user URL.
- Instagram profile URL.
- TikTok profile URL.
- X/Twitter search URL.

The fallback scanner performs simple HTTP requests with a timeout and user-agent string. It records each result as:

- `found`: HTTP status suggests a profile exists.
- `missing`: HTTP status suggests no profile exists.
- `unknown`: request failed, timed out, redirected ambiguously, or the platform blocks the check.

The fallback is intentionally small and conservative. It is a usability fallback, not a replacement for Sherlock.

## Storage

The current schema already has `lookup_results` linked to an entity. This feature also needs case-level tool run storage because a username scan may start from the Tools tab before an entity exists.

Add a `tool_runs` table:

- `id`
- `case_id`
- `tool_name`
- `target`
- `mode`
- `status`
- `exit_code`
- `output`
- `result_json`
- `started_at`
- `finished_at`

The app saves each completed username scan to `tool_runs`. Entity-linked `lookup_results` records are out of scope for this slice.

## Application Structure

Add focused modules:

- `osint_tool/tools/registry.py`: available tool metadata and detection.
- `osint_tool/tools/runner.py`: subprocess runner with streaming output callbacks.
- `osint_tool/tools/username_scan.py`: Sherlock command construction and fallback scanner.
- `osint_tool/ui/tools_tab.py`: Tkinter Tools tab UI, launcher view, run form, and terminal output.

Modify existing modules:

- `osint_tool/ui/main_window.py`: add `ttk.Notebook`; put existing board layout into the Board tab; add Tools tab.
- `osint_tool/data/db.py`: add `tool_runs` table migration.
- `osint_tool/data/repositories.py`: add create/list tool run methods.

## Error Handling

- Empty or invalid usernames show inline terminal output and do not start a run.
- Missing Sherlock automatically uses fallback mode.
- Subprocess startup failures are shown in terminal output and stored as failed tool runs.
- Stop button terminates an active subprocess and stores status `stopped`.
- Network errors in fallback mode become `unknown` results, not fatal errors.

## Testing

Automated tests cover:

- Sherlock detection when `shutil.which` returns a path or `None`.
- Sherlock command construction.
- Fallback URL generation and result classification using mocked HTTP responses.
- Tool run persistence in SQLite.
- Subprocess runner behavior using a small Python command that prints deterministic output.
- Tools tab import smoke test without creating a Tk window.

Manual verification covers:

- Launch app.
- Open Tools tab.
- Run Username Scan with Sherlock unavailable and confirm fallback output appears.
- Install/enable a fake Sherlock command in `PATH` and confirm Sherlock mode is selected.
- Confirm completed runs are stored in SQLite.
