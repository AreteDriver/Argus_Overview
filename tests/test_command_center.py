"""Tests for the Argus Command Center modules.

Covers:
  * Header chrome (brand, status line)
  * Fleet Rail (cards, identity persistence)
  * Attention queue (insertion, acknowledgement)
  * Operations timeline (insertion, eviction)
  * Operational Truth bar (subsystem updates, pulse animation)
  * Command palette (entry filtering, ranking)
  * Command Center shell assembly
"""
from __future__ import annotations

import time

import pytest

from argus_overview.intel.parser import ThreatLevel
from argus_overview.ui.command.attention import (
    AttentionItem,
    AttentionQueue,
    OpsEntry,
    OpsTimeline,
)
from argus_overview.ui.command.fleet_rail import FleetCard, FleetRail
from argus_overview.ui.command.header import (
    BrandMark,
    CommandCenterHeader,
    OperationalStatusLine,
)
from argus_overview.ui.command.operational_truth import OperationalTruthBar
from argus_overview.ui.command.palette import CommandPalette, PaletteEntry
from argus_overview.ui.command.shell import CommandCenterWidget
from argus_overview.ui.command.tactical_grid import TacticalCard, TacticalGrid


@pytest.fixture
def app(qapp):
    return qapp


class TestBrandMark:
    def test_renders_without_crash(self, app):
        w = BrandMark()
        w.resize(220, 48)
        w.show()
        app.processEvents()

    def test_size_hint_non_empty(self, app):
        w = BrandMark()
        hint = w.sizeHint()
        assert hint.width() >= 160


class TestOperationalStatusLine:
    def test_update_state_does_not_crash(self, app):
        w = OperationalStatusLine()
        w.update_state(fleet_count=4, alert_count=2, intel_health="live")
        app.processEvents()

    def test_supports_zero_state(self, app):
        w = OperationalStatusLine()
        w.update_state(fleet_count=0, alert_count=0, intel_health="idle")
        app.processEvents()

    def test_supports_offline(self, app):
        w = OperationalStatusLine()
        w.update_state(fleet_count=2, alert_count=1, intel_health="offline")
        app.processEvents()


class TestCommandCenterHeader:
    def test_construction(self, app):
        header = CommandCenterHeader()
        assert header.layout() is not None
        assert header.height() > 0


class TestFleetCard:
    def test_card_renders(self, app):
        card = FleetCard("w1", "Test Pilot", accent=(180, 100, 220))
        card.show()
        app.processEvents()
        assert card.character_name() == "Test Pilot"

    def test_threat_state_changes_label(self, app):
        card = FleetCard("w1", "Test", accent=(100, 200, 100))
        card.set_threat_state(ThreatLevel.DANGER, system="Jita", alpha=1.0)
        app.processEvents()
        assert "D" in card._threat_badge.text()

    def test_distance_badge_appears(self, app):
        card = FleetCard("w1", "Test", accent=(100, 200, 100))
        card.set_threat_state(ThreatLevel.DANGER, system="Jita",
                              alpha=0.6, distance=3)
        app.processEvents()
        assert "+3j" in card._threat_badge.text()

    def test_threat_clear_resets_badge(self, app):
        card = FleetCard("w1", "Test", accent=(100, 200, 100))
        card.set_threat_state(ThreatLevel.DANGER, system="Jita")
        app.processEvents()
        card.set_threat_state(ThreatLevel.CLEAR)
        app.processEvents()
        assert card._threat_badge.text() == ""

    def test_focus_state_toggles(self, app):
        card = FleetCard("w1", "Test", accent=(100, 200, 100))
        assert card._has_focus is False
        card.set_focused(True)
        assert card._has_focus is True

    def test_stale_system_label(self, app):
        card = FleetCard("w1", "Test", accent=(100, 200, 100))
        card.set_system("Jita")
        card.set_system("Unknown", stale=True)
        app.processEvents()
        assert "Unknown" in card._system_label.text()
        assert "Jita" in card._system_label.text()


class TestFleetRail:
    def test_upsert_creates_card(self, app):
        rail = FleetRail()
        card = rail.upsert_card("w1", "Pilot A", accent=(180, 100, 220))
        assert rail.card_count() == 1
        assert card.character_name() == "Pilot A"

    def test_upsert_idempotent(self, app):
        rail = FleetRail()
        rail.upsert_card("w1", "Pilot A", accent=(180, 100, 220))
        first = rail.card_for("w1")
        rail.upsert_card("w1", "Pilot A", accent=(180, 100, 220))
        second = rail.card_for("w1")
        assert first is second

    def test_remove_card(self, app):
        rail = FleetRail()
        rail.upsert_card("w1", "Pilot A", accent=(180, 100, 220))
        assert rail.remove_card("w1") is True
        assert rail.card_count() == 0

    def test_clear(self, app):
        rail = FleetRail()
        for i in range(3):
            rail.upsert_card(f"w{i}", f"Pilot {i}",
                              accent=(100, 200, 100))
        assert rail.card_count() == 3
        rail.clear()
        assert rail.card_count() == 0

    def test_threat_propagates_to_card(self, app):
        rail = FleetRail()
        rail.upsert_card("w1", "Pilot A", accent=(100, 200, 100))
        rail.set_pilot_threat("w1", ThreatLevel.DANGER, system="Jita", alpha=1.0)
        app.processEvents()
        assert rail.card_for("w1")._threat_level == ThreatLevel.DANGER


class TestAttentionQueue:
    def test_empty_state_renders(self, app):
        q = AttentionQueue()
        q.show()
        app.processEvents()

    def test_add_item_inserts_row(self, app):
        q = AttentionQueue()
        item = AttentionItem(
            id="t1", category="threat", title="Hostile in Jita",
            detail="5 Sabres", severity="critical"
        )
        q.add_item(item)
        app.processEvents()
        assert q.has_active() is True

    def test_acknowledge_removes_active(self, app):
        q = AttentionQueue()
        item = AttentionItem(
            id="t1", category="threat", title="x", severity="warning"
        )
        q.add_item(item)
        q._on_ack("t1")
        app.processEvents()
        assert q.has_active() is False


class TestOpsTimeline:
    def test_empty_renders(self, app):
        t = OpsTimeline()
        t.show()
        app.processEvents()

    def test_entries_evicted_at_max(self, app):
        t = OpsTimeline()
        t.ENTRIES_MAX = 3
        for i in range(5):
            t.add_entry(OpsEntry(timestamp=time.time(),
                                  label=f"Event {i}",
                                  category="layout"))
        app.processEvents()
        assert len(t._entries) <= t.ENTRIES_MAX


class TestOperationalTruthBar:
    def test_construction(self, app):
        bar = OperationalTruthBar()
        assert bar.height() == 30

    def test_subsystem_update(self, app):
        bar = OperationalTruthBar()
        bar.set_subsystem("capture", "healthy", "running")
        assert "CAPTURE" in bar._cells["capture"]._label
        bar.set_subsystem("capture", "unavailable", "pynput missing")
        assert bar._cells["capture"]._status == "unavailable"

    def test_alert_count_zero_hides(self, app):
        bar = OperationalTruthBar()
        bar.set_alert_count(0)
        assert bar._alert_cell.isHidden()

    def test_alert_count_positive_shows(self, app):
        bar = OperationalTruthBar()
        bar.set_alert_count(2)
        assert not bar._alert_cell.isHidden()
        assert "2 ALERTS" in bar._alert_text.text()

    def test_layout_state_text(self, app):
        bar = OperationalTruthBar()
        bar.set_layout_state("PvP", applied_at=time.time())
        assert "LAYOUT" in bar._layout_cell.text()


class TestCommandPalette:
    def _make_palette(self):
        return CommandPalette()

    def test_construction(self, app):
        pal = self._make_palette()
        assert pal.windowTitle() == "Argus // Command Palette"

    def test_score_starts_match_highest(self, app):
        pal = self._make_palette()
        entries = [
            PaletteEntry(id="a", title="Apply PvP Layout", category="layout"),
            PaletteEntry(id="b", title="Theme Dark", category="theme"),
            PaletteEntry(id="c", title="Refresh Windows", category="system"),
        ]
        pal.set_entries(entries)
        pal._refresh_list("pvp")
        first = pal._list.item(0)
        assert first is not None
        assert "a" in first.text() or "PvP" in first.text()

    def test_empty_filter_shows_all(self, app):
        pal = self._make_palette()
        entries = [
            PaletteEntry(id="a", title="X", category="system"),
            PaletteEntry(id="b", title="Y", category="system"),
        ]
        pal.set_entries(entries)
        pal._refresh_list("")
        assert pal._list.count() == 2

    def test_no_matches_shows_placeholder(self, app):
        pal = self._make_palette()
        pal.set_entries([PaletteEntry(id="a", title="X",
                                       category="system")])
        pal._refresh_list("zzzzznotfound")
        first = pal._list.item(0)
        assert "No matches" in first.text()


class TestCommandCenterWidget:
    def test_assembly(self, app):
        cc = CommandCenterWidget()
        cc.resize(1280, 720)
        cc.show()
        app.processEvents()
        assert cc.header() is not None
        assert cc.fleet_rail() is not None
        assert cc.attention() is not None
        assert cc.ops_timeline() is not None
        assert cc.truth() is not None

    def test_layout_structure(self, app):
        """The grid must contain header, rail, grid holder, ops, truth."""
        cc = CommandCenterWidget()
        # Header at row 0
        assert cc.header().parent() is cc or cc.header().parent().parent() is cc
        # Fleet rail accessible
        rail = cc.fleet_rail()
        assert rail.card_count() == 0

    def test_grid_holder_present(self, app):
        cc = CommandCenterWidget()
        assert cc.grid_holder() is not None


class TestTacticalCard:
    def test_card_renders(self, app):
        card = TacticalCard("w1", "Test Pilot", accent=(180, 100, 220))
        card.show()
        app.processEvents()
        assert card.character_name() == "Test Pilot"

    def test_threat_state_sets_chip(self, app):
        card = TacticalCard("w1", "Test", accent=(100, 200, 100))
        card.set_threat_state(ThreatLevel.DANGER, alpha=1.0)
        app.processEvents()
        assert card._threat_chip.text() == "D"

    def test_threat_distance_appears(self, app):
        card = TacticalCard("w1", "Test", accent=(100, 200, 100))
        card.set_threat_state(ThreatLevel.WARNING, alpha=1.0, distance=3)
        app.processEvents()
        assert "+3j" in card._threat_chip.text()

    def test_threat_clear_resets(self, app):
        card = TacticalCard("w1", "Test", accent=(100, 200, 100))
        card.set_threat_state(ThreatLevel.CRITICAL)
        app.processEvents()
        card.set_threat_state(ThreatLevel.CLEAR)
        app.processEvents()
        assert card._threat_chip.text() == ""

    def test_capture_health_label(self, app):
        card = TacticalCard("w1", "Test", accent=(100, 200, 100))
        card.set_capture_health("stale")
        app.processEvents()
        assert card._health_label.text() == "STALE"


class TestTacticalGrid:
    def test_grid_starts_empty(self, app):
        grid = TacticalGrid()
        assert grid.card_count() == 0
        grid.show()
        app.processEvents()

    def test_upsert_creates_card(self, app):
        grid = TacticalGrid()
        card = grid.upsert_card("w1", "Pilot A", accent=(180, 100, 220))
        assert grid.card_count() == 1
        assert card.character_name() == "Pilot A"

    def test_upsert_idempotent(self, app):
        grid = TacticalGrid()
        first = grid.upsert_card("w1", "Pilot A", accent=(180, 100, 220))
        second = grid.upsert_card("w1", "Pilot A", accent=(180, 100, 220))
        assert first is second

    def test_remove_card(self, app):
        grid = TacticalGrid()
        grid.upsert_card("w1", "Pilot A", accent=(180, 100, 220))
        assert grid.remove_card("w1") is True
        assert grid.card_count() == 0

    def test_three_columns_lay_out(self, app):
        grid = TacticalGrid()
        for i in range(7):
            grid.upsert_card(f"w{i}", f"Pilot {i}", accent=(100, 200, 100))
        # Cards exist
        assert grid.card_count() == 7
        # Each card has a parent (laid out)
        for card in grid._cards.values():
            assert card.parent() is grid
        app.processEvents()

    def test_clear_returns_to_empty(self, app):
        grid = TacticalGrid()
        for i in range(3):
            grid.upsert_card(f"w{i}", f"P{i}", accent=(100, 200, 100))
        assert grid.card_count() == 3
        grid.clear()
        assert grid.card_count() == 0


class TestCommandCenterGridIntegration:
    def test_shell_grid_is_tactical_grid(self, app):
        cc = CommandCenterWidget()
        assert isinstance(cc.grid_holder(), TacticalGrid)

    def test_shell_upsert_into_grid(self, app):
        cc = CommandCenterWidget()
        card = cc.grid_holder().upsert_card(
            "w1", "Pilot A", accent=(180, 100, 220)
        )
        assert cc.grid_holder().card_count() == 1
        assert card.character_name() == "Pilot A"
