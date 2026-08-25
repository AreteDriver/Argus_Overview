"""Centralized window activation and cycling behavior."""

from __future__ import annotations

import logging
from collections.abc import Callable


class CycleController:
    """Owns activation policy for preview clicks, hotkeys, and cycling."""

    def __init__(self, window_ops, settings_manager):
        self.window_ops = window_ops
        self.settings_manager = settings_manager
        self.logger = logging.getLogger(__name__)

    def _is_valid_window_id(self, window_id: str) -> bool:
        return self.window_ops._window_mgr.is_valid_window_id(window_id)

    def activate_window(self, window_id: str) -> bool:
        """Activate a window and optionally minimize the previously active one."""
        if not self._is_valid_window_id(window_id):
            self.logger.warning("Invalid window ID format: %s", window_id)
            return False

        try:
            auto_minimize = self.settings_manager.get(
                "performance.auto_minimize_inactive",
                False,
            )

            if auto_minimize:
                last_window = self.settings_manager.get_last_activated_window()
                if (
                    last_window
                    and last_window != window_id
                    and self._is_valid_window_id(last_window)
                ):
                    self.window_ops.minimize_window(last_window)
                    self.logger.info("Auto-minimized previous EVE window: %s", last_window)

            self.settings_manager.set_last_activated_window(window_id)
            result = self.window_ops.activate_window(window_id)

            if result:
                self.logger.info("Activated window: %s", window_id)
            else:
                self.logger.warning("Failed to activate window: %s", window_id)

            return bool(result)

        except (OSError, RuntimeError, ValueError) as exc:
            self.logger.error("Failed to activate window %s: %s", window_id, exc)
            return False

    def activate_character(
        self,
        char_name: str,
        window_lookup: Callable[[str], str | None],
    ) -> bool:
        """Resolve a character name to a live window and activate it."""
        window_id = window_lookup(char_name)
        if not window_id:
            self.logger.warning("Character not found: %s", char_name)
            return False
        return self.activate_window(window_id)

    def cycle(
        self,
        members: list[str],
        current_index: int,
        direction: int,
        window_lookup: Callable[[str], str | None],
    ) -> tuple[int, str | None]:
        """Cycle through group members until a live window is activated."""
        if not members:
            self.logger.warning("No members in cycling group")
            return current_index, None

        next_index = current_index

        for _ in range(len(members)):
            next_index = (next_index + direction) % len(members)
            char_name = members[next_index]
            window_id = window_lookup(char_name)

            if not window_id:
                self.logger.warning(
                    "Character '%s' not found in active windows, skipping",
                    char_name,
                )
                continue

            if self.activate_window(window_id):
                self.logger.info(
                    "Cycled to: %s (%d/%d)",
                    char_name,
                    next_index + 1,
                    len(members),
                )
                return next_index, char_name

        self.logger.warning("No active windows found in cycling group")
        return current_index, None
