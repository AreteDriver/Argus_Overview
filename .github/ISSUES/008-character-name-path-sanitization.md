---
title: "[SECURITY] Sanitize character names used in file paths"
labels: bug, low-priority, security
---

## Describe the Bug

Character names are used directly in file operations without sanitization. A name containing `../` could theoretically cause path traversal.

## Files Affected

- `src/argus_overview/core/character_manager.py` (line 311)

## Proposed Fix

- Sanitize names before use in file paths (strip `/`, `..`, null bytes)
- Use `pathlib.Path.is_relative_to()` to validate resolved paths stay within config directory (pattern already used in `layout_manager.py`)

## Risk Assessment

Low probability (names come from EVE API, not direct user input), but defense-in-depth is appropriate.

## Verification

- Unit test with adversarial character names
- Verify file operations stay within expected directories
