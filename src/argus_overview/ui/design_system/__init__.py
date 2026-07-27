"""Design System — reusable UI tokens and constants for Argus Overview.

Provides a single source of truth for colors, spacing, typography, radii,
and control metrics so that every widget can share a coherent visual
language without hardcoding values.

Example:
    from argus_overview.ui.design_system import colors, spacing
    surface = colors.SURFACE
    pad = spacing.SPACE_3
"""

from argus_overview.ui.design_system import colors, metrics, spacing, states, typography

__all__ = [
    "colors",
    "spacing",
    "typography",
    "metrics",
    "states",
]
