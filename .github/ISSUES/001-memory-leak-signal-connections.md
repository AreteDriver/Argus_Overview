---
title: "[BUG] Memory leak from Qt signal connections never disconnected"
labels: bug, high-priority, memory
---

## Describe the Bug

Dynamic signal connections in `MainWindow` are never disconnected on close. Lambda captures in signal handlers prevent garbage collection, causing memory to grow unbounded in long-running sessions.

## Files Affected

- `src/argus_overview/ui/main_window_v21.py` (lines 482-483, 827-866)

## Root Cause

1. `closeEvent()` does not disconnect dynamic signal connections
2. Lambda captures in signal handlers hold strong references, preventing GC
3. No weak references used for dynamic connections

## Proposed Fix

- Disconnect all dynamic signals in `closeEvent()`
- Replace lambda captures with `functools.partial` where possible
- Use weak references for dynamic connections
- Add `deleteLater()` calls for child widgets in teardown

## Impact

Memory grows unbounded during long sessions. Users who leave Argus running for hours/days will see increasing RAM usage.

## Verification

- Run Argus for extended period, monitor RSS with `ps` or `htop`
- Before/after comparison of memory growth rate
