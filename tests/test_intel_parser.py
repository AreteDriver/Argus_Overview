"""
Unit tests for the Intel Parser module.

Tests cover:
- System name extraction (null-sec format, known systems)
- Hostile keyword detection
- Ship type detection
- Count extraction
- Threat level assessment
- Clear report parsing
- Edge cases and malformed input
"""

import pytest
from datetime import datetime

from argus_overview.intel.parser import IntelParser, IntelReport, ThreatLevel


class TestSystemExtraction:
    """Tests for system name extraction"""

    def setup_method(self):
        """Setup parser for each test"""
        self.parser = IntelParser()

    def test_extract_nullsec_system_uppercase(self):
        """Should extract uppercase null-sec system names"""
        report = self.parser.parse("HED-GP hostile Loki")
        assert report is not None
        assert report.system == "HED-GP"

    def test_extract_nullsec_system_mixed_case(self):
        """Should extract system names with numbers"""
        report = self.parser.parse("1DQ1-A spike +50")
        assert report is not None
        assert report.system == "1DQ1-A"

    def test_extract_nullsec_system_long_format(self):
        """Should extract longer system name formats"""
        report = self.parser.parse("B-R5RB hostile fleet")
        assert report is not None
        assert report.system == "B-R5RB"

    def test_extract_known_system(self):
        """Should extract known system names from the default set"""
        parser = IntelParser(known_systems={"amamake", "tama"})
        report = parser.parse("Amamake hostile")
        assert report is not None
        assert report.system == "Amamake"

    def test_no_system_in_message(self):
        """Should handle messages without system names"""
        report = self.parser.parse("hostile loki +5")
        assert report is not None
        assert report.system is None


class TestHostileKeywords:
    """Tests for hostile keyword detection"""

    def setup_method(self):
        """Setup parser for each test"""
        self.parser = IntelParser()

    def test_hostile_keyword(self):
        """Should detect 'hostile' keyword"""
        report = self.parser.parse("HED-GP hostile")
        assert report is not None
        assert report.threat_level != ThreatLevel.CLEAR

    def test_neut_keyword(self):
        """Should detect 'neut' keyword"""
        report = self.parser.parse("HED-GP neut")
        assert report is not None
        assert report.threat_level != ThreatLevel.CLEAR

    def test_spike_keyword(self):
        """Should detect 'spike' keyword"""
        report = self.parser.parse("HED-GP spike")
        assert report is not None

    def test_gang_keyword(self):
        """Should detect 'gang' keyword"""
        report = self.parser.parse("HED-GP gang")
        assert report is not None

    def test_camp_keyword(self):
        """Should detect 'camp' keyword"""
        report = self.parser.parse("HED-GP gate camp")
        assert report is not None

    def test_bubble_keyword(self):
        """Should detect 'bubble' keyword"""
        report = self.parser.parse("HED-GP bubbled")
        assert report is not None


class TestClearReports:
    """Tests for clear report parsing"""

    def setup_method(self):
        """Setup parser for each test"""
        self.parser = IntelParser()

    def test_clear_keyword(self):
        """Should detect 'clear' keyword"""
        report = self.parser.parse("HED-GP clear")
        assert report is not None
        assert report.system == "HED-GP"
        assert report.threat_level == ThreatLevel.CLEAR
        assert report.hostile_count == 0

    def test_clr_keyword(self):
        """Should detect 'clr' abbreviation"""
        report = self.parser.parse("HED-GP clr")
        assert report is not None
        assert report.threat_level == ThreatLevel.CLEAR

    def test_nv_keyword(self):
        """Should detect 'nv' (no visual) keyword"""
        report = self.parser.parse("HED-GP nv")
        assert report is not None
        assert report.threat_level == ThreatLevel.CLEAR


class TestShipTypeDetection:
    """Tests for ship type detection"""

    def setup_method(self):
        """Setup parser for each test"""
        self.parser = IntelParser()

    def test_single_ship_type(self):
        """Should detect single ship type"""
        report = self.parser.parse("HED-GP hostile Loki")
        assert report is not None
        assert "loki" in report.ship_types

    def test_multiple_ship_types(self):
        """Should detect multiple ship types"""
        report = self.parser.parse("HED-GP hostile Loki Sabre +5")
        assert report is not None
        assert "loki" in report.ship_types
        assert "sabre" in report.ship_types

    def test_interceptor_detection(self):
        """Should detect interceptor ship types"""
        report = self.parser.parse("HED-GP hostile ares stiletto")
        assert report is not None
        assert "ares" in report.ship_types
        assert "stiletto" in report.ship_types

    def test_capital_ship_detection(self):
        """Should detect capital ship types"""
        report = self.parser.parse("HED-GP hostile carrier on gate")
        assert report is not None
        assert "carrier" in report.ship_types

    def test_titan_detection(self):
        """Should detect titan specifically"""
        report = self.parser.parse("HED-GP titan")
        assert report is not None
        assert "titan" in report.ship_types


class TestCountExtraction:
    """Tests for hostile count extraction"""

    def setup_method(self):
        """Setup parser for each test"""
        self.parser = IntelParser()

    def test_plus_count_format(self):
        """Should extract +N count format"""
        report = self.parser.parse("HED-GP hostile +5")
        assert report is not None
        assert report.hostile_count == 5

    def test_x_prefix_count_format(self):
        """Should extract xN count format"""
        report = self.parser.parse("HED-GP hostile x10")
        assert report is not None
        assert report.hostile_count == 10

    def test_x_suffix_count_format(self):
        """Should extract Nx count format"""
        report = self.parser.parse("HED-GP hostile 10x")
        assert report is not None
        assert report.hostile_count == 10

    def test_in_local_format(self):
        """Should extract 'N in local' count format"""
        report = self.parser.parse("HED-GP hostile 15 in local")
        assert report is not None
        assert report.hostile_count == 15

    def test_gang_of_format(self):
        """Should extract 'gang of N' count format"""
        report = self.parser.parse("HED-GP gang of 20")
        assert report is not None
        assert report.hostile_count == 20

    def test_hostiles_suffix_format(self):
        """Should extract 'N hostiles' count format"""
        report = self.parser.parse("HED-GP 8 hostiles")
        assert report is not None
        assert report.hostile_count == 8

    def test_spike_count_format(self):
        """Should extract spike count"""
        report = self.parser.parse("HED-GP 50 spike")
        assert report is not None
        assert report.hostile_count == 50


class TestThreatLevelAssessment:
    """Tests for threat level assessment"""

    def setup_method(self):
        """Setup parser for each test"""
        self.parser = IntelParser()

    def test_critical_for_capital(self):
        """Capital ships should trigger CRITICAL threat"""
        report = self.parser.parse("HED-GP hostile carrier")
        assert report is not None
        assert report.threat_level == ThreatLevel.CRITICAL

    def test_critical_for_titan(self):
        """Titan should trigger CRITICAL threat"""
        report = self.parser.parse("HED-GP titan on gate")
        assert report is not None
        assert report.threat_level == ThreatLevel.CRITICAL

    def test_critical_for_supercarrier(self):
        """Supercarrier should trigger CRITICAL threat"""
        report = self.parser.parse("HED-GP hostile nyx")
        assert report is not None
        assert report.threat_level == ThreatLevel.CRITICAL

    def test_danger_for_large_fleet(self):
        """Large fleet (10+) should trigger DANGER threat"""
        report = self.parser.parse("HED-GP hostile +15")
        assert report is not None
        assert report.threat_level == ThreatLevel.DANGER

    def test_warning_for_small_gang(self):
        """Small gang (2-9) should trigger WARNING threat"""
        report = self.parser.parse("HED-GP hostile +5")
        assert report is not None
        assert report.threat_level == ThreatLevel.WARNING

    def test_clear_threat_level(self):
        """Clear report should have CLEAR threat level"""
        report = self.parser.parse("HED-GP clr")
        assert report is not None
        assert report.threat_level == ThreatLevel.CLEAR


class TestEdgeCases:
    """Tests for edge cases and malformed input"""

    def setup_method(self):
        """Setup parser for each test"""
        self.parser = IntelParser()

    def test_empty_message(self):
        """Should handle empty message"""
        report = self.parser.parse("")
        assert report is None

    def test_non_intel_message(self):
        """Should not parse regular chat as intel"""
        report = self.parser.parse("hey guys what's up")
        assert report is None

    def test_message_with_only_greeting(self):
        """Should not parse greetings as intel"""
        report = self.parser.parse("o7 everyone")
        assert report is None

    def test_case_insensitive_hostile(self):
        """Should handle mixed case in hostile keywords"""
        report = self.parser.parse("HED-GP HOSTILE loki")
        assert report is not None

    def test_case_insensitive_ship(self):
        """Should handle mixed case in ship names"""
        report = self.parser.parse("HED-GP hostile LOKI")
        assert report is not None
        assert "loki" in report.ship_types

    def test_preserves_timestamp(self):
        """Should preserve provided timestamp"""
        ts = datetime(2025, 1, 29, 14, 30, 0)
        report = self.parser.parse("HED-GP hostile", timestamp=ts)
        assert report is not None
        assert report.timestamp == ts

    def test_preserves_channel(self):
        """Should preserve channel name"""
        report = self.parser.parse("HED-GP hostile", channel="Alliance")
        assert report is not None
        assert report.channel == "Alliance"

    def test_preserves_reporter(self):
        """Should preserve reporter name"""
        report = self.parser.parse("HED-GP hostile", reporter="TestPilot")
        assert report is not None
        assert report.reporter == "TestPilot"


class TestIsLikelyIntel:
    """Tests for the quick intel check method"""

    def setup_method(self):
        """Setup parser for each test"""
        self.parser = IntelParser()

    def test_likely_intel_with_hostile(self):
        """Should identify hostile messages as likely intel"""
        assert self.parser.is_likely_intel("hostile in local") is True

    def test_likely_intel_with_system(self):
        """Should identify messages with system names as likely intel"""
        assert self.parser.is_likely_intel("HED-GP") is True

    def test_likely_intel_with_ship(self):
        """Should identify messages with ship names as likely intel"""
        assert self.parser.is_likely_intel("loki on gate") is True

    def test_likely_intel_with_count(self):
        """Should identify messages with counts as likely intel"""
        assert self.parser.is_likely_intel("+5 in local") is True

    def test_not_intel_normal_chat(self):
        """Should not identify normal chat as intel"""
        assert self.parser.is_likely_intel("how's everyone doing?") is False


class TestReportDataclass:
    """Tests for IntelReport dataclass"""

    def test_intel_report_creation(self):
        """IntelReport can be created with all fields"""
        report = IntelReport(
            system="HED-GP",
            threat_level=ThreatLevel.WARNING,
            hostile_count=5,
            ship_types=["loki", "sabre"],
            player_names=[],
            raw_message="HED-GP hostile Loki Sabre +5",
            channel="Alliance",
            reporter="TestPilot",
        )
        assert report.system == "HED-GP"
        assert report.threat_level == ThreatLevel.WARNING
        assert report.hostile_count == 5
        assert "loki" in report.ship_types
        assert report.channel == "Alliance"

    def test_threat_level_enum_values(self):
        """ThreatLevel enum has expected values"""
        assert ThreatLevel.CLEAR.value == "clear"
        assert ThreatLevel.INFO.value == "info"
        assert ThreatLevel.WARNING.value == "warning"
        assert ThreatLevel.DANGER.value == "danger"
        assert ThreatLevel.CRITICAL.value == "critical"


class TestComplexMessages:
    """Tests for complex real-world message formats"""

    def setup_method(self):
        """Setup parser for each test"""
        self.parser = IntelParser()

    def test_full_intel_report(self):
        """Should parse full intel report with all components"""
        report = self.parser.parse("HED-GP hostile Loki Sabre +5 heading to R1O")
        assert report is not None
        assert report.system == "HED-GP"
        assert "loki" in report.ship_types
        assert "sabre" in report.ship_types
        assert report.hostile_count == 5

    def test_multiline_system_report(self):
        """Should handle reports mentioning multiple systems"""
        report = self.parser.parse("HED-GP to R1O-GN hostile gang 10")
        assert report is not None
        # Should extract first system
        assert report.system == "HED-GP"

    def test_report_with_player_jump_info(self):
        """Should handle reports with movement info"""
        report = self.parser.parse("HED-GP hostile cerberus gang jumping to SV5")
        assert report is not None
        assert report.system == "HED-GP"
        assert "cerberus" in report.ship_types

    def test_caps_on_field(self):
        """Should parse cap-related intel"""
        report = self.parser.parse("1DQ1-A cyno up dread landing")
        assert report is not None
        assert report.system == "1DQ1-A"
        assert "dreadnought" in report.ship_types or report.hostile_count is None
