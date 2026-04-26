"""
Shared test helpers for bypassed-`__init__` widgets / managers.

Many tests use `Widget.__new__(Widget)` and `patch.object(Widget, "__init__")`
to test individual methods without spinning up the full Qt object graph.
That path skips attribute initialization, so any production code that
references `self._x` on a bypassed instance raises `AttributeError`.

Rather than litter production code with `getattr(self, "_x", default)`
to paper over the test pattern, these helpers seed the minimum state
each method under test needs. Production code stays clean; tests own
their own setup.
"""

from __future__ import annotations

from collections import deque
from unittest.mock import MagicMock


def seed_preview_widget(widget) -> None:
    """Initialize the v3.2.0 attributes a bypassed-init WindowPreviewWidget
    needs to survive update_frame, paintEvent, and threat-state methods."""
    widget._replay_buffer = deque(maxlen=6)
    widget._replay_last_sample_ms = 0
    widget._replay_strip = None
    widget._replay_view_index = None


def seed_main_tab(tab) -> None:
    """Seed bypassed-init MainTab attributes needed by _on_window_removed
    and other lifecycle methods."""
    tab._focus_window_id = None
    tab.status_dock = MagicMock()


def seed_window_manager(manager) -> None:
    """Seed bypassed-init WindowManager attributes needed by
    apply_threat_state and the smart fan-out / jumps-from filter."""
    manager._character_systems = {}
    manager._jump_calculator = None
    manager._jump_max = 0
