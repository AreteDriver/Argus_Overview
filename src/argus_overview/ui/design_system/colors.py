"""Semantic color tokens.

All colors are named by purpose, not by hue, so that dark/light/high-contrast
theme swaps only need to replace these values. Every token must have a
contrast-safe counterpart for text that appears on top of it.

Verification: run ``python -m argus_overview.ui.design_system.colors``
to print the palette and compute WCAG-like contrast ratios.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Canvas / background
# ---------------------------------------------------------------------------
CANVAS = "#0B0E13"  # Deepest background (app window)
SURFACE = "#11161D"  # Primary card/panel background
SURFACE_RAISED = "#171D26"  # Elevated surface (hover, active)
SURFACE_HOVER = "#1D2530"  # Hover state background

# ---------------------------------------------------------------------------
# Borders
# ---------------------------------------------------------------------------
BORDER_SUBTLE = "#27313D"
BORDER_STRONG = "#3A4655"
BORDER_FOCUS = "#63C7FF"  # Focus ring (also used for keyboard focus)

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------
TEXT_PRIMARY = "#F2F5F7"
TEXT_SECONDARY = "#A5B0BC"
TEXT_MUTED = "#73808D"
TEXT_DISABLED = "#515C67"

# ---------------------------------------------------------------------------
# Semantic status
# ---------------------------------------------------------------------------
HEALTHY = "#4CC38A"
WARNING = "#F0B44D"
CRITICAL = "#F06464"
UNKNOWN = "#8994A0"
INFO = "#5EB3F2"

# ---------------------------------------------------------------------------
# Character identity base pool (deterministic mapping lives in main_tab.py)
# These are the raw accent hues used by character_accent_color().
# ---------------------------------------------------------------------------
ACCENT_POOL: list[tuple[int, int, int]] = [
    (255, 100, 100),
    (100, 255, 100),
    (100, 150, 255),
    (255, 200, 80),
    (220, 120, 220),
    (100, 220, 220),
    (255, 165, 60),
    (170, 130, 255),
]

# ---------------------------------------------------------------------------
# Threat-specific border tints (used by WindowPreviewWidget and CharacterChip)
# ---------------------------------------------------------------------------
THREAT_CLEAR = (0, 200, 100)
THREAT_INFO = (0, 180, 230)
THREAT_WARNING = (255, 170, 0)
THREAT_DANGER = (255, 90, 30)
THREAT_CRITICAL = (255, 40, 40)

THREAT_MAP: dict[str, tuple[int, int, int]] = {
    "clear": THREAT_CLEAR,
    "info": THREAT_INFO,
    "warning": THREAT_WARNING,
    "danger": THREAT_DANGER,
    "critical": THREAT_CRITICAL,
}

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _luminance(rgb: tuple[int, int, int]) -> float:
    """Relative luminance of an sRGB color (simplified)."""
    r, g, b = rgb
    return (r * 299 + g * 587 + b * 114) / 1000


def contrast_ratio(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    """Compute a simplified contrast ratio (higher is better)."""
    lum_fg = _luminance(fg)
    lum_bg = _luminance(bg)
    lighter = max(lum_fg, lum_bg)
    darker = min(lum_fg, lum_bg)
    return (lighter + 0.05) / (darker + 0.05)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert ``#RRGGBB`` to ``(r, g, b)``."""
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def all_semantic_keys() -> list[str]:
    """Return every public semantic color name defined in this module."""
    return [
        "CANVAS",
        "SURFACE",
        "SURFACE_RAISED",
        "SURFACE_HOVER",
        "BORDER_SUBTLE",
        "BORDER_STRONG",
        "BORDER_FOCUS",
        "TEXT_PRIMARY",
        "TEXT_SECONDARY",
        "TEXT_MUTED",
        "TEXT_DISABLED",
        "HEALTHY",
        "WARNING",
        "CRITICAL",
        "UNKNOWN",
        "INFO",
    ]


if __name__ == "__main__":
    # Print palette + rough contrast against SURFACE and CANVAS
    print("Argus Design System — Semantic Colors")
    print("=" * 50)
    for key in all_semantic_keys():
        val = globals()[key]
        rgb = hex_to_rgb(val)
        print(f"{key:20s} {val}  (rgb{rgb})")
        if key.startswith("TEXT_"):
            for bg_name in ("SURFACE", "CANVAS"):
                bg_rgb = hex_to_rgb(globals()[bg_name])
                ratio = contrast_ratio(rgb, bg_rgb)
                print(f"    vs {bg_name:8s} → contrast {ratio:.2f}")
