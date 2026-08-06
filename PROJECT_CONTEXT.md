# Argus Overview — Project Context

**Classification**: Flagship  
**Version**: 3.2.0  
**Owner**: AreteDriver  
**Repository**: https://github.com/AreteDriver/Argus_Overview  
**Branch**: main  
**Last updated**: 2026-06-18  
**Next review**: 2026-07-18  

---

## Technology Stack

- **Language**: Python 3.10+
- **GUI**: PySide6
- **Image**: Pillow
- **Platforms**: Windows, Linux (X11, Wayland)
- **CI**: GitHub Actions, truth baseline

## Key Directories

| Path | Purpose |
|------|---------|
| `argus_overview/` | Main package (was `eve_overview_pro`) |
| `argus_overview/intel/` | Chat-log parsing, threat detection |
| `argus_overview/platform/` | Windows, X11, Wayland capture backends |
| `docs/` | Documentation (needs v3.2 sync) |
| `tests/` | 2,391 tests, 96%+ coverage |

## Current Milestone

Update `docs/ARCHITECTURE.md` and `docs/USER_GUIDE.md` to reflect v3.2 reality.

## Quick Links

- [ROADMAP.md](ROADMAP.md)
- [PROJECT_CHARTER.md](PROJECT_CHARTER.md)
- [CLAUDE.md](CLAUDE.md)
- [README.md](README.md)
