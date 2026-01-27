---
title: "[BUG] X11 subprocess calls fail silently with no retry logic"
labels: bug, medium-priority, reliability
---

## Describe the Bug

Calls to `wmctrl` and `xdotool` via `subprocess` fail silently. No retry logic, no user feedback, no logging of failures.

## Files Affected

- `src/argus_overview/core/window_capture_threaded.py`
- `src/argus_overview/ui/layouts_tab.py`

## Examples

- `_move_window()` fails silently without user feedback
- No handling for transient X11 failures (e.g., window not yet mapped)
- No retry mechanism for intermittent failures

## Proposed Fix

- Add retry with exponential backoff (2-3 attempts) for transient X11 failures
- Log failures at WARNING level
- Surface persistent failures to user via status bar or notification
- Validate window IDs before each subprocess call

## Verification

- Simulate X11 failures (e.g., invalid window IDs) and verify recovery
- Check logs for appropriate warning messages
