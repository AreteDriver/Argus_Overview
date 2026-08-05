"""Tests for the CommandIntegrator's contract with MainWindowV21.

These tests exercise the *integration contract* — the integrator's
signal-path calls against the real MainWindow API surface. They are
intentionally written against a hand-built :class:`FakeMainWindow`
that mirrors the real MainWindow's public methods, so the tests
remain fast and X11-free while still pinning which real method the
integrator calls for each operator-initiated action.

If the integrator ever falls back to ``hasattr`` probing for a method
that does not exist on the real MainWindow, the corresponding test
will fail — by design. That is the whole point of this file.
"""
from __future__ import annotations

import pytest
from PySide6.QtCore import QRect
from PySide6.QtWidgets import QWidget

from argus_overview.ui.command.integration import CommandIntegrator


# ---------------------------------------------------------------------------
# FakeMainWindow — the real-MainWindow contract, distilled
# ---------------------------------------------------------------------------
class StubPosition:
    """Records the lock state requested via LayoutManager.

    Mirrors :class:`argus_overview.core.position.Position` behavioural
    surface (one method: set_locked) used by the layout-driven palette
    entries. Notably does NOT expose ``set_locked`` directly on the
    LayoutManager — the integrator must traverse ``position`` to satisfy
    the semantic contract.
    """

    def __init__(self) -> None:
        self.set_locked_calls: list[bool] = []

    def set_locked(self, locked: bool) -> None:
        self.set_locked_calls.append(locked)


class StubLayoutManager:
    """Layout manager fixture."""

    def __init__(self) -> None:
        self.position = StubPosition()
        # Direct set_locked on LayoutManager is the new canonical API.
        self.set_locked_calls: list[bool] = []

    def set_locked(self, locked: bool) -> None:
        # Forward to position registry so the real internal state matches
        # what the integrator's :class:`LayoutManager` wrapper does.
        self.set_locked_calls.append(locked)
        self.position.set_locked(locked)


class StubThemeManager:
    """Theme manager fixture.

    Signature matches the real :meth:`ThemeManager.apply_theme`:
    ``apply_theme(name, app)``. The integrator must pass
    ``QApplication.instance()`` as the second argument.
    """

    def __init__(self) -> None:
        self.apply_theme_calls: list[tuple[str, object]] = []

    def apply_theme(self, name: str, app: object) -> None:
        self.apply_theme_calls.append((name, app))


class StubAutoDiscovery:
    """AutoDiscovery fixture.

    Records ``run_once()`` calls — the public alias now provided on
    the real :class:`AutoDiscovery` class.
    """

    def __init__(self) -> None:
        self.run_once_calls: int = 0

    def run_once(self) -> int:
        self.run_once_calls += 1
        return 0


class StubWindowManager:
    """Window manager fixture — mirrors the real ``main_tab.window_manager``."""

    def __init__(self, windows: dict[str, str] | None = None) -> None:
        self._windows = windows or {}

    def known_windows(self) -> dict[str, str]:
        return dict(self._windows)


class StubMainTab:
    """MainTab fixture — exposes ``window_manager`` and nothing else."""

    def __init__(self, windows: dict[str, str] | None = None) -> None:
        self.window_manager = StubWindowManager(windows)


class FakeMainWindow(QWidget):
    """Minimal MainWindow stand-in with the surface CommandIntegrator uses.

    Every attribute here corresponds to a real method or property on
    :class:`MainWindowV21`. Tests assert that the integrator calls the
    real method (not a defensive fallback) by checking the corresponding
    stub's recorded calls.

    Inherits from ``QWidget`` so the integrator can attach a
    ``QShortcut`` and pass it as the ``QDialog`` parent for the
    CommandPalette — matching the real MainWindow's QWidget base.
    """

    def __init__(self, windows: dict[str, str] | None = None) -> None:
        super().__init__()
        self.layout_manager = StubLayoutManager()
        self.theme_manager = StubThemeManager()
        self.auto_discovery = StubAutoDiscovery()
        self.main_tab = StubMainTab(windows)
        self.system_status_bar = _StubSystemStatusBar()
        self._activate_window_calls: list[str] = []
        self.show_layout_chooser_calls: int = 0
        # Used by the palette's "Refresh window list" entry — the
        # FakeMainWindow records whether the integrator plumbed it through.
        self._geometry_for_palette = (100, 100, 800, 600)

    def activate_window(self, window_id: str) -> None:
        """Public alias for the real :meth:`MainWindowV21._activate_window`."""
        self._activate_window_calls.append(window_id)

    def show_layout_chooser(self) -> None:
        """Public method provided by the real :class:`MainWindowV21`."""
        self.show_layout_chooser_calls += 1

    def geometry(self) -> QRect:
        """Return a sentinel QRect — the integrator only uses its center."""
        return QRect(*self._geometry_for_palette)


class _StubSystemStatusBar:
    """Minimal subsystem status bar with the real private dict surface."""

    def __init__(self) -> None:
        self._status = {"capture": "healthy", "hotkeys": "healthy"}
        self._detail = {"capture": "ok", "hotkeys": "ok"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_integrator_with_fake(fake: FakeMainWindow) -> CommandIntegrator:
    """Build a wired integrator backed by a FakeMainWindow."""
    integrator = CommandIntegrator(fake)
    integrator.attach()
    return integrator


# ---------------------------------------------------------------------------
# Contract tests
# ---------------------------------------------------------------------------
class TestActivateWindow:
    """The integrator's focus path must call the real activate_window API."""

    def test_pilot_focus_calls_activate_window(self) -> None:
        fake = FakeMainWindow()
        integrator = _make_integrator_with_fake(fake)

        integrator.command().pilot_focus_requested.emit("wid_42")

        assert fake._activate_window_calls == ["wid_42"]

    def test_pilot_focus_records_ops_event(self) -> None:
        fake = FakeMainWindow(windows={"wid_42": "Eris Vale"})
        integrator = _make_integrator_with_fake(fake)
        # Seed the rail so the focus name comes from the card, not the id.
        integrator._mirror_main_tab_characters()

        integrator.command().pilot_focus_requested.emit("wid_42")

        ops = integrator.command().ops_timeline()._entries
        assert any("Focused Eris Vale" in e.label for e in ops)

    def test_grid_focus_also_calls_activate_window(self) -> None:
        """TacticalGrid pilot_focus_requested must also flow through."""
        fake = FakeMainWindow()
        integrator = _make_integrator_with_fake(fake)

        integrator.command().grid_holder().pilot_focus_requested.emit("wid_99")

        # The grid signal is wired to the same focus handler, so the
        # window is activated with the id once (the handler is invoked
        # once per signal emit).
        assert "wid_99" in fake._activate_window_calls


class TestLayoutChooser:
    """The Layout ▾ button on the header must open the real chooser."""

    def test_layout_chooser_calls_real_method(self) -> None:
        fake = FakeMainWindow()
        integrator = _make_integrator_with_fake(fake)

        integrator.command().layout_chooser_requested.emit()

        assert fake.show_layout_chooser_calls == 1

    def test_layout_chooser_records_ops_event(self) -> None:
        fake = FakeMainWindow()
        integrator = _make_integrator_with_fake(fake)

        integrator.command().layout_chooser_requested.emit()

        ops = integrator.command().ops_timeline()._entries
        assert any("Layout chooser" in e.label for e in ops)


class TestPaletteEntries:
    """Palette entries must hit the real MainWindow surfaces."""

    def _trigger_palette_entry(self, integrator: CommandIntegrator, entry_id: str) -> None:
        """Find and execute the palette entry by id."""
        palette = integrator.palette()
        assert palette is not None, "palette must exist after first focus"
        for entry in palette._entries:
            if entry.id == entry_id:
                # Bypass UI list — call the handler directly.
                entry.handler()
                return
        raise AssertionError(f"Palette entry {entry_id} not found")

    def test_refresh_window_list_calls_auto_discovery_run_once(self) -> None:
        fake = FakeMainWindow()
        integrator = _make_integrator_with_fake(fake)
        # open the palette once so entries are wired
        integrator.command().palette_requested.emit()

        self._trigger_palette_entry(integrator, "system::refresh")

        assert fake.auto_discovery.run_once_calls == 1

    def test_lock_windows_forwards_to_layout_manager(self) -> None:
        fake = FakeMainWindow()
        integrator = _make_integrator_with_fake(fake)
        integrator.command().palette_requested.emit()

        self._trigger_palette_entry(integrator, "system::lock")

        # The integrator must use the canonical LayoutManager.set_locked,
        # which delegates to the position registry.
        assert fake.layout_manager.set_locked_calls == [True]
        assert fake.layout_manager.position.set_locked_calls == [True]

    def test_unlock_windows_forwards_to_layout_manager(self) -> None:
        fake = FakeMainWindow()
        integrator = _make_integrator_with_fake(fake)
        integrator.command().palette_requested.emit()

        self._trigger_palette_entry(integrator, "system::unlock")

        assert fake.layout_manager.set_locked_calls == [False]
        assert fake.layout_manager.position.set_locked_calls == [False]

    def test_theme_entry_passes_qapplication(self) -> None:
        fake = FakeMainWindow()
        integrator = _make_integrator_with_fake(fake)
        integrator.command().palette_requested.emit()

        self._trigger_palette_entry(integrator, "theme::dark")

        assert len(fake.theme_manager.apply_theme_calls) == 1
        name, app = fake.theme_manager.apply_theme_calls[0]
        assert name == "dark"
        # Second argument must be the QApplication instance, not None.
        from PySide6.QtWidgets import QApplication
        assert isinstance(app, QApplication)


class TestSubsystemSeeding:
    """Subsystem health must be seeded from the real status bar."""

    def test_seed_uses_system_status_bar_state(self) -> None:
        fake = FakeMainWindow()
        # Pre-populate the status bar with a custom state.
        fake.system_status_bar._status["capture"] = "degraded"
        fake.system_status_bar._detail["capture"] = "throttled"

        integrator = _make_integrator_with_fake(fake)

        truth = integrator.command().truth()
        cap_cell = truth._cells["capture"]
        assert cap_cell._status == "degraded"
        assert "throttled" in cap_cell._detail

    def test_seed_falls_back_to_defaults_when_no_status_bar(self) -> None:
        """When the main window has no status bar, default to healthy.

        Exercises the no-existing-status-bar branch so the integrator
        doesn't crash when the bar is None (smoke test only).
        """

        class _NoBarWindow(FakeMainWindow):
            def __init__(self) -> None:
                super().__init__()
                self.system_status_bar = None

        integrator = _make_integrator_with_fake(_NoBarWindow())
        truth = integrator.command().truth()
        # All five subsystems default to healthy.
        for key in ("capture", "hotkeys", "discovery", "intel", "location"):
            assert truth._cells[key]._status == "healthy"


class TestCharacterMirror:
    """The rail/grid must reflect the main_tab's known windows."""

    def test_mirror_creates_rail_and_grid_cards(self) -> None:
        fake = FakeMainWindow(
            windows={"wid_a": "Pilot Alpha", "wid_b": "Pilot Bravo"},
        )
        integrator = _make_integrator_with_fake(fake)

        rail = integrator.command().fleet_rail()
        grid = integrator.command().grid_holder()

        assert rail.card_count() == 2
        assert grid.card_count() == 2
        assert rail.card_for("wid_a").character_name() == "Pilot Alpha"
        assert grid.card_for("wid_b").character_name() == "Pilot Bravo"

    def test_mirror_idempotent_on_repeated_calls(self) -> None:
        fake = FakeMainWindow(windows={"wid_a": "Pilot Alpha"})
        integrator = _make_integrator_with_fake(fake)

        # The integrator calls _mirror_main_tab_characters once during
        # attach(); calling it again should not duplicate cards.
        integrator._mirror_main_tab_characters()

        assert integrator.command().fleet_rail().card_count() == 1
        assert integrator.command().grid_holder().card_count() == 1


class TestUnconditionalAttachment:
    """The integrator must be defensive at the boundary, not in the body."""

    def test_attach_is_idempotent(self) -> None:
        fake = FakeMainWindow()
        integrator = CommandIntegrator(fake)
        first = integrator.attach()
        second = integrator.attach()
        assert first is second


@pytest.fixture
def app(qapp):
    return qapp
