---
title: "[BUG] Missing input validation in import_from_eve_sync()"
labels: bug, medium-priority, reliability
---

## Describe the Bug

No validation of `eve_char` attributes before access in `import_from_eve_sync()`. Malformed data causes attribute errors.

## Files Affected

- `src/argus_overview/core/character_manager.py`

## Proposed Fix

- Validate required attributes exist before access
- Provide clear error messages for missing/malformed data
- Skip invalid entries with logged warnings rather than crashing

## Verification

- Test with malformed EVE sync data (missing fields, wrong types)
- Verify graceful handling and logging
