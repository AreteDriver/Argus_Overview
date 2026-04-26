"""
Threat fan-out filter — resolves whether a frame/chip should tint for an
incoming intel alert, and at what intensity.

Used by both WindowManager.apply_threat_state and StatusDock.set_threat_state
so the per-character tinting rules stay symmetric across the preview grid
and the chip strip.

PR6 of the intel-aware UI uplift.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argus_overview.intel.jumps import JumpCalculator


# Alpha falloff: same-system = 1.0, each additional jump multiplies by this
# until we hit the floor or exceed max_jumps.
_PER_JUMP_FALLOFF = 0.5
# Absolute floor for adjacent-system alerts so they remain visible.
_MIN_ADJACENT_ALPHA = 0.4


def resolve_tint(
    known_system: str | None,
    alert_system: str | None,
    jump_calculator: JumpCalculator | None = None,
    max_jumps: int = 0,
) -> tuple[bool, float]:
    """
    Decide whether a frame/chip should tint for an alert, and at what alpha.

    Args:
        known_system: The character's last-known current system. None if
            we don't have a per-character location yet.
        alert_system: The system the intel report refers to. None if intel
            couldn't attribute the report to a system.
        jump_calculator: Optional graph for adjacency lookups. When None,
            only exact matches and the unknown-fallthrough rules apply.
        max_jumps: Maximum jump distance to consider "near". Zero means
            exact-match only (PR5 behavior).

    Returns:
        (should_apply, alpha)
            should_apply: True if the frame/chip should call set_threat_state
            alpha: Initial alpha in [0.0, 1.0]; same-system = 1.0,
                   each jump out scales down by _PER_JUMP_FALLOFF
                   with a floor of _MIN_ADJACENT_ALPHA.
    """
    # No known location → graceful fallback (apply at full intensity).
    if known_system is None:
        return True, 1.0

    # No alert system to match against → fallback (apply at full).
    if not alert_system:
        return True, 1.0

    # Same system → full intensity, no calculator needed.
    if known_system.lower() == alert_system.lower():
        return True, 1.0

    # Need a calculator + non-zero threshold to consider adjacency.
    if jump_calculator is None or max_jumps <= 0:
        return False, 0.0

    distance = jump_calculator.distance(known_system, alert_system)
    if distance is None or distance > max_jumps:
        return False, 0.0

    # Adjacent within threshold — scale alpha down by distance.
    alpha = max(_MIN_ADJACENT_ALPHA, _PER_JUMP_FALLOFF**distance)
    return True, alpha
