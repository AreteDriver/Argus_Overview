"""Typography roles.

Defines font size and weight by semantic role rather than by widget.
The application uses the system UI font (no external font dependency).
Tabular numerals are requested for timers, counts, and distances.
"""

from __future__ import annotations

# Point sizes
WINDOW_TITLE_PT = 14
SECTION_HEADING_PT = 12
PRIMARY_LABEL_PT = 10
SECONDARY_LABEL_PT = 9
BADGE_TEXT_PT = 8
TIMER_NUMERIC_PT = 9

# Weights
WEIGHT_NORMAL = 400
WEIGHT_BOLD = 700

# Optional CSS-style feature string for tabular figures
# Applied via QFont::setStyleHint or QSS where supported.
TABULAR_NUMERALS = "tnum"
