#!/usr/bin/env python3
"""
Performance benchmarks for Argus Overview core components.

Run with: python benchmarks/benchmark_core.py

Tests performance-critical paths:
- Image conversion (PIL to QImage)
- wmctrl caching
- Window capture processing
"""

import gc
import statistics
import sys
import time
from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def benchmark(func: Callable, iterations: int = 1000, warmup: int = 10) -> dict:
    """Run a benchmark and return timing statistics."""
    # Warmup
    for _ in range(warmup):
        func()

    # Collect garbage before timing
    gc.collect()

    # Actual benchmark
    times: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        func()
        end = time.perf_counter_ns()
        times.append((end - start) / 1_000_000)  # Convert to ms

    return {
        "iterations": iterations,
        "min_ms": min(times),
        "max_ms": max(times),
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        "total_ms": sum(times),
    }


def print_results(name: str, results: dict):
    """Print benchmark results in a formatted way."""
    print(f"\n{'=' * 60}")
    print(f"Benchmark: {name}")
    print(f"{'=' * 60}")
    print(f"  Iterations: {results['iterations']:,}")
    print(f"  Min:        {results['min_ms']:.4f} ms")
    print(f"  Max:        {results['max_ms']:.4f} ms")
    print(f"  Mean:       {results['mean_ms']:.4f} ms")
    print(f"  Median:     {results['median_ms']:.4f} ms")
    print(f"  Std Dev:    {results['stdev_ms']:.4f} ms")
    print(f"  Throughput: {1000 / results['mean_ms']:.1f} ops/sec")


def benchmark_pil_to_qimage():
    """Benchmark PIL to QImage conversion."""
    from PIL import Image

    from argus_overview.ui.main_tab import pil_to_qimage

    # Create test images at typical preview sizes
    small_image = Image.new("RGB", (320, 240), color=(100, 100, 100))
    medium_image = Image.new("RGB", (640, 480), color=(100, 100, 100))
    large_image = Image.new("RGB", (1920, 1080), color=(100, 100, 100))

    def convert_small():
        pil_to_qimage(small_image)

    def convert_medium():
        pil_to_qimage(medium_image)

    def convert_large():
        pil_to_qimage(large_image)

    results = benchmark(convert_small, iterations=1000)
    print_results("PIL->QImage - 320x240 (30% scale)", results)

    results = benchmark(convert_medium, iterations=1000)
    print_results("PIL->QImage - 640x480", results)

    results = benchmark(convert_large, iterations=500)
    print_results("PIL->QImage - 1920x1080 (full)", results)


def benchmark_wmctrl_cache():
    """Benchmark wmctrl result caching."""
    from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

    # Mock subprocess to avoid actual system calls
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = """0x12345678  0 desktop  Window 1
0x87654321  0 desktop  Window 2
0x11111111  0 desktop  EVE - Character Name
"""

    capture = WindowCaptureThreaded()

    with patch("subprocess.run", return_value=mock_result):
        # First call - cache miss
        def get_windows_cold():
            capture._wmctrl_cache = {}  # Clear cache
            capture._wmctrl_cache_time = 0
            return capture.get_window_list()

        results = benchmark(get_windows_cold, iterations=500)
        print_results("wmctrl - Cache Miss (cold)", results)

        # Subsequent calls - cache hit
        capture.get_window_list()  # Prime the cache

        def get_windows_cached():
            return capture.get_window_list()

        results = benchmark(get_windows_cached, iterations=5000)
        print_results("wmctrl - Cache Hit (warm)", results)


def benchmark_capture_queue():
    """Benchmark capture result queue processing."""
    import queue

    from PIL import Image

    # Simulate the result queue processing
    result_queue: queue.Queue = queue.Queue()

    # Pre-populate with test results
    test_image = Image.new("RGB", (320, 240), color=(50, 50, 50))

    def queue_get_empty():
        try:
            result_queue.get_nowait()
        except queue.Empty:
            pass

    results = benchmark(queue_get_empty, iterations=10000)
    print_results("Queue.get_nowait() - Empty", results)

    # Test with items
    for i in range(1000):
        result_queue.put((f"req_{i}", f"win_{i}", test_image))

    def queue_get_with_item():
        try:
            result_queue.get_nowait()
        except queue.Empty:
            pass

    results = benchmark(queue_get_with_item, iterations=1000)
    print_results("Queue.get_nowait() - With Item", results)


def benchmark_window_id_validation():
    """Benchmark window ID validation."""
    from argus_overview.core.window_capture_threaded import _is_valid_window_id

    valid_hex = "0x12345678"
    valid_dec = "12345678"
    invalid = "'; rm -rf /"

    def validate_hex():
        _is_valid_window_id(valid_hex)

    def validate_dec():
        _is_valid_window_id(valid_dec)

    def validate_invalid():
        _is_valid_window_id(invalid)

    results = benchmark(validate_hex, iterations=10000)
    print_results("Window ID Validation - Hex", results)

    results = benchmark(validate_dec, iterations=10000)
    print_results("Window ID Validation - Decimal", results)

    results = benchmark(validate_invalid, iterations=10000)
    print_results("Window ID Validation - Invalid", results)


def benchmark_screen_geometry():
    """Benchmark screen geometry parsing."""
    from argus_overview.utils.screen import get_screen_geometry

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = """Screen 0: minimum 8 x 8, current 3840 x 1080, maximum 32767 x 32767
DP-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 527mm x 296mm
   1920x1080     60.00*+
DP-2 connected 1920x1080+1920+0 (normal left inverted right x axis y axis) 527mm x 296mm
   1920x1080     60.00*+
"""

    with patch("subprocess.run", return_value=mock_result):

        def get_geometry():
            # Clear any caching by reimporting (if cached)
            return get_screen_geometry(0)

        results = benchmark(get_geometry, iterations=500)
        print_results("Screen Geometry - xrandr parse", results)


def main():
    """Run all benchmarks."""
    print("\n" + "=" * 60)
    print("ARGUS OVERVIEW PERFORMANCE BENCHMARKS")
    print("=" * 60)

    # Need QApplication for Qt-based benchmarks
    from PySide6.QtWidgets import QApplication

    _app = QApplication.instance() or QApplication([])

    try:
        benchmark_window_id_validation()
        benchmark_wmctrl_cache()
        benchmark_pil_to_qimage()
        benchmark_capture_queue()
        benchmark_screen_geometry()

    except Exception as e:
        print(f"\nError during benchmarks: {e}")
        import traceback

        traceback.print_exc()
        return 1

    print("\n" + "=" * 60)
    print("BENCHMARKS COMPLETE")
    print("=" * 60)

    # Performance targets
    print("\n📊 Performance Targets:")
    print("  - PIL->QImage (320x240): < 0.5ms")
    print("  - wmctrl cache hit: < 0.01ms")
    print("  - Window ID validation: < 0.001ms")

    return 0


if __name__ == "__main__":
    sys.exit(main())
