---
title: "[PERF] UI lag from missing debounce and inefficient widget rebuilds"
labels: enhancement, medium-priority, performance
---

## Description

Several UI operations cause lag with large datasets due to missing rate limiting and inefficient widget updates.

## Files Affected

- `src/argus_overview/ui/characters_teams_tab.py`
- `src/argus_overview/ui/layouts_tab.py`

## Issues

1. **No debouncing on `_populate_character_list()`** — called on every change without rate limiting
2. **Full ComboBox rebuild in `_refresh_groups()`** — entire widget rebuilt each call instead of incremental update
3. **Aggressive subprocess timeout** — 1-second timeout fails on slow systems

## Proposed Fix

1. Add 100-200ms `QTimer` debounce on population calls
2. Use `QStandardItemModel` for incremental ComboBox updates
3. Make subprocess timeout configurable (2-3s default)

## Verification

- Profile UI with 20+ characters, measure frame times before/after
- Test on slower hardware or VM to verify timeout improvements
