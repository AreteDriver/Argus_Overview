# Intel Alert Sounds

Place audio files here for intel alerts. Supported formats: WAV, OGG.

## Expected Files

| File | Threat Level | Description |
|------|--------------|-------------|
| `info.wav` | INFO | Low priority intel |
| `warning.wav` | WARNING | Neutral/unknown hostiles |
| `danger.wav` | DANGER | Confirmed hostiles nearby |
| `critical.wav` | CRITICAL | Immediate threat |

## Requirements

- **Linux**: Requires `paplay` (PulseAudio) or `aplay` (ALSA)
- **Windows**: Uses Windows audio APIs (future)

## Custom Sounds

Set a custom audio file in Settings > Intel > Audio File to override defaults.

## Recommended Sources

- [Freesound.org](https://freesound.org/) - Free sound effects (check license)
- [OpenGameArt.org](https://opengameart.org/) - Game-ready audio assets
