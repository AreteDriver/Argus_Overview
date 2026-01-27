---
title: "[BUG] Missing JSON schema validation on config file loading"
labels: bug, high-priority, reliability
---

## Describe the Bug

Config files are loaded via `json.load()` without schema validation. Malformed or corrupted config files cause runtime `KeyError`/`TypeError` crashes with no useful error message.

## Files Affected

- `src/argus_overview/core/character_manager.py`
- `src/argus_overview/core/layout_manager.py`

## Proposed Fix

- Add pydantic models or dataclass validators for all config schemas
- Validate on load, provide clear error messages for malformed data
- Fall back to defaults when validation fails (with user notification)
- Add migration support for schema version changes

## Impact

Users who manually edit configs or experience file corruption get mysterious crashes with no recovery path.

## Verification

- Create intentionally malformed config files and verify graceful handling
- Add unit tests for schema validation edge cases
