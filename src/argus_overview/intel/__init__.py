"""
Intel Channel Parser - EVE Online chat log monitoring and alert system.

This module monitors EVE Online chat logs for intel reports (hostile player
names, system names, threat keywords) and triggers visual and audio alerts.

Components:
    - log_watcher: Monitors EVE chat log files for new messages
    - parser: Parses chat messages for intel content
    - alerts: Dispatches visual and audio alerts
"""

from argus_overview.intel.alerts import AlertConfig, AlertDispatcher, AlertType
from argus_overview.intel.jumps import JumpCalculator
from argus_overview.intel.log_watcher import ChatLogWatcher, ChatMessage
from argus_overview.intel.parser import IntelParser, IntelReport, ThreatLevel
from argus_overview.intel.systems import load_systems

__all__ = [
    "ChatLogWatcher",
    "ChatMessage",
    "IntelParser",
    "IntelReport",
    "JumpCalculator",
    "ThreatLevel",
    "AlertDispatcher",
    "AlertConfig",
    "AlertType",
    "load_systems",
]
