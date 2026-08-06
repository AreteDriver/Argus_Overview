"""Tests for the v3.3 OPS IA tab containers.

Each container is a thin :class:`QWidget` that composes existing
v2.2 tabs into a single top-level tab. Tests pin the splitter
structure so the IA contract is enforced: every container exposes
both inner widgets and the splitter that joins them.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication, QSplitter, QWidget

from argus_overview.ui.tabs import (
    CommandTab,
    FleetTab,
    LayoutsContainer,
    SystemTab,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def app(qapp):
    return qapp


def _stub_widget(name: str = "stub") -> QWidget:
    """Return a real QWidget (not a MagicMock) — splitter children must be
    real widgets or setSizes() short-circuits."""
    w = QWidget()
    w.setObjectName(name)
    return w


# ---------------------------------------------------------------------------
# CommandTab
# ---------------------------------------------------------------------------
class TestCommandTab:
    """The COMMAND tab hosts the Command Center flagship surface."""

    def test_creates_command_center_widget(self, app: QApplication) -> None:
        tab = CommandTab()
        assert tab.command_center is not None
        assert tab.command_center.objectName() == "CommandCenter"

    def test_forwards_command_center_signals(self, app: QApplication) -> None:
        tab = CommandTab()
        captured: list[str] = []

        def _on_palette() -> None:
            captured.append("palette")

        def _on_layout() -> None:
            captured.append("layout")

        tab.palette_requested.connect(_on_palette)
        tab.layout_chooser_requested.connect(_on_layout)

        tab.command_center.palette_requested.emit()
        tab.command_center.layout_chooser_requested.emit()

        assert captured == ["palette", "layout"]

    def test_forwards_pilot_focus_signal(self, app: QApplication) -> None:
        tab = CommandTab()
        seen: list[str] = []

        def _on_focus(wid: str) -> None:
            seen.append(wid)

        tab.pilot_focus_requested.connect(_on_focus)
        tab.command_center.pilot_focus_requested.emit("wid_42")
        assert seen == ["wid_42"]


# ---------------------------------------------------------------------------
# FleetTab — Roster + Intel
# ---------------------------------------------------------------------------
class TestFleetTab:
    """The FLEET tab joins the Roster and Intel inner widgets."""

    def test_holds_both_inner_widgets(self, app: QApplication) -> None:
        roster = _stub_widget("Roster")
        intel = _stub_widget("Intel")
        tab = FleetTab(roster, intel)

        assert tab.characters_tab is roster
        assert tab.intel_tab is intel

    def test_uses_qsplitter(self, app: QApplication) -> None:
        tab = FleetTab(_stub_widget(), _stub_widget())
        assert isinstance(tab.splitter, QSplitter)
        assert tab.splitter.count() == 2

    def test_default_split_is_60_40(self, app: QApplication) -> None:
        """The 60/40 default gives the character/team grid room to breathe."""
        tab = FleetTab(_stub_widget(), _stub_widget())
        sizes = tab.splitter.sizes()
        total = sum(sizes)
        assert total > 0
        # Roster side (60%) should be larger than intel side (40%).
        assert sizes[0] > sizes[1]
        # Ratio should be 3:2.
        ratio = sizes[0] / sizes[1]
        assert 1.4 < ratio < 1.6

    def test_accepts_qwidget_subclasses(self, app: QApplication) -> None:
        """Smoke test: arbitrary QWidget subclasses drop into the splitter."""

        class InnerA(QWidget):
            pass

        class InnerB(QWidget):
            pass

        tab = FleetTab(InnerA(), InnerB())
        assert tab.splitter.count() == 2


# ---------------------------------------------------------------------------
# LayoutsContainer — Layout Presets + Cycle Control
# ---------------------------------------------------------------------------
class TestLayoutsContainer:
    """The LAYOUTS tab joins layout presets and cycle control."""

    def test_holds_both_inner_widgets(self, app: QApplication) -> None:
        presets = _stub_widget("LayoutPresets")
        hotkeys = _stub_widget("Hotkeys")
        tab = LayoutsContainer(presets, hotkeys)

        assert tab.layouts_panel is presets
        assert tab.hotkeys_tab is hotkeys

    def test_uses_qsplitter(self, app: QApplication) -> None:
        tab = LayoutsContainer(_stub_widget(), _stub_widget())
        assert isinstance(tab.splitter, QSplitter)
        assert tab.splitter.count() == 2

    def test_default_split_is_70_30(self, app: QApplication) -> None:
        """The 70/30 default gives the visual grid dominant space."""
        tab = LayoutsContainer(_stub_widget(), _stub_widget())
        sizes = tab.splitter.sizes()
        assert sizes[0] > sizes[1]
        ratio = sizes[0] / sizes[1]
        assert 2.2 < ratio < 2.4


# ---------------------------------------------------------------------------
# SystemTab — Settings + Sync
# ---------------------------------------------------------------------------
class TestSystemTab:
    """The SYSTEM tab joins app settings and EVE folder sync."""

    def test_holds_both_inner_widgets(self, app: QApplication) -> None:
        settings = _stub_widget("Settings")
        sync = _stub_widget("Sync")
        tab = SystemTab(settings, sync)

        assert tab.settings_tab is settings
        assert tab.settings_sync_tab is sync

    def test_uses_qsplitter(self, app: QApplication) -> None:
        tab = SystemTab(_stub_widget(), _stub_widget())
        assert isinstance(tab.splitter, QSplitter)
        assert tab.splitter.count() == 2

    def test_default_split_is_60_40(self, app: QApplication) -> None:
        """Settings takes the larger slice — sync is more occasional."""
        tab = SystemTab(_stub_widget(), _stub_widget())
        sizes = tab.splitter.sizes()
        assert sizes[0] > sizes[1]
        ratio = sizes[0] / sizes[1]
        assert 1.4 < ratio < 1.6


# ---------------------------------------------------------------------------
# Cross-cutting: object names
# ---------------------------------------------------------------------------
class TestContainerObjectNames:
    """Container objectNames are the QA/test selectors for these widgets."""

    @pytest.mark.parametrize(
        "factory,name",
        [
            (lambda: CommandTab(), "CommandTab"),
            (lambda: FleetTab(_stub_widget(), _stub_widget()), "FleetTab"),
            (lambda: LayoutsContainer(_stub_widget(), _stub_widget()), "LayoutsContainer"),
            (lambda: SystemTab(_stub_widget(), _stub_widget()), "SystemTab"),
        ],
    )
    def test_object_name(self, app: QApplication, factory, name: str) -> None:
        widget = factory()
        assert widget.objectName() == name


# ---------------------------------------------------------------------------
# Cross-cutting: splitter is horizontal
# ---------------------------------------------------------------------------
class TestContainerOrientation:
    """All splitters are horizontal — left/right pane pairing."""

    @pytest.mark.parametrize(
        "factory",
        [
            lambda: FleetTab(_stub_widget(), _stub_widget()),
            lambda: LayoutsContainer(_stub_widget(), _stub_widget()),
            lambda: SystemTab(_stub_widget(), _stub_widget()),
        ],
    )
    def test_horizontal_splitter(self, app: QApplication, factory) -> None:
        from PySide6.QtCore import Qt

        widget = factory()
        assert widget.splitter.orientation() == Qt.Orientation.Horizontal


# ---------------------------------------------------------------------------
# Cross-cutting: containers can be constructed with mock inner widgets
# ---------------------------------------------------------------------------
class TestContainersAcceptStubs:
    """Container constructors take any QWidget — they don't reach in."""

    def test_all_containers_accept_stubs(self, app: QApplication) -> None:
        """Smoke test: MagicMock-injected stubs still produce a valid tab."""
        # Real QWidgets rather than MagicMocks — splitter rejects non-widgets.
        stub_a, stub_b = _stub_widget(), _stub_widget()

        c1 = CommandTab()
        c2 = FleetTab(stub_a, stub_b)
        c3 = LayoutsContainer(stub_a, stub_b)
        c4 = SystemTab(stub_a, stub_b)

        for c in (c1, c2, c3, c4):
            assert c is not None
            assert isinstance(c, QWidget)
