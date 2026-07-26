"""Explicit state models for capture health and threat.

These enums and dataclasses replace implicit state encoded in widget
attributes (``_last_frame_received_at``, ``_threat_alpha``, etc.) with
readable, testable, serializable models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PreviewHealth(str, Enum):
    """Capture pipeline health for a single preview."""

    INITIALIZING = "initializing"
    LIVE = "live"
    STATIC = "static"
    STALE = "stale"
    PAUSED = "paused"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class ThreatLevel(str, Enum):
    """Intel threat severity."""

    UNKNOWN = "unknown"
    CLEAR = "clear"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"


@dataclass(frozen=True)
class PreviewState:
    """Complete observable state of a single preview card.

    Attributes:
        health: Current capture health.
        threat: Current threat severity.
        character_name: Name of the character in this window.
        system: Current EVE system (may be None if unknown).
        last_capture_at: When the last frame arrived.
        last_frame_change_at: When the frame last differed from prior.
        threat_reported_at: When the current threat was first observed.
        threat_system: System where the threat was reported.
        threat_distance_jumps: Jumps from character to threat system.
        error_message: Human-readable error if health is ERROR.
    """

    health: PreviewHealth
    threat: ThreatLevel
    character_name: str
    system: str | None = None
    last_capture_at: datetime | None = None
    last_frame_change_at: datetime | None = None
    threat_reported_at: datetime | None = None
    threat_system: str | None = None
    threat_distance_jumps: int | None = None
    error_message: str | None = None

    def is_live(self) -> bool:
        """True when the preview is receiving fresh frames."""
        return self.health in (PreviewHealth.LIVE, PreviewHealth.STATIC)

    def has_active_threat(self) -> bool:
        """True when a threat is known and not merely unknown/clear."""
        return self.threat in (ThreatLevel.WARNING, ThreatLevel.DANGER, ThreatLevel.CRITICAL)
