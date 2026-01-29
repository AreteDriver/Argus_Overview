"""
Intel Parser - Analyzes EVE chat messages for intel content.

Parses messages for:
- System names (null-sec format like HED-GP, and known systems)
- Hostile indicators (hostile, neut, red, spike, etc.)
- Ship types
- Player counts (+5, x3, gang of 10, etc.)
- Clear reports (clr, clear, nv, etc.)
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Set


class ThreatLevel(Enum):
    """Threat level classification for intel reports."""

    CLEAR = "clear"  # System reported clear
    INFO = "info"  # General intel, not immediate threat
    WARNING = "warning"  # Hostiles nearby (2+ jumps)
    DANGER = "danger"  # Hostiles close (1 jump) or small gang
    CRITICAL = "critical"  # Hostiles in system or capital ships


@dataclass
class IntelReport:
    """Represents parsed intel from a chat message."""

    system: Optional[str]
    threat_level: ThreatLevel
    hostile_count: Optional[int]
    ship_types: List[str]
    player_names: List[str]
    raw_message: str
    timestamp: datetime = field(default_factory=datetime.now)
    channel: str = ""
    reporter: str = ""
    jumps_from_current: Optional[int] = None


class IntelParser:
    """
    Parses chat messages for intel content.

    Uses pattern matching to identify:
    - EVE system names
    - Hostile/threat indicators
    - Ship types
    - Player counts
    """

    # Common EVE ship types for detection (lowercase)
    SHIP_TYPES: Set[str] = {
        # Frigates
        "atron",
        "tristan",
        "merlin",
        "rifter",
        "punisher",
        "tormentor",
        "executioner",
        "condor",
        "slasher",
        "incursus",
        "kestrel",
        "breacher",
        "magnate",
        "heron",
        "probe",
        "imicus",
        # Interceptors
        "ares",
        "taranis",
        "crow",
        "raptor",
        "crusader",
        "malediction",
        "claw",
        "stiletto",
        # Assault Frigates
        "enyo",
        "ishkur",
        "harpy",
        "hawk",
        "retribution",
        "vengeance",
        "jaguar",
        "wolf",
        # Interdictors
        "sabre",
        "heretic",
        "flycatcher",
        "eris",
        # Destroyers
        "catalyst",
        "algos",
        "cormorant",
        "corax",
        "coercer",
        "dragoon",
        "thrasher",
        "talwar",
        # Cruisers
        "thorax",
        "vexor",
        "caracal",
        "moa",
        "rupture",
        "stabber",
        "omen",
        "maller",
        "arbitrator",
        "bellicose",
        "celestis",
        "blackbird",
        # Heavy Assault Cruisers
        "deimos",
        "ishtar",
        "cerberus",
        "eagle",
        "vagabond",
        "muninn",
        "zealot",
        "sacrilege",
        # Recon Ships
        "lachesis",
        "arazu",
        "falcon",
        "rook",
        "rapier",
        "huginn",
        "curse",
        "pilgrim",
        # Strategic Cruisers (T3C)
        "proteus",
        "tengu",
        "loki",
        "legion",
        # Battlecruisers
        "brutix",
        "myrmidon",
        "ferox",
        "drake",
        "harbinger",
        "prophecy",
        "hurricane",
        "cyclone",
        "gnosis",
        # Command Ships
        "astarte",
        "eos",
        "vulture",
        "nighthawk",
        "absolution",
        "damnation",
        "sleipnir",
        "claymore",
        # Battleships
        "megathron",
        "hyperion",
        "dominix",
        "raven",
        "rokh",
        "scorpion",
        "typhoon",
        "tempest",
        "maelstrom",
        "apocalypse",
        "armageddon",
        "abaddon",
        "machariel",
        "nightmare",
        "vindicator",
        "rattlesnake",
        "barghest",
        "nestor",
        # Capitals
        "carrier",
        "dreadnought",
        "fax",
        "supercarrier",
        "titan",
        # Specific Capitals
        "nyx",
        "hel",
        "aeon",
        "wyvern",
        "avatar",
        "erebus",
        "ragnarok",
        "leviathan",
        "moros",
        "naglfar",
        "revelation",
        "phoenix",
        "ninazu",
        "lif",
        "apostle",
        "minokawa",
        "thanatos",
        "archon",
        "chimera",
        "nidhoggur",
        # Force Auxiliaries
        "force auxiliary",
        # Other notable ships
        "stratios",
        "astero",
        "svipul",
        "confessor",
        "hecate",
        "jackdaw",
    }

    # Capital ship types (subset for threat escalation)
    CAPITAL_SHIPS: Set[str] = {
        "carrier",
        "dreadnought",
        "fax",
        "supercarrier",
        "titan",
        "nyx",
        "hel",
        "aeon",
        "wyvern",
        "avatar",
        "erebus",
        "ragnarok",
        "leviathan",
        "moros",
        "naglfar",
        "revelation",
        "phoenix",
        "ninazu",
        "lif",
        "apostle",
        "minokawa",
        "thanatos",
        "archon",
        "chimera",
        "nidhoggur",
        "force auxiliary",
    }

    # Intel keywords
    HOSTILE_KEYWORDS: Set[str] = {
        "hostile",
        "hostiles",
        "neut",
        "neuts",
        "neutral",
        "neutrals",
        "red",
        "reds",
        "spike",
        "spiked",
        "gang",
        "fleet",
        "camp",
        "gate camp",
        "gatecamp",
        "bubble",
        "bubbled",
        "drag",
        "tackled",
        "tackle",
        "point",
        "pointed",
        "warp disrupted",
        "cyno",
        "cyno up",
        "hot",
        "contact",
        "contacts",
    }

    CLEAR_KEYWORDS: Set[str] = {
        "clear",
        "clr",
        "empty",
        "nv",
        "no visual",
        "no vis",
        "nothing",
        "safe",
        "all clear",
    }

    MOVEMENT_KEYWORDS: Set[str] = {
        "jumping",
        "jumped",
        "holding",
        "warping",
        "landing",
        "inbound",
        "outbound",
        "heading",
        "moving",
    }

    def __init__(self, known_systems: Optional[Set[str]] = None):
        """
        Initialize the intel parser.

        Args:
            known_systems: Optional set of known system names (lowercase)
        """
        self.logger = logging.getLogger(__name__)
        self.known_systems: Set[str] = known_systems or self._load_default_systems()

    def _load_default_systems(self) -> Set[str]:
        """
        Load a default set of known EVE system names.

        Returns:
            Set of known system names (lowercase)
        """
        # Common null-sec, low-sec, and high-sec systems
        # In production, this would be loaded from EVE SDE
        return {
            # Trade hubs
            "jita",
            "amarr",
            "dodixie",
            "rens",
            "hek",
            # Famous null-sec systems
            "hed-gp",
            "1dq1-a",
            "r1o-gn",
            "b-r5rb",
            "m-oee8",
            "y-2anf",
            "ge-8jv",
            "f-eup9",
            "4-hwwf",
            "t-m0fa",
            # Low-sec hotspots
            "amamake",
            "tama",
            "rancer",
            "old man star",
            "asakai",
            "rakapas",
        }

    def add_known_system(self, system: str):
        """Add a system to the known systems set."""
        self.known_systems.add(system.lower())

    def parse(
        self,
        message: str,
        timestamp: Optional[datetime] = None,
        channel: str = "",
        reporter: str = "",
    ) -> Optional[IntelReport]:
        """
        Parse a message for intel content.

        Args:
            message: Chat message text
            timestamp: Message timestamp
            channel: Source channel name
            reporter: Player who sent the message

        Returns:
            IntelReport if intel detected, None otherwise
        """
        msg_lower = message.lower()

        # Check for clear reports first
        if any(kw in msg_lower for kw in self.CLEAR_KEYWORDS):
            system = self._extract_system(message)
            if system:
                return IntelReport(
                    system=system,
                    threat_level=ThreatLevel.CLEAR,
                    hostile_count=0,
                    ship_types=[],
                    player_names=[],
                    raw_message=message,
                    timestamp=timestamp or datetime.now(),
                    channel=channel,
                    reporter=reporter,
                )

        # Check for hostile indicators
        has_hostile_keyword = any(kw in msg_lower for kw in self.HOSTILE_KEYWORDS)

        # Extract system name
        system = self._extract_system(message)

        # Extract ship types mentioned
        ships = self._extract_ships(message)

        # Extract count (e.g., "+5", "x3", "5 in local")
        count = self._extract_count(message)

        # Extract player names (basic)
        players = self._extract_players(message)

        # If we have a system and hostile indicators, it's intel
        if system and (has_hostile_keyword or ships or count):
            threat_level = self._assess_threat(count, ships)
            return IntelReport(
                system=system,
                threat_level=threat_level,
                hostile_count=count,
                ship_types=ships,
                player_names=players,
                raw_message=message,
                timestamp=timestamp or datetime.now(),
                channel=channel,
                reporter=reporter,
            )

        # Check if it looks like intel even without a system
        # (e.g., just "hostile Loki +5" in an intel channel)
        if has_hostile_keyword and (ships or count):
            threat_level = self._assess_threat(count, ships)
            return IntelReport(
                system=None,
                threat_level=threat_level,
                hostile_count=count,
                ship_types=ships,
                player_names=players,
                raw_message=message,
                timestamp=timestamp or datetime.now(),
                channel=channel,
                reporter=reporter,
            )

        return None

    def _extract_system(self, message: str) -> Optional[str]:
        """
        Extract system name from message.

        Args:
            message: Chat message

        Returns:
            System name if found, None otherwise
        """
        # Pattern for null-sec system names:
        # - All caps with numbers/dashes: HED-GP, 1DQ1-A, B-R5RB, Y-2ANO
        null_pattern = r"\b([A-Z0-9]{1,4}-[A-Z0-9]{1,6})\b"
        match = re.search(null_pattern, message)
        if match:
            return match.group(1)

        # Also try lowercase version
        null_pattern_lower = r"\b([a-z0-9]{1,4}-[a-z0-9]{1,6})\b"
        match = re.search(null_pattern_lower, message.lower())
        if match:
            return match.group(1).upper()

        # Check against known systems (case-insensitive)
        words = re.findall(r"\b[\w-]+\b", message)
        for word in words:
            if word.lower() in self.known_systems:
                return word

        return None

    def _extract_ships(self, message: str) -> List[str]:
        """
        Extract ship types from message.

        Args:
            message: Chat message

        Returns:
            List of ship types found
        """
        found = []
        msg_lower = message.lower()

        for ship in self.SHIP_TYPES:
            # Use word boundary matching
            if re.search(rf"\b{re.escape(ship)}\b", msg_lower):
                found.append(ship)

        return found

    def _extract_count(self, message: str) -> Optional[int]:
        """
        Extract hostile count from message.

        Args:
            message: Chat message

        Returns:
            Count if found, None otherwise
        """
        msg_lower = message.lower()

        # Patterns for count extraction (in order of specificity)
        patterns = [
            r"\+(\d+)",  # +5
            r"x(\d+)",  # x5
            r"(\d+)x\b",  # 5x
            r"(\d+)\s*in\s*local",  # 5 in local
            r"gang\s*of\s*(\d+)",  # gang of 5
            r"fleet\s*of\s*(\d+)",  # fleet of 5
            r"(\d+)\s*hostiles?",  # 5 hostile(s)
            r"(\d+)\s*neuts?",  # 5 neut(s)
            r"(\d+)\s*reds?",  # 5 red(s)
            r"(\d+)\s*man",  # 5 man (gang)
            r"(\d{1,3})\s*spike",  # 50 spike
        ]

        for pattern in patterns:
            match = re.search(pattern, msg_lower)
            if match:
                count = int(match.group(1))
                if 1 <= count <= 500:  # Sanity check
                    return count

        return None

    def _extract_players(self, message: str) -> List[str]:
        """
        Extract player names from message (basic heuristic).

        Args:
            message: Chat message

        Returns:
            List of potential player names
        """
        # This is a basic implementation
        # In production, could cross-reference with ESI character search
        # or maintain a cache of known hostile players

        # Look for patterns like "Player Name" (capitalized words)
        # but filter out ship names, system names, and keywords
        players = []

        # Simple pattern: 2-3 capitalized words together
        name_pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b"
        matches = re.findall(name_pattern, message)

        for match in matches:
            # Filter out known ship names and keywords
            if match.lower() not in self.SHIP_TYPES:
                if match.lower() not in self.HOSTILE_KEYWORDS:
                    if match.lower() not in self.CLEAR_KEYWORDS:
                        players.append(match)

        return players[:5]  # Limit to 5 names

    def _assess_threat(self, count: Optional[int], ships: List[str]) -> ThreatLevel:
        """
        Assess threat level based on intel.

        Args:
            count: Number of hostiles
            ships: Ship types detected

        Returns:
            Appropriate ThreatLevel
        """
        # Capital ships = critical threat
        if any(ship in self.CAPITAL_SHIPS for ship in ships):
            return ThreatLevel.CRITICAL

        # Supercarrier/Titan specifically
        super_ships = {
            "supercarrier",
            "titan",
            "nyx",
            "hel",
            "aeon",
            "wyvern",
            "avatar",
            "erebus",
            "ragnarok",
            "leviathan",
        }
        if any(ship in super_ships for ship in ships):
            return ThreatLevel.CRITICAL

        # Large fleet (10+)
        if count and count >= 10:
            return ThreatLevel.DANGER

        # Medium gang (5-9)
        if count and count >= 5:
            return ThreatLevel.WARNING

        # Small gang (2-4) or any hostile report
        if count and count >= 2:
            return ThreatLevel.WARNING

        # Single hostile or ship sighting
        if ships or count:
            return ThreatLevel.INFO

        # Default for any hostile mention
        return ThreatLevel.WARNING

    def is_likely_intel(self, message: str) -> bool:
        """
        Quick check if a message is likely intel (for filtering).

        Args:
            message: Chat message

        Returns:
            True if message appears to be intel
        """
        msg_lower = message.lower()

        # Clear report
        if any(kw in msg_lower for kw in self.CLEAR_KEYWORDS):
            return True

        # Hostile keyword
        if any(kw in msg_lower for kw in self.HOSTILE_KEYWORDS):
            return True

        # Has a system name pattern
        if re.search(r"\b[A-Z0-9]{1,4}-[A-Z0-9]{1,6}\b", message):
            return True

        # Contains a ship type
        if any(ship in msg_lower for ship in self.SHIP_TYPES):
            return True

        # Contains a count pattern
        if re.search(r"\+\d+|x\d+|\d+x\b", msg_lower):
            return True

        return False
