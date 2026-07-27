# Argus Overview Roadmap

**Project**: Argus Overview — EVE Online desktop multi-boxing / window-preview tool  
**Classification**: Flagship  
**Version**: 3.2.0  
**Last updated**: 2026-06-18  
**Next review**: 2026-07-18  

---

## Current State

- Shipping v3.2.0 with 2,495 tests, 96%+ coverage
- Mature PySide6 codebase with Windows, Linux (X11/Wayland) support
- Full `intel/` subsystem for chat-log parsing and threat detection
- v6 aspirational artifacts **archived** (no longer misleading)
- Truth baseline: 7/7 passing ✅
- `ux-ui-overhaul` design-system migration merged

---

## Milestones

### Phase 1: Documentation Sync (Q3 2026) — ✅ COMPLETE 2026-07-26
- [x] Update `docs/ARCHITECTURE.md` — fix package name to `argus_overview`, add `intel/` module, add Wayland/Windows platforms
- [x] Update `docs/USER_GUIDE.md` to v3.2 — add Intel tab, threat-chrome, focus mode, replay strip, Wayland notes
- [x] Remove stale `esi/` directory remnant
- [x] Verify `docs/SMOKE_TEST_v3.2.0.md` is still current
- [x] Run truth baseline — 7/7 passing

### Phase 2: ESI Integration Decision (Q3 2026)
- [ ] Evaluate whether ESI integration is still a priority
- [ ] If yes: design minimal ESI scope, create ADR
- [x] If no: `esi/` directory removed (2026-07-26); document final decision in ADR

### Phase 2b: Runtime Validation (Q3 2026)
- [ ] Run `docs/RUNTIME_VALIDATION_v3.2.0.md` manual protocol with real EVE clients
- [ ] Close 10/10 Release Gate findings
- [ ] Document P2/P3 conscious deferrals with rationale

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

1. **Run runtime validation protocol** — `docs/RUNTIME_VALIDATION_v3.2.0.md` with real EVE clients (2-4 hours, requires manual testing)
2. **ESI Integration Decision** — write ADR: ESI deprioritized vs minimal scope (1 hour)
3. **Wayland compatibility validation** — test on wlroots compositor with real capture (2-3 hours)
4. **Windows build pipeline validation** — verify CI produces working installer (1-2 hours)

---

## Blockers

- None. Docs-only work.

## Definition of Done (Phase 1) — ✅ COMPLETE

- [x] Truth baseline passes all checks (7/7)
- [x] `docs/ARCHITECTURE.md` describes actual v3.2 codebase
- [x] `docs/USER_GUIDE.md` covers all shipped features
- [x] `docs/RUNTIME_VALIDATION_v3.2.0.md` exists with manual protocol
- [x] `esi/` dead code removed
