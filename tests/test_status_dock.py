"""Tests for the character status dock (PR2)."""

from unittest.mock import MagicMock

from argus_overview.intel.parser import ThreatLevel
from argus_overview.ui.status_dock import (
    CharacterChip,
    StatusDock,
    _initials,
    accent_for,
)

# =============================================================================
# Helpers
# =============================================================================


class TestInitials:
    def test_single_word(self):
        assert _initials("Solo") == "SO"

    def test_two_words(self):
        assert _initials("Foo Bar") == "FB"

    def test_underscores(self):
        assert _initials("foo_bar") == "FB"

    def test_empty(self):
        assert _initials("") == "?"

    def test_three_words_uses_first_and_last(self):
        assert _initials("Alice Beta Gamma") == "AG"


class TestAccentFor:
    def test_deterministic(self):
        assert accent_for("Pilot1").rgb() == accent_for("Pilot1").rgb()

    def test_different_names_likely_differ(self):
        # Not guaranteed but extremely probable across the small palette
        names = ["A", "B", "C", "D", "E", "F", "G", "H"]
        seen = {accent_for(n).rgb() for n in names}
        # At least 3 different accents in 8 names is a generous lower bound
        assert len(seen) >= 3


# =============================================================================
# CharacterChip
# =============================================================================


class TestCharacterChip:
    def test_init_sets_basic_state(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            assert chip.window_id == "0xABC"
            assert chip.character_name == "TestPilot"
            assert chip._system is None
            assert chip._threat_level is None
        finally:
            chip.deleteLater()

    def test_set_system_updates_label(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            chip.set_system("HED-GP")
            assert chip._system == "HED-GP"
            assert chip._system_label.text() == "HED-GP"
        finally:
            chip.deleteLater()

    def test_set_system_none_uses_dash(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            chip.set_system("HED-GP")
            chip.set_system(None)
            assert chip._system_label.text() == "—"
        finally:
            chip.deleteLater()

    def test_set_threat_state_stores_level(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            chip.set_threat_state(ThreatLevel.WARNING, "HED-GP")
            assert chip._threat_level == ThreatLevel.WARNING
            assert chip._threat_alpha == 1.0
            assert chip._system == "HED-GP"
        finally:
            chip.deleteLater()

    def test_set_threat_state_clear_resets(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            chip.set_threat_state(ThreatLevel.DANGER, "Jita")
            chip.set_threat_state(ThreatLevel.CLEAR)
            assert chip._threat_level is None
            assert chip._threat_alpha == 0.0
        finally:
            chip.deleteLater()

    def test_set_threat_state_none_resets(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            chip.set_threat_state(ThreatLevel.DANGER, "Jita")
            chip.set_threat_state(None)
            assert chip._threat_level is None
        finally:
            chip.deleteLater()

    def test_set_threat_state_alpha_clamped(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            chip.set_threat_state(ThreatLevel.WARNING, "HED-GP", alpha=2.5)
            assert chip._threat_alpha == 1.0
            chip.set_threat_state(ThreatLevel.WARNING, "HED-GP", alpha=-0.5)
            assert chip._threat_alpha == 0.0
        finally:
            chip.deleteLater()

    def test_click_emits_window_id(self, qapp):
        from PySide6.QtCore import QPoint, Qt
        from PySide6.QtGui import QMouseEvent

        chip = CharacterChip("0xABC", "TestPilot")
        try:
            received: list[str] = []
            chip.clicked.connect(received.append)
            event = QMouseEvent(
                QMouseEvent.Type.MouseButtonPress,
                QPoint(5, 5),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            chip.mousePressEvent(event)
            assert received == ["0xABC"]
        finally:
            chip.deleteLater()

    def test_right_click_does_not_emit(self, qapp):
        from PySide6.QtCore import QPoint, Qt
        from PySide6.QtGui import QMouseEvent

        chip = CharacterChip("0xABC", "TestPilot")
        try:
            received: list[str] = []
            chip.clicked.connect(received.append)
            event = QMouseEvent(
                QMouseEvent.Type.MouseButtonPress,
                QPoint(5, 5),
                Qt.MouseButton.RightButton,
                Qt.MouseButton.RightButton,
                Qt.KeyboardModifier.NoModifier,
            )
            chip.mousePressEvent(event)
            assert received == []
        finally:
            chip.deleteLater()

    def test_paint_event_no_threat_does_not_crash(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            chip.resize(200, 40)
            chip.repaint()
        finally:
            chip.deleteLater()

    def test_paint_event_with_threat_does_not_crash(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            chip.resize(200, 40)
            chip.set_threat_state(ThreatLevel.CRITICAL, "Jita")
            chip.repaint()
        finally:
            chip.deleteLater()

    def test_tooltip_includes_system_and_threat(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            chip.set_system("HED-GP")
            chip.set_threat_state(ThreatLevel.WARNING, "HED-GP")
            tip = chip.toolTip()
            assert "TestPilot" in tip
            assert "HED-GP" in tip
            assert "warning" in tip
        finally:
            chip.deleteLater()


# =============================================================================
# StatusDock
# =============================================================================


class TestStatusDock:
    def test_init_empty(self, qapp):
        dock = StatusDock()
        try:
            assert dock.chip_count() == 0
        finally:
            dock.deleteLater()

    def test_add_chip(self, qapp):
        dock = StatusDock()
        try:
            chip = dock.add_chip("0x1", "Alice")
            assert chip is not None
            assert dock.chip_count() == 1
            assert dock.has_chip("0x1")
        finally:
            dock.deleteLater()

    def test_add_chip_duplicate_returns_none(self, qapp):
        dock = StatusDock()
        try:
            dock.add_chip("0x1", "Alice")
            dup = dock.add_chip("0x1", "Alice")
            assert dup is None
            assert dock.chip_count() == 1
        finally:
            dock.deleteLater()

    def test_remove_chip(self, qapp):
        dock = StatusDock()
        try:
            dock.add_chip("0x1", "Alice")
            dock.add_chip("0x2", "Bob")
            assert dock.remove_chip("0x1") is True
            assert dock.chip_count() == 1
            assert not dock.has_chip("0x1")
            assert dock.has_chip("0x2")
        finally:
            dock.deleteLater()

    def test_remove_chip_missing_returns_false(self, qapp):
        dock = StatusDock()
        try:
            assert dock.remove_chip("nope") is False
        finally:
            dock.deleteLater()

    def test_clear_removes_all(self, qapp):
        dock = StatusDock()
        try:
            for i in range(5):
                dock.add_chip(f"0x{i}", f"Pilot{i}")
            dock.clear()
            assert dock.chip_count() == 0
        finally:
            dock.deleteLater()

    def test_set_threat_state_fans_to_all_chips(self, qapp):
        dock = StatusDock()
        try:
            dock.add_chip("0x1", "Alice")
            dock.add_chip("0x2", "Bob")
            count = dock.set_threat_state(ThreatLevel.DANGER, "HED-GP")
            assert count == 2
            for chip in dock._chips.values():
                assert chip._threat_level == ThreatLevel.DANGER
                assert chip._system == "HED-GP"
        finally:
            dock.deleteLater()

    def test_set_threat_state_clear(self, qapp):
        dock = StatusDock()
        try:
            dock.add_chip("0x1", "Alice")
            dock.set_threat_state(ThreatLevel.DANGER, "Jita")
            dock.set_threat_state(ThreatLevel.CLEAR)
            for chip in dock._chips.values():
                assert chip._threat_level is None
        finally:
            dock.deleteLater()

    def test_set_chip_system_updates_one_chip(self, qapp):
        dock = StatusDock()
        try:
            dock.add_chip("0x1", "Alice")
            dock.add_chip("0x2", "Bob")
            assert dock.set_chip_system("0x1", "HED-GP") is True
            assert dock._chips["0x1"]._system == "HED-GP"
            assert dock._chips["0x2"]._system is None
        finally:
            dock.deleteLater()

    def test_set_chip_system_unknown_returns_false(self, qapp):
        dock = StatusDock()
        try:
            assert dock.set_chip_system("nope", "Jita") is False
        finally:
            dock.deleteLater()

    def test_chip_clicked_signal_propagates(self, qapp):
        dock = StatusDock()
        try:
            received: list[str] = []
            dock.chip_clicked.connect(received.append)
            chip = dock.add_chip("0xABC", "Alice")
            chip.clicked.emit("0xABC")
            assert received == ["0xABC"]
        finally:
            dock.deleteLater()

    def test_sync_from_window_ids_adds_and_removes(self, qapp):
        dock = StatusDock()
        try:
            dock.add_chip("0x1", "Alice")
            dock.add_chip("0x2", "Bob")
            added, removed = dock.sync_from_window_ids({"0x2": "Bob", "0x3": "Carol"})
            assert added == ["0x3"]
            assert removed == ["0x1"]
            assert dock.has_chip("0x2") and dock.has_chip("0x3")
            assert not dock.has_chip("0x1")
        finally:
            dock.deleteLater()

    def test_sync_from_window_ids_empty_clears(self, qapp):
        dock = StatusDock()
        try:
            dock.add_chip("0x1", "Alice")
            added, removed = dock.sync_from_window_ids({})
            assert added == []
            assert removed == ["0x1"]
            assert dock.chip_count() == 0
        finally:
            dock.deleteLater()


# =============================================================================
# MainWindowV21 wiring — dock receives threat fan-out
# =============================================================================


class TestMainWindowV21StatusDockFanout:
    def test_visual_border_alert_calls_dock_set_threat_state(self):
        from argus_overview.intel.alerts import AlertType
        from argus_overview.intel.parser import IntelReport, ThreatLevel
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MainWindowV21.__new__(MainWindowV21)
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.status_dock = MagicMock()
        window.system_tray = MagicMock()

        report = IntelReport(
            system="HED-GP",
            threat_level=ThreatLevel.DANGER,
            hostile_count=2,
            ship_types=[],
            player_names=[],
            raw_message="hostiles HED-GP",
        )

        window._on_intel_alert(report, AlertType.VISUAL_BORDER)

        window.main_tab.status_dock.set_threat_state.assert_called_once_with(
            ThreatLevel.DANGER, "HED-GP"
        )

    def test_audio_alert_does_not_touch_dock(self):
        from argus_overview.intel.alerts import AlertType
        from argus_overview.intel.parser import IntelReport, ThreatLevel
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MainWindowV21.__new__(MainWindowV21)
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.status_dock = MagicMock()
        window.system_tray = MagicMock()

        report = IntelReport(
            system="HED-GP",
            threat_level=ThreatLevel.WARNING,
            hostile_count=1,
            ship_types=[],
            player_names=[],
            raw_message="neut",
        )

        window._on_intel_alert(report, AlertType.AUDIO)

        window.main_tab.status_dock.set_threat_state.assert_not_called()

    def test_dock_optional_does_not_crash_when_missing(self):
        from argus_overview.intel.alerts import AlertType
        from argus_overview.intel.parser import IntelReport, ThreatLevel
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MainWindowV21.__new__(MainWindowV21)
        window.main_tab = MagicMock(spec=["window_manager"])
        window.main_tab.window_manager = MagicMock()
        window.system_tray = MagicMock()

        report = IntelReport(
            system="HED-GP",
            threat_level=ThreatLevel.DANGER,
            hostile_count=2,
            ship_types=[],
            player_names=[],
            raw_message="hostiles",
        )

        # Should not raise even though main_tab has no status_dock attr
        window._on_intel_alert(report, AlertType.VISUAL_BORDER)
        window.main_tab.window_manager.apply_threat_state.assert_called_once()


# =============================================================================
# Distance badge (PR7)
# =============================================================================


class TestCharacterChipDistanceBadge:
    """+Nj badge state on the chip."""

    def test_default_distance_is_none(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            assert chip._threat_distance is None
        finally:
            chip.deleteLater()

    def test_distance_stored_when_positive(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            chip.set_threat_state(ThreatLevel.WARNING, "HED-GP", alpha=0.5, distance=2)
            assert chip._threat_distance == 2
        finally:
            chip.deleteLater()

    def test_zero_distance_treated_as_none(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            # Same-system case: caller passes distance=0; chip stores None
            chip.set_threat_state(ThreatLevel.DANGER, "HED-GP", alpha=1.0, distance=0)
            assert chip._threat_distance is None
        finally:
            chip.deleteLater()

    def test_clear_resets_distance(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            chip.set_threat_state(ThreatLevel.WARNING, "HED-GP", alpha=0.5, distance=2)
            chip.set_threat_state(ThreatLevel.CLEAR)
            assert chip._threat_distance is None
        finally:
            chip.deleteLater()

    def test_paint_with_distance_does_not_crash(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            chip.resize(200, 40)
            chip.set_threat_state(ThreatLevel.WARNING, "HED-GP", alpha=0.5, distance=1)
            chip.repaint()
        finally:
            chip.deleteLater()

    def test_paint_with_no_distance_does_not_crash(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            chip.resize(200, 40)
            chip.set_threat_state(ThreatLevel.DANGER, "HED-GP", alpha=1.0)
            chip.repaint()
        finally:
            chip.deleteLater()

    def test_tooltip_includes_distance(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            chip.set_system("Jita")
            chip.set_threat_state(ThreatLevel.WARNING, "HED-GP", alpha=0.5, distance=2)
            tip = chip.toolTip()
            assert "2j away" in tip
        finally:
            chip.deleteLater()

    def test_tooltip_omits_distance_for_same_system(self, qapp):
        chip = CharacterChip("0xABC", "TestPilot")
        try:
            chip.set_system("HED-GP")
            chip.set_threat_state(ThreatLevel.DANGER, "HED-GP", alpha=1.0)
            tip = chip.toolTip()
            assert "j away" not in tip
        finally:
            chip.deleteLater()


class TestStatusDockPassesDistanceToChip:
    """Dock fan-out queries calculator.distance and passes it to chips."""

    def _make_calc(self, distance: int | None):
        calc = MagicMock()
        calc.distance.return_value = distance
        return calc

    def test_adjacent_chip_receives_distance(self, qapp):
        from argus_overview.ui.status_dock import StatusDock

        dock = StatusDock()
        try:
            dock.set_jump_calculator(self._make_calc(distance=1), max_jumps=2)
            dock.add_chip("0x1", "Alice")
            dock.set_character_system("Alice", "Jita")

            dock.set_threat_state(ThreatLevel.DANGER, "HED-GP")

            assert dock._chips["0x1"]._threat_distance == 1
        finally:
            dock.deleteLater()

    def test_same_system_chip_has_no_distance(self, qapp):
        from argus_overview.ui.status_dock import StatusDock

        dock = StatusDock()
        try:
            dock.set_jump_calculator(self._make_calc(distance=0), max_jumps=2)
            dock.add_chip("0x1", "Alice")
            dock.set_character_system("Alice", "HED-GP")

            dock.set_threat_state(ThreatLevel.DANGER, "HED-GP")

            assert dock._chips["0x1"]._threat_distance is None
        finally:
            dock.deleteLater()

    def test_unknown_chip_system_has_no_distance(self, qapp):
        """Graceful fallback: unknown chip tints at full alpha, no badge."""
        from argus_overview.ui.status_dock import StatusDock

        dock = StatusDock()
        try:
            dock.set_jump_calculator(self._make_calc(distance=99), max_jumps=2)
            dock.add_chip("0x1", "Alice")
            # No set_character_system → chip._system stays None

            dock.set_threat_state(ThreatLevel.DANGER, "HED-GP")

            assert dock._chips["0x1"]._threat_distance is None
            # Calculator should not have been queried at all (alpha=1.0 path)
        finally:
            dock.deleteLater()

    def test_calculator_error_swallowed(self, qapp):
        from argus_overview.ui.status_dock import StatusDock

        dock = StatusDock()
        try:
            calc = MagicMock()
            calc.distance.side_effect = ValueError("graph corrupt")
            dock.set_jump_calculator(calc, max_jumps=2)
            dock.add_chip("0x1", "Alice")
            dock.set_character_system("Alice", "Jita")

            # Force smart-filter branch by stubbing resolve_tint? No — just
            # rely on real resolve_tint: it would call calculator.distance
            # too. Either way, the dock should not raise.
            dock.set_threat_state(ThreatLevel.DANGER, "HED-GP")

            # Chip threat state may or may not be set depending on which
            # call raised, but the dock must not have crashed.
            assert "0x1" in dock._chips
        finally:
            dock.deleteLater()
