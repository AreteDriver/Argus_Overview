"""
Unit tests for the AlertDetector module.

Tests cover:
- AlertLevel enum
- AlertConfig dataclass
- AlertDetector initialization
- Callback registration
- Frame analysis
- Red flash detection
- Screen change detection
- History management
"""
from unittest.mock import MagicMock

import pytest
from PIL import Image

from eve_overview_pro.core.alert_detector import (
    AlertConfig,
    AlertDetector,
    AlertLevel,
)


class TestAlertLevel:
    """Tests for AlertLevel enum"""

    def test_all_levels_exist(self):
        """All expected alert levels exist"""
        assert AlertLevel.LOW.value == "low"
        assert AlertLevel.MEDIUM.value == "medium"
        assert AlertLevel.HIGH.value == "high"

    def test_level_count(self):
        """Correct number of alert levels"""
        assert len(AlertLevel) == 3


class TestAlertConfig:
    """Tests for AlertConfig dataclass"""

    def test_default_values(self):
        """AlertConfig has correct defaults"""
        config = AlertConfig()

        assert config.enabled is True
        assert config.red_flash_threshold == 0.7
        assert config.change_threshold == 0.3
        assert config.alert_cooldown == 5
        assert config.sound_enabled is False
        assert config.visual_border is True
        assert config.border_color == "#ff0000"
        assert config.border_flash_duration == 3

    def test_custom_values(self):
        """AlertConfig accepts custom values"""
        config = AlertConfig(
            enabled=False,
            red_flash_threshold=0.5,
            change_threshold=0.2,
            alert_cooldown=10,
            sound_enabled=True,
            visual_border=False,
            border_color="#00ff00",
            border_flash_duration=5
        )

        assert config.enabled is False
        assert config.red_flash_threshold == 0.5
        assert config.change_threshold == 0.2
        assert config.alert_cooldown == 10
        assert config.sound_enabled is True
        assert config.visual_border is False
        assert config.border_color == "#00ff00"
        assert config.border_flash_duration == 5


class TestAlertDetectorInit:
    """Tests for AlertDetector initialization"""

    def test_default_state(self):
        """AlertDetector starts with correct state"""
        detector = AlertDetector()

        assert isinstance(detector.config, AlertConfig)
        assert detector.previous_frames == {}
        assert detector.last_alert_times == {}
        assert detector.alert_callbacks == {}

    def test_set_config(self):
        """Can set custom config"""
        detector = AlertDetector()
        config = AlertConfig(enabled=False, red_flash_threshold=0.5)

        detector.set_config(config)

        assert detector.config.enabled is False
        assert detector.config.red_flash_threshold == 0.5


class TestCallbackRegistration:
    """Tests for callback registration"""

    @pytest.fixture
    def detector(self):
        """Create a fresh detector"""
        return AlertDetector()

    def test_register_callback(self, detector):
        """Can register a callback"""
        callback = MagicMock()
        detector.register_callback("win1", callback)

        assert "win1" in detector.alert_callbacks
        assert detector.alert_callbacks["win1"] == callback

    def test_register_multiple_callbacks(self, detector):
        """Can register callbacks for multiple windows"""
        cb1 = MagicMock()
        cb2 = MagicMock()

        detector.register_callback("win1", cb1)
        detector.register_callback("win2", cb2)

        assert len(detector.alert_callbacks) == 2

    def test_unregister_callback(self, detector):
        """Can unregister a callback"""
        callback = MagicMock()
        detector.register_callback("win1", callback)
        detector.previous_frames["win1"] = MagicMock()

        detector.unregister_callback("win1")

        assert "win1" not in detector.alert_callbacks
        assert "win1" not in detector.previous_frames

    def test_unregister_nonexistent(self, detector):
        """Unregistering nonexistent callback doesn't error"""
        detector.unregister_callback("nonexistent")  # Should not raise


class TestAnalyzeFrame:
    """Tests for frame analysis"""

    @pytest.fixture
    def detector(self):
        """Create a fresh detector"""
        return AlertDetector()

    @pytest.fixture
    def normal_image(self):
        """Create a normal (non-red) image"""
        # Create a blue/green image (no red)
        img = Image.new('RGB', (100, 100), color=(50, 100, 150))
        return img

    @pytest.fixture
    def red_image(self):
        """Create a predominantly red image"""
        # Create a very red image (simulates damage flash)
        img = Image.new('RGB', (100, 100), color=(255, 50, 50))
        return img

    def test_disabled_returns_none(self, detector, normal_image):
        """Returns None when disabled"""
        detector.config.enabled = False
        result = detector.analyze_frame("win1", normal_image)
        assert result is None

    def test_none_image_returns_none(self, detector):
        """Returns None for None image"""
        result = detector.analyze_frame("win1", None)
        assert result is None

    def test_stores_frame_for_comparison(self, detector, normal_image):
        """Stores frame for next comparison"""
        detector.analyze_frame("win1", normal_image)
        assert "win1" in detector.previous_frames

    def test_red_flash_triggers_high_alert(self, detector, red_image):
        """Red flash triggers HIGH alert"""
        # Lower threshold for test
        detector.config.red_flash_threshold = 0.5

        result = detector.analyze_frame("win1", red_image)
        assert result == AlertLevel.HIGH

    def test_normal_image_no_immediate_alert(self, detector, normal_image):
        """Normal image with no previous frame returns None"""
        result = detector.analyze_frame("win1", normal_image)
        assert result is None

    def test_callback_triggered_on_alert(self, detector, red_image):
        """Callback triggered when alert detected"""
        callback = MagicMock()
        detector.register_callback("win1", callback)
        detector.config.red_flash_threshold = 0.5

        detector.analyze_frame("win1", red_image)

        callback.assert_called_once_with(AlertLevel.HIGH)

    def test_callback_error_handled(self, detector, red_image):
        """Callback errors are handled gracefully"""
        callback = MagicMock(side_effect=Exception("Test error"))
        detector.register_callback("win1", callback)
        detector.config.red_flash_threshold = 0.5

        # Should not raise
        result = detector.analyze_frame("win1", red_image)
        assert result == AlertLevel.HIGH


class TestRedFlashDetection:
    """Tests for red flash detection"""

    @pytest.fixture
    def detector(self):
        """Create a fresh detector"""
        return AlertDetector()

    def test_pure_red_detected(self, detector):
        """Pure red image detected as flash"""
        detector.config.red_flash_threshold = 0.5
        img = Image.new('RGB', (100, 100), color=(255, 0, 0))

        result = detector._detect_red_flash(img)
        assert result

    def test_blue_not_detected(self, detector):
        """Blue image not detected as flash"""
        img = Image.new('RGB', (100, 100), color=(0, 0, 255))

        result = detector._detect_red_flash(img)
        assert not result

    def test_green_not_detected(self, detector):
        """Green image not detected as flash"""
        img = Image.new('RGB', (100, 100), color=(0, 255, 0))

        result = detector._detect_red_flash(img)
        assert not result

    def test_threshold_respected(self, detector):
        """Threshold controls detection sensitivity"""
        # Create image with 50% red pixels
        img = Image.new('RGB', (100, 100), color=(255, 0, 0))
        pixels = img.load()
        for x in range(50, 100):
            for y in range(100):
                pixels[x, y] = (0, 0, 255)

        # High threshold - should not detect
        detector.config.red_flash_threshold = 0.7
        assert not detector._detect_red_flash(img)

        # Low threshold - should detect
        detector.config.red_flash_threshold = 0.3
        assert detector._detect_red_flash(img)

    def test_dark_red_not_detected(self, detector):
        """Dark red (below brightness threshold) not detected"""
        # Red must be > 200 to count
        img = Image.new('RGB', (100, 100), color=(150, 50, 50))

        result = detector._detect_red_flash(img)
        assert not result


class TestScreenChangeDetection:
    """Tests for screen change detection"""

    @pytest.fixture
    def detector(self):
        """Create a fresh detector"""
        return AlertDetector()

    def test_identical_images_no_change(self, detector):
        """Identical images show no change"""
        img1 = Image.new('RGB', (100, 100), color=(100, 100, 100))
        img2 = Image.new('RGB', (100, 100), color=(100, 100, 100))

        result = detector._detect_screen_change(img1, img2)
        assert not result

    def test_completely_different_detected(self, detector):
        """Completely different images detected as change"""
        img1 = Image.new('RGB', (100, 100), color=(0, 0, 0))
        img2 = Image.new('RGB', (100, 100), color=(255, 255, 255))

        result = detector._detect_screen_change(img1, img2)
        assert result

    def test_partial_change_threshold(self, detector):
        """Partial change respects threshold"""
        # Create mostly similar images with 20% different
        img1 = Image.new('RGB', (100, 100), color=(100, 100, 100))
        img2 = img1.copy()
        pixels = img2.load()
        for x in range(20):
            for y in range(100):
                pixels[x, y] = (200, 200, 200)

        # High threshold - should not detect
        detector.config.change_threshold = 0.5
        assert not detector._detect_screen_change(img1, img2)

        # Low threshold - should detect
        detector.config.change_threshold = 0.1
        assert detector._detect_screen_change(img1, img2)

    def test_handles_different_sizes(self, detector):
        """Handles images of different sizes"""
        img1 = Image.new('RGB', (200, 200), color=(100, 100, 100))
        img2 = Image.new('RGB', (50, 50), color=(100, 100, 100))

        # Should not raise
        result = detector._detect_screen_change(img1, img2)
        assert not result


class TestHistoryManagement:
    """Tests for frame history management"""

    @pytest.fixture
    def detector(self):
        """Create detector with some history"""
        d = AlertDetector()
        d.previous_frames["win1"] = MagicMock()
        d.previous_frames["win2"] = MagicMock()
        return d

    def test_clear_specific_window(self, detector):
        """Can clear history for specific window"""
        detector.clear_history("win1")

        assert "win1" not in detector.previous_frames
        assert "win2" in detector.previous_frames

    def test_clear_nonexistent_window(self, detector):
        """Clearing nonexistent window doesn't error"""
        detector.clear_history("nonexistent")  # Should not raise
        assert len(detector.previous_frames) == 2

    def test_clear_all_history(self, detector):
        """Can clear all history"""
        detector.clear_history()

        assert len(detector.previous_frames) == 0


class TestMediumAlertOnChange:
    """Tests for MEDIUM alert on screen change"""

    @pytest.fixture
    def detector(self):
        """Create a fresh detector"""
        return AlertDetector()

    def test_change_triggers_medium_alert(self, detector):
        """Significant screen change triggers MEDIUM alert"""
        # First frame - stores as previous
        img1 = Image.new('RGB', (100, 100), color=(50, 50, 50))
        detector.analyze_frame("win1", img1)

        # Second frame - very different
        img2 = Image.new('RGB', (100, 100), color=(200, 200, 200))
        result = detector.analyze_frame("win1", img2)

        assert result == AlertLevel.MEDIUM

    def test_no_change_no_alert(self, detector):
        """No change means no alert"""
        img = Image.new('RGB', (100, 100), color=(100, 100, 100))

        # First frame
        detector.analyze_frame("win1", img)

        # Same image again
        result = detector.analyze_frame("win1", img.copy())

        assert result is None


class TestExceptionHandling:
    """Tests for exception handling in detection methods"""

    @pytest.fixture
    def detector(self):
        """Create a fresh detector"""
        return AlertDetector()

    def test_red_flash_handles_conversion_error(self, detector):
        """_detect_red_flash handles image conversion errors"""
        from unittest.mock import patch, MagicMock

        # Create a mock image that raises on convert
        mock_image = MagicMock()
        mock_image.convert.side_effect = Exception("Conversion failed")

        result = detector._detect_red_flash(mock_image)

        # Should return False on error, not raise
        assert result is False

    def test_red_flash_handles_numpy_error(self, detector):
        """_detect_red_flash handles numpy array errors"""
        from unittest.mock import patch

        img = Image.new('RGB', (100, 100), color=(255, 0, 0))

        # Mock numpy.array to raise
        with patch('eve_overview_pro.core.alert_detector.np.array',
                   side_effect=Exception("numpy failed")):
            result = detector._detect_red_flash(img)

        # Should return False on error
        assert result is False

    def test_screen_change_handles_resize_error(self, detector):
        """_detect_screen_change handles resize errors"""
        from unittest.mock import MagicMock

        # Create mock images where resize fails
        mock_current = MagicMock()
        mock_current.resize.side_effect = Exception("Resize failed")

        mock_previous = MagicMock()

        result = detector._detect_screen_change(mock_current, mock_previous)

        # Should return False on error
        assert result is False

    def test_screen_change_handles_numpy_error(self, detector):
        """_detect_screen_change handles numpy errors"""
        from unittest.mock import patch

        img1 = Image.new('RGB', (100, 100), color=(50, 50, 50))
        img2 = Image.new('RGB', (100, 100), color=(200, 200, 200))

        # Mock numpy.array to raise on second call (during comparison)
        call_count = [0]
        original_array = __import__('numpy').array

        def mock_array(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] > 1:
                raise Exception("numpy failed")
            return original_array(*args, **kwargs)

        with patch('eve_overview_pro.core.alert_detector.np.array',
                   side_effect=mock_array):
            result = detector._detect_screen_change(img1, img2)

        # Should return False on error
        assert result is False
