# Argus Overview Project Charter

**Version**: 1.0  
**Date**: 2026-06-18  
**Classification**: Flagship  
**Owner**: AreteDriver  

---

## Purpose

Maintain and evolve **Argus Overview** — a desktop multi-boxing and window-preview tool for EVE Online, providing real-time threat detection via chat-log parsing and streamlined window management across multiple game clients.

## Scope

### In Scope
- PySide6 desktop application (Windows, Linux X11/Wayland)
- Window capture pipeline with crop-based deduplication
- Chat-log parsing and threat chrome overlay
- Intel tab for system monitoring
- Focus mode and replay strip UX

### Out of Scope
- In-game automation (banned by EVE ToS)
- ESI integration (deferred pending decision)
- Mobile or web versions
- General-purpose window manager

## Success Criteria

1. v3.2.0 stable on Windows and Linux
2. Truth baseline passes all documentation checks
3. `docs/ARCHITECTURE.md` and `docs/USER_GUIDE.md` reflect v3.2 reality
4. 2,391 tests maintained with 96%+ coverage
5. No aspirational v6 stubs in production code

## Constraints

- Must comply with EVE Online Terms of Service
- No automation of game inputs
- Read-only from game client (logs, screen capture)
- PySide6 + Pillow dependency stack

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| EVE ToS changes | High | Monitor CCP announcements, design read-only |
| Wayland compatibility gaps | Medium | Platform abstraction layer, X11 fallback |
| Documentation drift | Medium | Truth baseline CI gate |

## Authority

- **Decision maker**: AreteDriver
- **Feature requests**: Personal need-driven only
- **Version bumps**: Semantic versioning, truth baseline must pass

## Definition of Done

- Feature works on Windows and Linux
- Tests added/updated
- Documentation updated to v3.2
- Truth baseline passes
- No ToS violations introduced
