"""Tests for CharacterLocationTracker (PR4: per-character system tracking)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from argus_overview.intel.character_location import (
    CharacterLocationTracker,
    find_eve_chat_log_directory,
)

# Header block as EVE writes it, plus an initial Channel-changed line.
_HEADER_TEMPLATE = (
    "﻿"  # BOM stripped by utf-16-le decoding errors=ignore is fine
    "---------------------------------------------------------------\r\n"
    "  Channel ID:    Local\r\n"
    "  Channel Name:  Local\r\n"
    "  Listener:      {listener}\r\n"
    "  Session Started: 2024.01.15 14:30:00\r\n"
    "---------------------------------------------------------------\r\n"
)


def _write_local_log(
    directory: Path,
    listener: str,
    lines: list[str] | None = None,
    suffix: str = "20240115_143000",
) -> Path:
    """Write a UTF-16-LE Local log file with header + provided lines."""
    content = _HEADER_TEMPLATE.format(listener=listener)
    if lines:
        content += "\r\n".join(lines) + "\r\n"
    path = directory / f"Local_{suffix}.txt"
    # Use 'utf-16' (with BOM) to match real EVE files; tracker uses utf-16-le
    # with errors='ignore' which handles either.
    path.write_bytes(content.encode("utf-16-le"))
    return path


def _append_local_log(path: Path, lines: list[str]) -> None:
    """Append UTF-16-LE-encoded lines to an existing log file."""
    addition = ("\r\n".join(lines) + "\r\n").encode("utf-16-le")
    with open(path, "ab") as f:
        f.write(addition)


# =============================================================================
# Helpers
# =============================================================================


class TestFindEveChatLogDirectory:
    def test_returns_first_existing(self, tmp_path):
        # Manually patch Path.home to a directory layout where a candidate exists.
        fake_home = tmp_path / "home"
        chatlogs = fake_home / "Documents" / "EVE" / "logs" / "Chatlogs"
        chatlogs.mkdir(parents=True)
        with patch("argus_overview.intel.character_location.Path.home", return_value=fake_home):
            result = find_eve_chat_log_directory()
        assert result == chatlogs

    def test_returns_none_when_no_candidates_exist(self, tmp_path):
        fake_home = tmp_path / "no-eve"
        fake_home.mkdir()
        with patch("argus_overview.intel.character_location.Path.home", return_value=fake_home):
            result = find_eve_chat_log_directory()
        assert result is None


# =============================================================================
# Tracker — initial state
# =============================================================================


class TestCharacterLocationTrackerInit:
    def test_initial_state_empty(self, qapp, tmp_path):
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        try:
            assert tracker.get_all_locations() == {}
            assert tracker.get_system("Anyone") is None
            assert tracker.is_running() is False
        finally:
            tracker.deleteLater()

    def test_poll_interval_clamped(self, qapp, tmp_path):
        tracker = CharacterLocationTracker(log_directory=tmp_path, poll_interval_ms=10)
        try:
            assert tracker.poll_interval_ms == 250
        finally:
            tracker.deleteLater()


# =============================================================================
# Tracker — header + line parsing
# =============================================================================


class TestCharacterLocationTrackerParsing:
    def test_listener_extracted_from_header(self, qapp, tmp_path):
        path = _write_local_log(tmp_path, "TestPilot")
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        try:
            listener = tracker._read_listener(path)
            assert listener == "TestPilot"
        finally:
            tracker.deleteLater()

    def test_listener_returns_none_for_missing_header(self, qapp, tmp_path):
        path = tmp_path / "Local_20240115_140000.txt"
        path.write_bytes("just chat data\r\n".encode("utf-16-le"))
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        try:
            assert tracker._read_listener(path) is None
        finally:
            tracker.deleteLater()

    def test_listener_with_special_characters(self, qapp, tmp_path):
        path = _write_local_log(tmp_path, "Pilot O'Connor-Smith")
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        try:
            assert tracker._read_listener(path) == "Pilot O'Connor-Smith"
        finally:
            tracker.deleteLater()

    def test_channel_changed_emits_signal(self, qapp, tmp_path):
        path = _write_local_log(tmp_path, "Alice")
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        received: list[tuple[str, str]] = []
        tracker.character_system_changed.connect(lambda c, s: received.append((c, s)))
        try:
            # First scan establishes the file at end-of-file: no events.
            tracker._poll()
            assert received == []

            _append_local_log(
                path,
                ["[ 2024.01.15 14:31:00 ] EVE System > Channel changed to Local : Jita"],
            )
            tracker._poll()
            assert received == [("Alice", "Jita")]
        finally:
            tracker.deleteLater()

    def test_channel_changed_dedupes_same_system(self, qapp, tmp_path):
        path = _write_local_log(tmp_path, "Alice")
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        received: list[tuple[str, str]] = []
        tracker.character_system_changed.connect(lambda c, s: received.append((c, s)))
        try:
            tracker._poll()
            _append_local_log(
                path,
                [
                    "[ 2024.01.15 14:31:00 ] EVE System > Channel changed to Local : Jita",
                    "[ 2024.01.15 14:32:00 ] EVE System > Channel changed to Local : Jita",
                ],
            )
            tracker._poll()
            assert received == [("Alice", "Jita")]
        finally:
            tracker.deleteLater()

    def test_channel_changed_emits_on_real_change(self, qapp, tmp_path):
        path = _write_local_log(tmp_path, "Alice")
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        received: list[tuple[str, str]] = []
        tracker.character_system_changed.connect(lambda c, s: received.append((c, s)))
        try:
            tracker._poll()
            _append_local_log(
                path,
                ["[ 2024.01.15 14:31:00 ] EVE System > Channel changed to Local : Jita"],
            )
            tracker._poll()
            _append_local_log(
                path,
                ["[ 2024.01.15 14:33:00 ] EVE System > Channel changed to Local : Amarr"],
            )
            tracker._poll()
            assert received == [("Alice", "Jita"), ("Alice", "Amarr")]
            assert tracker.get_system("Alice") == "Amarr"
        finally:
            tracker.deleteLater()

    def test_unrelated_lines_ignored(self, qapp, tmp_path):
        path = _write_local_log(tmp_path, "Alice")
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        received: list[tuple[str, str]] = []
        tracker.character_system_changed.connect(lambda c, s: received.append((c, s)))
        try:
            tracker._poll()
            _append_local_log(
                path,
                [
                    "[ 2024.01.15 14:31:00 ] Bob > o7",
                    "[ 2024.01.15 14:31:05 ] Carol > anyone home?",
                ],
            )
            tracker._poll()
            assert received == []
        finally:
            tracker.deleteLater()

    def test_handles_file_truncation(self, qapp, tmp_path):
        path = _write_local_log(tmp_path, "Alice")
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        try:
            tracker._poll()  # Start at end-of-file
            # Truncate the file (simulates rotation/recreation)
            path.write_bytes(_HEADER_TEMPLATE.format(listener="Alice").encode("utf-16-le"))
            # File is now smaller — tracker should reset cursor
            tracker._poll()
            _append_local_log(
                path,
                ["[ 2024.01.15 15:00:00 ] EVE System > Channel changed to Local : Dodixie"],
            )
            received: list[tuple[str, str]] = []
            tracker.character_system_changed.connect(lambda c, s: received.append((c, s)))
            tracker._poll()
            assert received == [("Alice", "Dodixie")]
        finally:
            tracker.deleteLater()


# =============================================================================
# Tracker — multi-character
# =============================================================================


class TestCharacterLocationTrackerMultiChar:
    def test_two_characters_tracked_independently(self, qapp, tmp_path):
        a = _write_local_log(tmp_path, "Alice", suffix="20240115_140000")
        b = _write_local_log(tmp_path, "Bob", suffix="20240115_140100")
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        try:
            tracker._poll()  # establish cursors
            _append_local_log(
                a,
                ["[ 2024.01.15 14:30:00 ] EVE System > Channel changed to Local : Jita"],
            )
            _append_local_log(
                b,
                ["[ 2024.01.15 14:30:01 ] EVE System > Channel changed to Local : Amarr"],
            )
            tracker._poll()
            assert tracker.get_system("Alice") == "Jita"
            assert tracker.get_system("Bob") == "Amarr"
            assert tracker.get_all_locations() == {"Alice": "Jita", "Bob": "Amarr"}
        finally:
            tracker.deleteLater()

    def test_files_without_listener_skipped(self, qapp, tmp_path):
        # File without a Listener line — tracker should not crash and should
        # not emit anything for it.
        bad = tmp_path / "Local_20240115_140200.txt"
        bad.write_bytes("garbage data\r\n".encode("utf-16-le"))
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        try:
            tracker._poll()
            tracker._poll()
            assert tracker.get_all_locations() == {}
        finally:
            tracker.deleteLater()


# =============================================================================
# Tracker — lifecycle
# =============================================================================


class TestCharacterLocationTrackerLifecycle:
    def test_start_no_directory_idles(self, qapp, tmp_path):
        tracker = CharacterLocationTracker(log_directory=None)
        try:
            with patch(
                "argus_overview.intel.character_location.find_eve_chat_log_directory",
                return_value=None,
            ):
                tracker.start()
            assert tracker.is_running() is False
        finally:
            tracker.deleteLater()

    def test_start_with_directory_runs(self, qapp, tmp_path):
        tracker = CharacterLocationTracker(log_directory=tmp_path, poll_interval_ms=500)
        try:
            tracker.start()
            assert tracker.is_running() is True
            tracker.stop()
            assert tracker.is_running() is False
        finally:
            tracker.deleteLater()

    def test_start_idempotent(self, qapp, tmp_path):
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        try:
            tracker.start()
            tracker.start()  # should not raise or restart
            assert tracker.is_running() is True
            tracker.stop()
        finally:
            tracker.deleteLater()

    def test_stop_idempotent(self, qapp, tmp_path):
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        try:
            tracker.stop()  # never started
            assert tracker.is_running() is False
        finally:
            tracker.deleteLater()


# =============================================================================
# StatusDock.set_character_system
# =============================================================================


class TestStatusDockSetCharacterSystem:
    def test_updates_only_chips_for_named_character(self, qapp):
        from argus_overview.ui.status_dock import StatusDock

        dock = StatusDock()
        try:
            dock.add_chip("0x1", "Alice")
            dock.add_chip("0x2", "Bob")
            dock.add_chip("0x3", "Alice")  # multibox: Alice in two windows

            count = dock.set_character_system("Alice", "Jita")

            assert count == 2
            assert dock._chips["0x1"]._system == "Jita"
            assert dock._chips["0x3"]._system == "Jita"
            assert dock._chips["0x2"]._system is None
        finally:
            dock.deleteLater()

    def test_unknown_character_returns_zero(self, qapp):
        from argus_overview.ui.status_dock import StatusDock

        dock = StatusDock()
        try:
            dock.add_chip("0x1", "Alice")
            count = dock.set_character_system("Nobody", "Jita")
            assert count == 0
        finally:
            dock.deleteLater()


# =============================================================================
# WindowManager.set_character_system
# =============================================================================


class TestWindowManagerSetCharacterSystem:
    def _make_manager(self):
        from argus_overview.ui.main_tab import WindowManager

        manager = WindowManager.__new__(WindowManager)
        manager.preview_frames = {}
        manager._character_systems = {}
        return manager

    def test_set_then_get(self):
        manager = self._make_manager()
        manager.set_character_system("Alice", "Jita")
        assert manager.get_character_system("Alice") == "Jita"

    def test_overwrite(self):
        manager = self._make_manager()
        manager.set_character_system("Alice", "Jita")
        manager.set_character_system("Alice", "Amarr")
        assert manager.get_character_system("Alice") == "Amarr"

    def test_set_none_clears(self):
        manager = self._make_manager()
        manager.set_character_system("Alice", "Jita")
        manager.set_character_system("Alice", None)
        assert manager.get_character_system("Alice") is None

    def test_unknown_character_returns_none(self):
        manager = self._make_manager()
        assert manager.get_character_system("Nobody") is None


# =============================================================================
# MainWindowV21 wiring
# =============================================================================


class TestMainWindowV21CharacterLocationWiring:
    def test_on_character_system_changed_forwards_to_dock_and_manager(self):
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MainWindowV21.__new__(MainWindowV21)
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.status_dock = MagicMock()

        window._on_character_system_changed("Alice", "Jita")

        window.main_tab.window_manager.set_character_system.assert_called_once_with("Alice", "Jita")
        window.main_tab.status_dock.set_character_system.assert_called_once_with("Alice", "Jita")

    def test_on_character_system_changed_no_main_tab_safe(self):
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MainWindowV21.__new__(MainWindowV21)
        # No main_tab set — should not raise
        window._on_character_system_changed("Alice", "Jita")

    def test_on_character_system_changed_dock_optional(self):
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MainWindowV21.__new__(MainWindowV21)
        window.main_tab = MagicMock(spec=["window_manager"])
        window.main_tab.window_manager = MagicMock()

        window._on_character_system_changed("Alice", "Jita")

        window.main_tab.window_manager.set_character_system.assert_called_once()


# =============================================================================
# MainTab._sync_status_dock seeding
# =============================================================================


class TestMainTabSyncStatusDockSeedsSystem:
    def test_sync_seeds_known_systems_into_chips(self):
        from argus_overview.ui.main_tab import MainTab

        tab = MainTab.__new__(MainTab)
        tab.logger = MagicMock()
        tab.window_manager = MagicMock()
        tab.window_manager.preview_frames = {}
        tab.window_manager._character_systems = {"Alice": "Jita", "Bob": "Amarr"}
        tab.status_dock = MagicMock()

        tab._sync_status_dock()

        # Verify both characters were pushed into the dock for seeding
        calls = tab.status_dock.set_character_system.call_args_list
        seeded = {(c.args[0], c.args[1]) for c in calls}
        assert seeded == {("Alice", "Jita"), ("Bob", "Amarr")}


# =============================================================================
# Additional safety: malformed lines
# =============================================================================


@pytest.mark.parametrize(
    "line",
    [
        "",
        "garbage",
        "[ bad timestamp ] EVE System > Channel changed to Local : Jita",
        "[ 2024.01.15 14:31:00 ] EVE System > Some other message",
        "[ 2024.01.15 14:31:00 ] Player > Channel changed to Local : Jita",
    ],
)
def test_channel_changed_regex_rejects_garbage(qapp, tmp_path, line):
    path = _write_local_log(tmp_path, "Alice")
    tracker = CharacterLocationTracker(log_directory=tmp_path)
    received: list[tuple[str, str]] = []
    tracker.character_system_changed.connect(lambda c, s: received.append((c, s)))
    try:
        tracker._poll()
        _append_local_log(path, [line])
        tracker._poll()
        assert received == []
    finally:
        tracker.deleteLater()


class TestCharacterLocationTrackerLogoff:
    """Tests for the on_character_gone slot / character_logged_off signal."""

    def test_on_character_gone_removes_known_character(self, qapp, tmp_path):
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        try:
            tracker._update_location("Pilot1", "Jita")
            tracker.on_character_gone("Pilot1", "win123")
            assert tracker.get_all_locations() == {}
        finally:
            tracker.deleteLater()

    def test_on_character_gone_emits_logged_off_signal(self, qapp, tmp_path):
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        received: list[str] = []
        tracker.character_logged_off.connect(received.append)
        try:
            tracker._update_location("Pilot1", "Jita")
            tracker.on_character_gone("Pilot1", "win123")
            assert received == ["Pilot1"]
        finally:
            tracker.deleteLater()

    def test_on_character_gone_unknown_character_is_noop(self, qapp, tmp_path):
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        received: list[str] = []
        tracker.character_logged_off.connect(received.append)
        try:
            tracker.on_character_gone("GhostPilot", "win999")
            assert received == []
            assert tracker.get_all_locations() == {}
        finally:
            tracker.deleteLater()

    def test_on_character_gone_does_not_clear_file_state(self, qapp, tmp_path):
        path = _write_local_log(tmp_path, "Pilot1")
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        try:
            tracker._poll()  # seeds _file_state for path
            assert path in tracker._file_state
            seeded = tracker._file_state[path]
            tracker._update_location("Pilot1", "Jita")
            tracker.on_character_gone("Pilot1", "win123")
            assert path in tracker._file_state
            assert tracker._file_state[path] is seeded
        finally:
            tracker.deleteLater()

    def test_get_system_returns_none_after_logoff(self, qapp, tmp_path):
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        try:
            tracker._update_location("Pilot1", "Jita")
            tracker.on_character_gone("Pilot1", "win123")
            assert tracker.get_system("Pilot1") is None
        finally:
            tracker.deleteLater()

    def test_relogin_reuses_existing_path(self, qapp, tmp_path):
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        system_changes: list[tuple[str, str]] = []
        logoffs: list[str] = []
        tracker.character_system_changed.connect(lambda c, s: system_changes.append((c, s)))
        tracker.character_logged_off.connect(logoffs.append)
        try:
            tracker._update_location("P", "Jita")
            tracker.on_character_gone("P", "w1")
            tracker._update_location("P", "Amarr")
            assert tracker.get_all_locations() == {"P": "Amarr"}
            assert system_changes == [("P", "Jita"), ("P", "Amarr")]
            assert logoffs == ["P"]
        finally:
            tracker.deleteLater()

    def test_logoff_signal_fires_after_dict_mutation(self, qapp, tmp_path):
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        observed: list[str | None] = []

        def on_logoff(name: str) -> None:
            observed.append(tracker.get_system(name))

        tracker.character_logged_off.connect(on_logoff)
        try:
            tracker._update_location("Pilot1", "Jita")
            tracker.on_character_gone("Pilot1", "win123")
            assert observed == [None]
        finally:
            tracker.deleteLater()

    def test_on_character_gone_empty_name_is_silent_noop(self, qapp, tmp_path):
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        received: list[str] = []
        tracker.character_logged_off.connect(received.append)
        try:
            tracker._update_location("Pilot1", "Jita")
            tracker.on_character_gone("", "w1")
            tracker.on_character_gone("   ", "w1")
            assert received == []
            assert tracker.get_all_locations() == {"Pilot1": "Jita"}
        finally:
            tracker.deleteLater()

    def test_on_character_gone_idempotent(self, qapp, tmp_path):
        tracker = CharacterLocationTracker(log_directory=tmp_path)
        received: list[str] = []
        tracker.character_logged_off.connect(received.append)
        try:
            tracker._update_location("Pilot1", "Jita")
            tracker.on_character_gone("Pilot1", "win123")
            tracker.on_character_gone("Pilot1", "win123")
            assert received == ["Pilot1"]
        finally:
            tracker.deleteLater()

    def test_logoff_latency_under_5ms(self, qapp, tmp_path):
        import time

        tracker = CharacterLocationTracker(log_directory=tmp_path)
        try:
            for i in range(100):
                tracker._update_location(f"P{i}", "Jita")
            durations_ns: list[int] = []
            for i in range(100):
                start = time.perf_counter_ns()
                tracker.on_character_gone(f"P{i}", "w")
                durations_ns.append(time.perf_counter_ns() - start)
            durations_ns.sort()
            p95 = durations_ns[94]
            assert p95 < 5_000_000, f"p95 logoff latency {p95}ns exceeds 5ms budget"
        finally:
            tracker.deleteLater()
