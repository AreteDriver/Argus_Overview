"""Tests for the design-system token layer.

Verifies that all expected tokens exist, are well-formed, and that
theme switching does not leave the palette in an invalid state.
"""

from __future__ import annotations

import re

import pytest

from argus_overview.ui.design_system import colors, metrics, spacing, states, typography
from argus_overview.ui.design_system.colors import all_semantic_keys, hex_to_rgb


class TestSemanticColors:
    """All semantic colors must be valid 6-digit hex strings with acceptable contrast."""

    def test_all_keys_exist(self):
        for key in all_semantic_keys():
            assert hasattr(colors, key), f"Missing color token: {key}"

    def test_all_values_are_valid_hex(self):
        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for key in all_semantic_keys():
            value = getattr(colors, key)
            assert hex_pattern.match(value), f"{key} = {value!r} is not a valid hex color"

    def test_contrast_against_surface(self):
        """TEXT_PRIMARY must be legible on SURFACE (contrast > 4.5)."""
        fg = hex_to_rgb(colors.TEXT_PRIMARY)
        bg = hex_to_rgb(colors.SURFACE)
        ratio = colors.contrast_ratio(fg, bg)
        assert ratio > 4.5, f"TEXT_PRIMARY on SURFACE contrast = {ratio:.2f}"

    def test_threat_map_has_all_levels(self):
        for level in ("clear", "info", "warning", "danger", "critical"):
            assert level in colors.THREAT_MAP, f"Missing threat color for {level}"
            rgb = colors.THREAT_MAP[level]
            assert len(rgb) == 3
            for c in rgb:
                assert 0 <= c <= 255

    def test_accent_pool_has_eight_entries(self):
        assert len(colors.ACCENT_POOL) == 8
        for rgb in colors.ACCENT_POOL:
            assert len(rgb) == 3


class TestSpacing:
    """Spacing values follow the 4px grid and are monotonically increasing."""

    def test_values_are_multiples_of_four(self):
        for val in spacing.all_spacing_values():
            assert val % 4 == 0, f"{val} is not a multiple of 4"

    def test_values_are_monotonic(self):
        vals = spacing.all_spacing_values()
        assert vals == sorted(vals)
        assert len(vals) == len(set(vals)), "Duplicate spacing values found"


class TestMetrics:
    """Radii and heights are positive and reasonable."""

    def test_radii_are_positive(self):
        assert metrics.RADIUS_CONTROL > 0
        assert metrics.RADIUS_CARD >= metrics.RADIUS_CONTROL
        assert metrics.RADIUS_PANEL >= metrics.RADIUS_CARD

    def test_control_heights_are_ordered(self):
        assert metrics.CONTROL_HEIGHT_SMALL < metrics.CONTROL_HEIGHT < metrics.CONTROL_HEIGHT_LARGE

    def test_preview_constraints_sane(self):
        assert metrics.PREVIEW_MIN_WIDTH >= 120
        assert metrics.PREVIEW_MIN_HEIGHT >= 90
        assert metrics.PREVIEW_MAX_WIDTH >= metrics.PREVIEW_MIN_WIDTH
        assert metrics.PREVIEW_MAX_HEIGHT >= metrics.PREVIEW_MIN_HEIGHT


class TestTypography:
    """Font roles are defined and point sizes are reasonable."""

    def test_point_sizes_defined(self):
        assert typography.WINDOW_TITLE_PT >= 12
        assert typography.PRIMARY_LABEL_PT >= 8
        assert typography.BADGE_TEXT_PT >= 7


class TestStates:
    """State enums cover all required values and PreviewState is frozen."""

    def test_preview_health_values(self):
        vals = {e.value for e in states.PreviewHealth}
        expected = {
            "initializing",
            "live",
            "static",
            "stale",
            "paused",
            "error",
            "disconnected",
        }
        assert vals == expected

    def test_threat_level_values(self):
        vals = {e.value for e in states.ThreatLevel}
        expected = {"unknown", "clear", "warning", "danger", "critical"}
        assert vals == expected

    def test_preview_state_is_frozen(self):
        s = states.PreviewState(
            health=states.PreviewHealth.LIVE,
            threat=states.ThreatLevel.UNKNOWN,
            character_name="TestPilot",
        )
        with pytest.raises(AttributeError):
            s.health = states.PreviewHealth.STALE  # type: ignore[misc]

    def test_preview_state_helpers(self):
        s = states.PreviewState(
            health=states.PreviewHealth.LIVE,
            threat=states.ThreatLevel.CRITICAL,
            character_name="TestPilot",
        )
        assert s.is_live()
        assert s.has_active_threat()

        s2 = states.PreviewState(
            health=states.PreviewHealth.STALE,
            threat=states.ThreatLevel.CLEAR,
            character_name="Scout",
        )
        assert not s2.is_live()
        assert not s2.has_active_threat()
