"""Tests for intel/threat_filter.resolve_tint helper (PR6)."""

from unittest.mock import MagicMock

from argus_overview.intel.threat_filter import resolve_tint


class TestResolveTintExplicitFlush:
    """Cases where the helper falls through to apply at full alpha."""

    def test_unknown_character_falls_through_full(self):
        should, alpha = resolve_tint(known_system=None, alert_system="HED-GP")
        assert should is True
        assert alpha == 1.0

    def test_no_alert_system_falls_through_full(self):
        should, alpha = resolve_tint(known_system="Jita", alert_system=None)
        assert should is True
        assert alpha == 1.0

    def test_empty_alert_system_falls_through_full(self):
        should, alpha = resolve_tint(known_system="Jita", alert_system="")
        assert should is True
        assert alpha == 1.0


class TestResolveTintExactMatch:
    def test_same_system_full_alpha(self):
        should, alpha = resolve_tint(known_system="HED-GP", alert_system="HED-GP")
        assert should is True
        assert alpha == 1.0

    def test_case_insensitive_match(self):
        should, alpha = resolve_tint(known_system="hed-gp", alert_system="HED-GP")
        assert should is True
        assert alpha == 1.0


class TestResolveTintAdjacency:
    """Cases that need a JumpCalculator + non-zero max_jumps."""

    def test_no_calculator_skips_mismatch(self):
        should, alpha = resolve_tint(
            known_system="Amarr", alert_system="HED-GP", jump_calculator=None
        )
        assert should is False
        assert alpha == 0.0

    def test_zero_max_jumps_skips_mismatch_even_with_calculator(self):
        calc = MagicMock()
        calc.distance.return_value = 1
        should, alpha = resolve_tint(
            known_system="Amarr",
            alert_system="HED-GP",
            jump_calculator=calc,
            max_jumps=0,
        )
        assert should is False
        # Calculator should NOT have been queried — max_jumps=0 short-circuits
        calc.distance.assert_not_called()

    def test_one_jump_within_threshold_uses_falloff_alpha(self):
        calc = MagicMock()
        calc.distance.return_value = 1
        should, alpha = resolve_tint(
            known_system="Amarr",
            alert_system="HED-GP",
            jump_calculator=calc,
            max_jumps=2,
        )
        assert should is True
        # 0.5 ** 1 = 0.5 (above floor 0.4)
        assert alpha == 0.5

    def test_two_jumps_within_threshold_uses_floor_alpha(self):
        calc = MagicMock()
        calc.distance.return_value = 2
        should, alpha = resolve_tint(
            known_system="Amarr",
            alert_system="HED-GP",
            jump_calculator=calc,
            max_jumps=2,
        )
        assert should is True
        # 0.5 ** 2 = 0.25 → clamped to 0.4 floor
        assert alpha == 0.4

    def test_distance_beyond_threshold_skipped(self):
        calc = MagicMock()
        calc.distance.return_value = 3
        should, alpha = resolve_tint(
            known_system="Amarr",
            alert_system="HED-GP",
            jump_calculator=calc,
            max_jumps=2,
        )
        assert should is False
        assert alpha == 0.0

    def test_unknown_distance_skipped(self):
        """JumpCalculator returns None when graph lookup fails."""
        calc = MagicMock()
        calc.distance.return_value = None
        should, alpha = resolve_tint(
            known_system="Unknown",
            alert_system="HED-GP",
            jump_calculator=calc,
            max_jumps=5,
        )
        assert should is False
        assert alpha == 0.0
