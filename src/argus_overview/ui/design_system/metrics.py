"""Layout and component metrics.

Radii and control heights are standardized so buttons, inputs, and cards
feel like they belong to the same family.
"""

from __future__ import annotations

# Border radii
RADIUS_CONTROL = 4   # Buttons, inputs, badges
RADIUS_CARD = 6      # Preview cards, chips
RADIUS_PANEL = 8     # Panels, dialogs

# Control heights
CONTROL_HEIGHT_SMALL = 28   # Compact toolbar buttons
CONTROL_HEIGHT = 34         # Standard buttons
CONTROL_HEIGHT_LARGE = 40   # Primary CTAs

# Preview card constraints (operational minimums)
PREVIEW_MIN_WIDTH = 180
PREVIEW_MIN_HEIGHT = 135
PREVIEW_MAX_WIDTH = 600
PREVIEW_MAX_HEIGHT = 450
