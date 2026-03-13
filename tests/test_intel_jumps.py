"""
Unit tests for the JumpCalculator module.

Tests cover:
- BFS distance calculation (known paths)
- Distance returns None for unknown systems
- systems_within returns correct neighbors
- path returns correct route
- Case insensitivity
- Missing/corrupt data file fallback
- Integration: parser populates jumps_from_current
"""

import json
from pathlib import Path

from argus_overview.intel.jumps import JumpCalculator


class TestDistance:
    """Tests for BFS distance calculation."""

    def setup_method(self):
        self.calc = JumpCalculator()

    def test_same_system_zero_jumps(self):
        """Distance from a system to itself is 0."""
        assert self.calc.distance("Jita", "Jita") == 0

    def test_adjacent_systems_one_jump(self):
        """Adjacent systems are 1 jump apart."""
        assert self.calc.distance("Jita", "Perimeter") == 1

    def test_two_jumps(self):
        """Systems two hops apart return 2."""
        # Jita -> Perimeter -> Urlen
        assert self.calc.distance("Jita", "Urlen") == 2

    def test_multi_hop_path(self):
        """Longer paths return correct distance."""
        # Jita -> Perimeter -> Urlen -> Sirppala
        assert self.calc.distance("Jita", "Sirppala") == 3

    def test_unknown_origin_returns_none(self):
        """Unknown origin system returns None."""
        assert self.calc.distance("FakeSystem", "Jita") is None

    def test_unknown_destination_returns_none(self):
        """Unknown destination system returns None."""
        assert self.calc.distance("Jita", "FakeSystem") is None

    def test_both_unknown_returns_none(self):
        """Both systems unknown returns None."""
        assert self.calc.distance("FakeA", "FakeB") is None

    def test_disconnected_systems_return_none(self):
        """Systems with no path between them return None."""
        # Thera has no gates in the data (wormhole-only)
        assert self.calc.distance("Jita", "Thera") is None

    def test_known_pipe_distance(self):
        """HED-GP -> SV5-8N is 1 jump."""
        assert self.calc.distance("HED-GP", "SV5-8N") == 1

    def test_null_sec_chain(self):
        """HED-GP -> GE-8JV is 2 jumps (HED -> SV5 -> GE)."""
        assert self.calc.distance("HED-GP", "GE-8JV") == 2


class TestCaseInsensitivity:
    """Tests for case-insensitive lookups."""

    def setup_method(self):
        self.calc = JumpCalculator()

    def test_lowercase(self):
        assert self.calc.distance("jita", "perimeter") == 1

    def test_uppercase(self):
        assert self.calc.distance("JITA", "PERIMETER") == 1

    def test_mixed_case(self):
        assert self.calc.distance("Jita", "perimeter") == 1

    def test_null_sec_case(self):
        assert self.calc.distance("hed-gp", "SV5-8N") == 1


class TestSystemsWithin:
    """Tests for systems_within range query."""

    def setup_method(self):
        self.calc = JumpCalculator()

    def test_zero_range_returns_self(self):
        result = self.calc.systems_within("Jita", 0)
        assert result == {"jita": 0}

    def test_one_jump_returns_neighbors(self):
        result = self.calc.systems_within("Jita", 1)
        assert "jita" in result
        assert result["jita"] == 0
        assert "perimeter" in result
        assert result["perimeter"] == 1
        assert "new caldari" in result
        assert result["new caldari"] == 1

    def test_two_jump_range(self):
        result = self.calc.systems_within("Jita", 2)
        # Jita neighbors at 1 jump
        assert result["perimeter"] == 1
        # Perimeter neighbors at 2 jumps
        assert "urlen" in result
        assert result["urlen"] == 2

    def test_unknown_system_returns_empty(self):
        result = self.calc.systems_within("FakeSystem", 5)
        assert result == {}

    def test_max_jumps_respected(self):
        result = self.calc.systems_within("Jita", 1)
        # Urlen is 2 jumps — should NOT be in 1-jump range
        assert "urlen" not in result


class TestPath:
    """Tests for shortest path calculation."""

    def setup_method(self):
        self.calc = JumpCalculator()

    def test_same_system(self):
        result = self.calc.path("Jita", "Jita")
        assert result == ["jita"]

    def test_adjacent_path(self):
        result = self.calc.path("Jita", "Perimeter")
        assert result == ["jita", "perimeter"]

    def test_multi_hop_path(self):
        result = self.calc.path("Jita", "Urlen")
        assert result is not None
        assert result[0] == "jita"
        assert result[-1] == "urlen"
        assert len(result) == 3  # jita -> perimeter -> urlen

    def test_unknown_system_returns_none(self):
        assert self.calc.path("FakeSystem", "Jita") is None

    def test_disconnected_returns_none(self):
        assert self.calc.path("Jita", "Thera") is None

    def test_path_length_matches_distance(self):
        """Path length - 1 should equal distance."""
        path = self.calc.path("Jita", "Sirppala")
        dist = self.calc.distance("Jita", "Sirppala")
        assert path is not None
        assert dist is not None
        assert len(path) - 1 == dist


class TestDataFileFallback:
    """Tests for missing or corrupt data file handling."""

    def test_missing_file_creates_empty_calculator(self):
        calc = JumpCalculator(data_path=Path("/nonexistent/jumps.json"))
        assert calc.system_count == 0
        assert calc.distance("Jita", "Perimeter") is None

    def test_corrupt_json_creates_empty_calculator(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json {{{", encoding="utf-8")
        calc = JumpCalculator(data_path=bad_file)
        assert calc.system_count == 0

    def test_wrong_json_type_creates_empty_calculator(self, tmp_path):
        bad_file = tmp_path / "array.json"
        bad_file.write_text('["jita", "amarr"]', encoding="utf-8")
        calc = JumpCalculator(data_path=bad_file)
        assert calc.system_count == 0

    def test_valid_custom_data(self, tmp_path):
        data = {"alpha": ["beta"], "beta": ["alpha", "gamma"], "gamma": ["beta"]}
        data_file = tmp_path / "custom.json"
        data_file.write_text(json.dumps(data), encoding="utf-8")
        calc = JumpCalculator(data_path=data_file)
        assert calc.system_count == 3
        assert calc.distance("alpha", "gamma") == 2


class TestParserIntegration:
    """Tests for JumpCalculator wired into IntelParser."""

    def setup_method(self):
        self.calc = JumpCalculator()

    def test_parser_populates_jumps_from_current(self):
        """Parser should set jumps_from_current when calculator and current system are set."""
        from argus_overview.intel.parser import IntelParser

        parser = IntelParser(jump_calculator=self.calc)
        parser.set_current_system("Jita")
        report = parser.parse("Perimeter hostile +5")
        assert report is not None
        assert report.jumps_from_current == 1

    def test_parser_no_calculator_leaves_none(self):
        """Without a calculator, jumps_from_current stays None."""
        from argus_overview.intel.parser import IntelParser

        parser = IntelParser()
        parser.set_current_system("Jita")
        report = parser.parse("Perimeter hostile +5")
        assert report is not None
        assert report.jumps_from_current is None

    def test_parser_no_current_system_leaves_none(self):
        """Without current system set, jumps_from_current stays None."""
        from argus_overview.intel.parser import IntelParser

        parser = IntelParser(jump_calculator=self.calc)
        report = parser.parse("HED-GP hostile +5")
        assert report is not None
        assert report.jumps_from_current is None

    def test_parser_clear_report_has_jumps(self):
        """Clear reports should also get jump distance populated."""
        from argus_overview.intel.parser import IntelParser

        parser = IntelParser(jump_calculator=self.calc)
        parser.set_current_system("Jita")
        report = parser.parse("Perimeter clr")
        assert report is not None
        assert report.jumps_from_current == 1

    def test_parser_unknown_system_jumps_none(self):
        """Report for a system not in jump data gets None for jumps."""
        from argus_overview.intel.parser import IntelParser

        parser = IntelParser(
            known_systems={"xyzzy"},
            jump_calculator=self.calc,
        )
        parser.set_current_system("Jita")
        report = parser.parse("Xyzzy hostile +3")
        assert report is not None
        assert report.jumps_from_current is None

    def test_parser_no_system_report_no_jumps(self):
        """Reports without a system should not get jumps populated."""
        from argus_overview.intel.parser import IntelParser

        parser = IntelParser(jump_calculator=self.calc)
        parser.set_current_system("Jita")
        report = parser.parse("hostile loki +5")
        assert report is not None
        assert report.system is None
        assert report.jumps_from_current is None

    def test_set_current_system(self):
        """set_current_system stores the system name."""
        from argus_overview.intel.parser import IntelParser

        parser = IntelParser(jump_calculator=self.calc)
        parser.set_current_system("Amarr")
        assert parser._current_system == "Amarr"


class TestDefaultDataPath:
    """Test the default data path helper."""

    def test_default_path_exists(self):
        from argus_overview.intel.jumps import get_default_data_path

        path = get_default_data_path()
        assert path.exists()
        assert path.name == "jumps.json"

    def test_default_data_loads(self):
        """Default bundled data should load successfully."""
        calc = JumpCalculator()
        assert calc.system_count > 0
