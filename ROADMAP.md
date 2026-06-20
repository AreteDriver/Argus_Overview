# Argus Overview Roadmap

**Project**: Argus Overview — EVE Online desktop multi-boxing / window-preview tool  
**Classification**: Flagship  
**Version**: 3.2.0  
**Last updated**: 2026-06-18  
**Next review**: 2026-07-18  

---

## Current State

- Shipping v3.2.0 with 2,391 tests, 96%+ coverage
- Mature PySide6 codebase with Windows, Linux (X11/Wayland) support
- Full `intel/` subsystem for chat-log parsing and threat detection
- v6 aspirational artifacts **archived** (no longer misleading)
- Truth baseline: 2/7 passing 🟠

---

## Milestones

### Phase 1: Documentation Sync (Q3 2026)
- [ ] Update `docs/ARCHITECTURE.md` — fix package name to `argus_overview`, add `intel/` module, add Wayland/Windows platforms
- [ ] Update `docs/USER_GUIDE.md` to v3.2 — add Intel tab, threat-chrome, focus mode, replay strip, Wayland notes
- [ ] Remove stale `esi/` directory remnant
- [ ] Verify `docs/SMOKE_TEST_v3.2.0.md` is still current

### Phase 2: ESI Integration Decision (Q3 2026)
- [ ] Evaluate whether ESI integration is still a priority
- [ ] If yes: design minimal ESI scope, create ADR
- [ ] If no: document deprecation, remove `esi/` directory entirely

### Phase 3: Platform Hardening (Q4 2026)
- [ ] Wayland compatibility validation (currently has `platform/wayland.py`)
- [ ] Windows build pipeline validation
- [ ] Performance baseline for capture pipeline (crop-based dedup, bounded queue)

### Phase 4: Feature Polish (Q1 2027)
- [ ] Intel tab UX improvements
- [ ] Threat chrome customization
- [ ] Replay strip enhancements
- [ ] Accessibility audit

---

## Prioritized Next Actions

1. **Fix `docs/ARCHITECTURE.md`** — update to v3.2 reality (2-3 hours)
2. **Update `docs/USER_GUIDE.md`** — bump to v3.2, document Intel tab (4-6 hours)
3. **Remove `esi/` dead code** — delete directory and stale `__pycache__`
4. **Re-run truth baseline** — confirm docs are now accurate

---

## Blockers

- None. Docs-only work.

## Definition of Done (Phase 1)

- Truth baseline passes all checks
- `docs/ARCHITECTURE.md` describes actual v3.2 codebase
- `docs/USER_GUIDE.md` covers all shipped features
