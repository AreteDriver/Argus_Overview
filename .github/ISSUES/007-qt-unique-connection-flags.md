---
title: "[REFACTOR] Add UniqueConnection flags to signal connections"
labels: enhancement, low-priority, code-quality
---

## Description

Signal connections across UI files lack `Qt.UniqueConnection` flags, allowing potential duplicate connections if setup methods are called multiple times.

## Files Affected

- All UI files with signal connections

## Proposed Fix

Add `Qt.ConnectionType.UniqueConnection` to signal `.connect()` calls where applicable.

## Verification

- Grep for `.connect(` calls, audit each for uniqueness needs
- Run action registry audit after changes
