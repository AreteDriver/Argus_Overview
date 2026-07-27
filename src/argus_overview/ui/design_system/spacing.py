"""Spacing scale.

All spacing values are multiples of 4px so the UI has a rhythmic grid.
Use these instead of ad-hoc pixel values in margins, paddings, and gaps.
"""

from __future__ import annotations

SPACE_1 = 4
SPACE_2 = 8
SPACE_3 = 12
SPACE_4 = 16
SPACE_5 = 24
SPACE_6 = 32
SPACE_7 = 48
SPACE_8 = 64


def all_spacing_values() -> list[int]:
    """Return every spacing token in ascending order."""
    return [SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_5, SPACE_6, SPACE_7, SPACE_8]
