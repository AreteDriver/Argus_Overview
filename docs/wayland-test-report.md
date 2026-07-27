# Wayland POC Real-Hardware Validation Report

**Date**: 2026-03-13
**Tester**: Claude (automated validation)
**Argus_Overview version**: 3.2.0

## System Information

| Property | Value |
|----------|-------|
| Distro | Ubuntu 24.04.4 LTS |
| Kernel | 6.17.0-14-generic |
| GPU | AMD Radeon RX 7900 XT/XTX/M (Navi 31) |
| Display Server | X11 (`XDG_SESSION_TYPE=x11`) |
| DISPLAY | `:0` |
| WAYLAND_DISPLAY | unset |

### Tool Availability

| Tool | Path | Installed |
|------|------|-----------|
| grim | `/usr/bin/grim` | Yes |
| wlr-randr | — | No |
| swaymsg | — | No |
| hyprctl | — | No |

---

## Test Results

### Test 1: grim Capture on X11

**Command**: `grim -g "0,0 100x100" /tmp/test_grim.png`
**Result**: FAILED (expected)

```
Exit code: 1
Stderr: failed to create display
File: NOT created
```

**Analysis**: grim requires a Wayland compositor with the `wlr-screencopy-unstable-v1` protocol. On a pure X11 session, grim cannot connect to any Wayland display, so it fails with "failed to create display." This is the correct and expected behavior — grim is a Wayland-only tool. The `WindowCaptureWayland._capture_grim()` method handles this gracefully by catching the failure and returning `None`.

---

### Test 2: Factory Routing

Tests that `get_window_manager()` returns the correct implementation class based on environment variables.

| Scenario | Environment | Expected Class | Actual Class | Result |
|----------|-------------|----------------|--------------|--------|
| X11 session | `XDG_SESSION_TYPE=x11`, `DISPLAY=:0` | `WindowManagerLinux` | `WindowManagerLinux` | PASS |
| Pure Wayland | `XDG_SESSION_TYPE=wayland`, no `DISPLAY`, `WAYLAND_DISPLAY=wayland-0` | `WindowManagerWayland` | `WindowManagerWayland` | PASS |
| XWayland | `XDG_SESSION_TYPE=wayland`, `DISPLAY=:0` | `WindowManagerLinux` | `WindowManagerLinux` | PASS |

**Analysis**: The routing logic in `_is_pure_wayland()` (via `detect_display_server()`) correctly differentiates between:
- Native X11 → uses X11/xdotool/wmctrl stack (Linux classes)
- Pure Wayland (no DISPLAY) → uses Wayland classes (swaymsg/hyprctl)
- XWayland (Wayland + DISPLAY set) → uses X11 stack since X11 tools work

The singleton cache (`_clear_singleton_cache()`) works correctly for switching between environments.

---

### Test 3: WindowManagerWayland Graceful Degradation

Instantiated `WindowManagerWayland` directly on the X11 system (no Sway/Hyprland running).

| Method | Expected | Actual | Result |
|--------|----------|--------|--------|
| `_compositor` | `"unknown"` | `"unknown"` | PASS |
| `get_window_list()` | `[]` | `[]` | PASS |
| `get_eve_windows()` | `[]` | `[]` | PASS |
| `is_valid_window_id("0x1234")` | `True` | `True` | PASS |
| `is_valid_window_id("")` | `False` | `False` | PASS |

**Analysis**: All methods degrade gracefully. No crashes, no unhandled exceptions. When the compositor is "unknown", `_get_compositor_windows()` logs a warning and returns an empty list. The `is_valid_window_id()` regex correctly validates both Sway integer IDs and Hyprland hex addresses, and rejects empty strings.

---

### Test 4: ScreenManagerWayland Fallback

Instantiated `ScreenManagerWayland` without wlr-randr installed.

| Method | Expected | Actual | Result |
|--------|----------|--------|--------|
| `get_all_monitors()` | `[ScreenGeometry(0, 0, 1920, 1080, True)]` | `[ScreenGeometry(x=0, y=0, width=1920, height=1080, is_primary=True)]` | PASS |
| `get_screen_geometry(0)` | `ScreenGeometry(0, 0, 1920, 1080, True)` | `ScreenGeometry(x=0, y=0, width=1920, height=1080, is_primary=True)` | PASS |

**Analysis**: When `wlr-randr` is not installed, `_query_monitors()` catches the `OSError` and returns an empty list. Both `get_all_monitors()` and `get_screen_geometry()` then fall back to the default 1920x1080 geometry. No crashes.

---

## Summary

| Area | Status | Notes |
|------|--------|-------|
| grim capture | N/A on X11 | Expected failure; needs Wayland compositor |
| Factory routing (X11) | PASS | Correctly returns `WindowManagerLinux` |
| Factory routing (Wayland) | PASS | Correctly returns `WindowManagerWayland` |
| Factory routing (XWayland) | PASS | Correctly falls back to `WindowManagerLinux` |
| WM graceful degradation | PASS | Empty results, no crashes |
| WM ID validation | PASS | Accepts hex/int, rejects empty |
| Screen fallback (no wlr-randr) | PASS | Default 1920x1080 returned |

### What Works

1. **Factory routing** — The `_is_pure_wayland()` detection correctly routes to Wayland or Linux classes based on `XDG_SESSION_TYPE`, `DISPLAY`, and `WAYLAND_DISPLAY`.
2. **Graceful degradation** — All Wayland classes handle missing compositors and tools without crashing. Empty lists and sensible defaults are returned.
3. **Singleton cache** — `_clear_singleton_cache()` properly resets state for environment changes.
4. **ID validation** — The regex pattern `^[0-9a-fA-Fx]+$` correctly handles both Sway integer IDs and Hyprland hex addresses.

### What Doesn't Work (Expected)

1. **grim on X11** — grim requires a Wayland compositor. It cannot capture on X11. This is a tool limitation, not a code bug. The code already handles this with `None` returns.

### What Needs Compositor-Specific Testing

These items could not be validated on this X11 system and require a Sway or Hyprland session:

1. **Window enumeration via swaymsg/hyprctl** — `_get_sway_windows()` and `_get_hyprland_windows()` parse JSON output from compositor tools. Needs real compositor to verify parsing.
2. **grim region capture** — `WindowCaptureWayland._capture_grim()` pipes grim output to PIL. Needs Wayland session to verify image capture pipeline.
3. **Window move/resize/focus** — `move_window()`, `activate_window()`, `minimize_window()`, `restore_window()` all send compositor-specific commands. Need real windows to test.
4. **wlr-randr monitor parsing** — `_parse_wlr_randr_output()` parses multi-line text output. The parser logic looks correct but needs real wlr-randr output to verify all edge cases (multi-monitor, disabled outputs, different refresh rates).
5. **EVE window detection** — `get_eve_windows()` pattern-matches against `^EVE - (.+)$` and `^EVE Online - (.+)$`. Needs EVE running under a Wayland compositor.
6. **Focused window tracking** — `get_focused_window()` walks the Sway tree or queries Hyprland. Needs compositor to verify.

### Recommendations

- Run the same validation script on a Sway VM or container with a headless Wayland compositor (e.g., `cage` or `weston`) to test tool integration.
- Consider adding `wlr-randr` parsing unit tests with canned output strings (no compositor needed).
- The `_parse_wlr_randr_output()` method is a good candidate for pure-function unit tests since it only processes text.
