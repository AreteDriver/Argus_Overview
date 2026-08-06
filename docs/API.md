# Argus Overview API Reference

This document covers the public APIs for developers extending or integrating with Argus Overview.

## Platform Abstraction Layer

The `argus_overview.platform` module provides cross-platform interfaces for window management, screen capture, and EVE Online path resolution.

### Factory Functions

```python
from argus_overview.platform import (
    get_window_manager,
    get_window_capture,
    get_screen_manager,
    get_eve_path_resolver,
    get_hotkey_helper,
    get_platform_name,
    is_windows,
    is_linux,
)
```

#### `get_platform_name() -> str`
Returns the current platform name: `'windows'`, `'linux'`, `'macos'`, or `'unknown'`.

#### `is_windows() -> bool`
Returns `True` if running on Windows.

#### `is_linux() -> bool`
Returns `True` if running on Linux.

#### `get_window_manager() -> WindowManager`
Creates a platform-appropriate `WindowManager` instance.

**Raises:** `RuntimeError` if platform is not supported.

#### `get_window_capture(max_workers: int = 4) -> WindowCapture`
Creates a platform-appropriate `WindowCapture` instance.

**Args:**
- `max_workers`: Number of capture worker threads (default: 4)

**Raises:** `RuntimeError` if platform is not supported.

#### `get_screen_manager() -> ScreenManager`
Creates a platform-appropriate `ScreenManager` instance.

**Raises:** `RuntimeError` if platform is not supported.

#### `get_eve_path_resolver() -> EVEPathResolver`
Creates a platform-appropriate `EVEPathResolver` instance.

**Raises:** `RuntimeError` if platform is not supported.

#### `get_hotkey_helper() -> HotkeyHelper`
Creates a platform-appropriate `HotkeyHelper` instance.

**Raises:** `RuntimeError` if platform is not supported.

---

### Data Classes

#### `WindowInfo`
Information about a window.

```python
@dataclass
class WindowInfo:
    window_id: str  # Platform-specific window identifier
    title: str  # Window title
    class_name: str  # Window class (default: "")
```

#### `ScreenGeometry`
Screen/monitor geometry information.

```python
@dataclass
class ScreenGeometry:
    x: int  # X position
    y: int  # Y position
    width: int  # Screen width in pixels
    height: int  # Screen height in pixels
    is_primary: bool  # True if primary display (default: False)
```

---

### WindowManager Interface

Handles platform-specific window enumeration, positioning, and state changes.

```python
window_mgr = get_window_manager()
```

#### `get_window_list() -> List[Tuple[str, str]]`
Get list of all visible windows.

**Returns:** List of `(window_id, window_title)` tuples.

#### `get_eve_windows() -> List[Tuple[str, str]]`
Get list of EVE Online windows.

**Returns:** List of `(window_id, window_title)` tuples for EVE windows.

#### `move_window(window_id: str, x: int, y: int, w: int, h: int, timeout: float = 2.0) -> bool`
Move and resize a window.

**Args:**
- `window_id`: Platform-specific window identifier
- `x`: Target X position
- `y`: Target Y position
- `w`: Target width
- `h`: Target height
- `timeout`: Operation timeout in seconds (default: 2.0)

**Returns:** `True` if successful.

#### `activate_window(window_id: str, timeout: float = 2.0) -> bool`
Activate (focus/bring to front) a window.

**Args:**
- `window_id`: Platform-specific window identifier
- `timeout`: Operation timeout in seconds (default: 2.0)

**Returns:** `True` if successful.

#### `minimize_window(window_id: str) -> bool`
Minimize a window.

**Returns:** `True` if successful.

#### `restore_window(window_id: str) -> bool`
Restore a minimized window.

**Returns:** `True` if successful.

#### `get_focused_window() -> Optional[str]`
Get the currently focused window ID.

**Returns:** Window ID string or `None` if unable to determine.

#### `is_valid_window_id(window_id: str) -> bool`
Validate that a string is a valid window ID for this platform.

**Returns:** `True` if valid format.

#### `get_window_title(window_id: str) -> str`
Get the title of a window.

**Returns:** Window title string.

---

### WindowCapture Interface

Handles platform-specific screen capture using appropriate APIs.

- **Linux:** ImageMagick/X11 via `import` command
- **Windows:** GDI via Win32 API

```python
capture = get_window_capture(max_workers=4)
capture.start()  # Start worker threads
```

#### `start()`
Start capture worker threads.

#### `stop()`
Stop capture worker threads.

#### `running -> bool` (property)
Check if capture workers are running.

#### `capture_window_async(window_id: str, scale: float = 1.0) -> str`
Request async window capture.

**Args:**
- `window_id`: Platform-specific window identifier
- `scale`: Scale factor 0.0-1.0 (default: 1.0)

**Returns:** Request ID (UUID) to retrieve result later, empty string if invalid.

#### `get_result(timeout: float = 0.1) -> Optional[Tuple[str, str, Image.Image]]`
Get capture result if available.

**Args:**
- `timeout`: Timeout in seconds (default: 0.1)

**Returns:** Tuple of `(request_id, window_id, image)` or `None`.

#### `capture_window_sync(window_id: str, scale: float = 1.0) -> Optional[Image.Image]`
Synchronous window capture.

**Args:**
- `window_id`: Platform-specific window identifier
- `scale`: Scale factor 0.0-1.0 (default: 1.0)

**Returns:** PIL `Image` or `None` if capture failed.

---

### ScreenManager Interface

Queries display geometry using platform-appropriate methods.

- **Linux:** xrandr
- **Windows:** EnumDisplayMonitors

```python
screen_mgr = get_screen_manager()
monitors = screen_mgr.get_all_monitors()
```

#### `get_screen_geometry(monitor: int = 0) -> ScreenGeometry`
Get geometry for a specific monitor.

**Args:**
- `monitor`: Monitor index, 0-based (default: 0)

**Returns:** `ScreenGeometry` for requested monitor, or default on failure.

#### `get_all_monitors() -> List[ScreenGeometry]`
Get geometry for all connected monitors.

**Returns:** List of `ScreenGeometry` for all monitors.

---

### EVEPathResolver Interface

Locates EVE settings and log directories.

- **Linux:** Proton/Wine paths under Steam compatdata
- **Windows:** `%LOCALAPPDATA%\CCP\EVE\`

```python
path_resolver = get_eve_path_resolver()
settings_paths = path_resolver.get_eve_settings_paths()
```

#### `get_eve_settings_paths() -> List[Path]`
Get list of candidate EVE settings paths.

**Returns:** List of `Path` objects that may contain EVE settings.

#### `get_eve_logs_paths() -> List[Path]`
Get list of candidate EVE game logs paths.

**Returns:** List of `Path` objects that may contain EVE game logs.

#### `get_config_directory() -> Path`
Get application config directory.

**Returns:** `Path` to store application configuration.

---

### HotkeyHelper Interface

Normalizes hotkey strings to pynput-compatible format.

```python
hotkey_helper = get_hotkey_helper()
normalized = hotkey_helper.normalize_combo("<ctrl>+<v>")
```

#### `normalize_combo(key_combo: str) -> str`
Normalize a hotkey combo string for pynput.

**Args:**
- `key_combo`: Raw hotkey combo string (e.g., `"<ctrl>+<v>"`)

**Returns:** Normalized string compatible with pynput.

#### `is_single_key(key_combo: str) -> bool`
Check if a key combo is a single key (no modifiers).

**Returns:** `True` if single key, `False` if combo with modifiers.

---

## Intel Module

The `argus_overview.intel` module monitors EVE chat logs for intel reports and triggers alerts.

```python
from argus_overview.intel import (
    ChatLogWatcher,
    ChatMessage,
    IntelParser,
    IntelReport,
    ThreatLevel,
    AlertDispatcher,
    AlertConfig,
    AlertType,
)
```

---

### ThreatLevel Enum

Threat level classification for intel reports.

```python
class ThreatLevel(Enum):
    CLEAR = "clear"  # System reported clear
    INFO = "info"  # General intel, not immediate threat
    WARNING = "warning"  # Hostiles nearby (2+ jumps)
    DANGER = "danger"  # Hostiles close (1 jump) or small gang
    CRITICAL = "critical"  # Hostiles in system or capital ships
```

---

### IntelReport

Represents parsed intel from a chat message.

```python
@dataclass
class IntelReport:
    system: Optional[str]  # EVE system name (e.g., "HED-GP")
    threat_level: ThreatLevel  # Assessed threat level
    hostile_count: Optional[int]  # Number of hostiles if known
    ship_types: List[str]  # Detected ship types
    player_names: List[str]  # Detected player names
    raw_message: str  # Original message text
    timestamp: datetime  # Message timestamp
    channel: str  # Source channel name
    reporter: str  # Player who sent the message
    jumps_from_current: Optional[int]  # Distance from current system
```

---

### IntelParser

Parses chat messages for intel content.

```python
parser = IntelParser()
report = parser.parse("HED-GP hostile Loki +5")
```

#### `__init__(known_systems: Optional[Set[str]] = None)`
Initialize the intel parser.

**Args:**
- `known_systems`: Optional set of known system names (lowercase). Defaults to common EVE systems.

#### `parse(message: str, timestamp: Optional[datetime] = None, channel: str = "", reporter: str = "") -> Optional[IntelReport]`
Parse a message for intel content.

**Args:**
- `message`: Chat message text
- `timestamp`: Message timestamp (default: now)
- `channel`: Source channel name
- `reporter`: Player who sent the message

**Returns:** `IntelReport` if intel detected, `None` otherwise.

#### `is_likely_intel(message: str) -> bool`
Quick check if a message is likely intel (for filtering).

**Returns:** `True` if message appears to be intel.

#### `add_known_system(system: str)`
Add a system to the known systems set.

---

### AlertType Enum

Types of alerts that can be triggered.

```python
class AlertType(Enum):
    VISUAL_BORDER = "border"  # Flash window border
    VISUAL_OVERLAY = "overlay"  # Show overlay on preview
    AUDIO = "audio"  # Play sound
    SYSTEM_NOTIFICATION = "notification"  # Desktop notification
```

---

### AlertConfig

Configuration for alert behavior.

```python
@dataclass
class AlertConfig:
    enabled: bool = True
    visual_border: bool = True
    visual_overlay: bool = True
    audio: bool = True
    audio_file: Optional[Path] = None
    system_notification: bool = False

    # Thresholds
    min_threat_level: str = "warning"  # Minimum level to alert on
    jumps_threshold: int = 5  # Only alert if within N jumps

    # Visual settings
    border_color: str = "#FF0000"
    border_duration_ms: int = 2000
    overlay_duration_ms: int = 5000

    # Audio settings
    audio_volume: float = 1.0  # 0.0 to 1.0

    # Cooldown
    cooldown_seconds: int = 5  # Min time between alerts per system

    # Threat level colors (ThreatLevel -> hex color)
    threat_colors: dict
```

---

### AlertDispatcher

Dispatches alerts to the Argus Overview UI. Inherits from `QObject`.

```python
from PySide6.QtCore import QObject

dispatcher = AlertDispatcher(config=AlertConfig())
dispatcher.alert_triggered.connect(my_handler)
```

#### Signals

```python
border_flash_requested = Signal(str, int)  # (color, duration_ms)
overlay_requested = Signal(object)  # (IntelReport)
alert_triggered = Signal(object, object)  # (IntelReport, AlertType)
```

#### `__init__(config: Optional[AlertConfig] = None, parent: Optional[QObject] = None)`
Initialize the alert dispatcher.

#### `set_config(config: AlertConfig)`
Update alert configuration.

#### `dispatch(report: IntelReport)`
Dispatch alerts for an intel report. Respects configuration, thresholds, and cooldowns.

#### `test_alert(threat_level: ThreatLevel = ThreatLevel.WARNING)`
Trigger a test alert for testing UI integration.

#### `clear_cooldowns()`
Clear all alert cooldowns.

---

### ChatMessage

Represents a parsed chat log message.

```python
@dataclass
class ChatMessage:
    timestamp: datetime
    channel: str
    sender: str
    message: str
```

---

### ChatLogWatcher

Monitors EVE chat log files for new messages.

```python
watcher = ChatLogWatcher(log_paths=[Path("~/.eve/logs")])
watcher.message_received.connect(on_message)
watcher.start()
```

#### Signals

```python
message_received = Signal(object)  # (ChatMessage)
```

#### `__init__(log_paths: List[Path], parent: Optional[QObject] = None)`
Initialize the chat log watcher.

**Args:**
- `log_paths`: List of directories containing EVE chat logs

#### `start()`
Start monitoring chat logs.

#### `stop()`
Stop monitoring chat logs.

#### `add_channel(channel_name: str)`
Add a channel to monitor.

#### `remove_channel(channel_name: str)`
Remove a channel from monitoring.

---

## Usage Examples

### Basic Window Management

```python
from argus_overview.platform import get_window_manager

wm = get_window_manager()

# List all EVE windows
for window_id, title in wm.get_eve_windows():
    print(f"{window_id}: {title}")

# Activate a specific window
wm.activate_window(window_id)

# Move and resize
wm.move_window(window_id, x=0, y=0, w=1920, h=1080)
```

### Window Capture

```python
from argus_overview.platform import get_window_capture

capture = get_window_capture()
capture.start()

# Synchronous capture
image = capture.capture_window_sync(window_id, scale=0.5)
if image:
    image.save("screenshot.png")

# Async capture
request_id = capture.capture_window_async(window_id)
result = capture.get_result(timeout=1.0)
if result:
    req_id, win_id, image = result
    image.save("screenshot.png")

capture.stop()
```

### Intel Parsing and Alerts

```python
from argus_overview.intel import (
    IntelParser,
    AlertDispatcher,
    AlertConfig,
    ThreatLevel,
)

# Parse intel messages
parser = IntelParser()
report = parser.parse("HED-GP hostile Loki Sabre +5 heading 1DQ")

if report:
    print(f"System: {report.system}")
    print(f"Threat: {report.threat_level.value}")
    print(f"Ships: {report.ship_types}")
    print(f"Count: {report.hostile_count}")

# Set up alerts
config = AlertConfig(
    enabled=True,
    visual_border=True,
    audio=True,
    min_threat_level="warning",
    jumps_threshold=3,
)

dispatcher = AlertDispatcher(config=config)
dispatcher.alert_triggered.connect(lambda r, t: print(f"Alert: {t.value}"))

# Dispatch alert
if report:
    dispatcher.dispatch(report)
```

### Multi-Monitor Setup

```python
from argus_overview.platform import get_screen_manager

sm = get_screen_manager()

for monitor in sm.get_all_monitors():
    print(f"Monitor at ({monitor.x}, {monitor.y})")
    print(f"  Size: {monitor.width}x{monitor.height}")
    print(f"  Primary: {monitor.is_primary}")
```

---

## Platform-Specific Notes

### Linux

- Window management uses `xdotool` and `wmctrl`
- Screen capture uses ImageMagick `import` command
- Audio playback uses `paplay` (PulseAudio) or `aplay` (ALSA)
- Desktop notifications use `notify-send`
- EVE paths searched under Steam Proton compatdata

### Windows

- Window management uses Win32 API (`pywin32`)
- Screen capture uses GDI via `win32ui`
- EVE paths use `%LOCALAPPDATA%\CCP\EVE\`
- Audio playback uses Windows audio APIs

---

## Error Handling

All platform operations are designed to fail gracefully:

- Window operations return `False` on failure
- Capture operations return `None` on failure
- Path operations return empty lists if directories don't exist
- Audio/notification operations log warnings but don't raise exceptions

Always check return values when using platform APIs.
