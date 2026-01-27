---
title: "[REFACTOR] Consolidate duplicate alert detection methods"
labels: enhancement, medium-priority, code-quality
---

## Description

`_detect_red_flash()` and `_detect_red_flash_fast()` in `alert_detector.py` (lines 118-188) are nearly identical, creating maintenance burden and risk of divergent bugs.

## Files Affected

- `src/argus_overview/core/alert_detector.py`

## Proposed Fix

Consolidate into a single method with a `fast: bool = False` parameter (or similar) that controls the accuracy/speed tradeoff.

## Verification

- Existing alert detection tests pass
- Both fast and standard detection paths still function correctly
