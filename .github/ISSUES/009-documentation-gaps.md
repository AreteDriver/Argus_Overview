---
title: "[DOCS] Add missing architecture and thread-safety documentation"
labels: enhancement, low-priority, documentation
---

## Description

Several documentation gaps make it harder for contributors to understand the codebase:

1. Module-level architecture overviews
2. Thread-safety guarantees and concurrency model
3. Signal parameter documentation (e.g., `Signal(str, list)`)
4. Usage examples for complex features
5. Performance and memory usage notes

## Proposed Work

- Add docstrings to key modules explaining purpose and threading model
- Document which signals are emitted from which threads
- Add a Wayland troubleshooting section to USER_GUIDE.md
- Document performance tuning options

## Files Affected

- `src/argus_overview/core/window_capture_threaded.py`
- `src/argus_overview/ui/main_window_v21.py`
- `docs/USER_GUIDE.md`
