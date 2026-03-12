# Contributing to Argus Overview

Thank you for your interest in contributing to Argus Overview!

## Getting Started

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Argus_Overview
   cd Argus_Overview
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/AreteDriver/Argus_Overview
   ```

### Development Setup

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install wmctrl xdotool imagemagick x11-apps python3-pip python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install ruff black isort pytest pytest-cov

# Run in development mode
python src/main.py --debug
```

### Project Structure

```
Argus_Overview/
├── src/
│   ├── main.py                    # Entry point
│   └── eve_overview_pro/
│       ├── core/                  # Business logic
│       │   ├── character_manager.py
│       │   ├── layout_manager.py
│       │   ├── position.py
│       │   └── ...
│       ├── ui/                    # UI components
│       │   ├── main_window_v21.py
│       │   ├── main_tab.py
│       │   └── ...
│       └── utils/                 # Utilities
├── assets/                        # Icons and images
├── docs/                          # Documentation
└── windows/                       # Windows-specific code
```

## Code Style

### Python Style

- Follow PEP 8
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use meaningful variable names

### Formatting

We use `black` for formatting and `isort` for import sorting:

```bash
# Format code
black src/

# Sort imports
isort src/

# Check for issues
ruff check src/
```

### Pre-commit Checks

Before committing, run:

```bash
# Format and lint
black src/ && isort src/ && ruff check src/

# Run tests (when available)
pytest tests/ -v
```

## Making Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring

### Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

Examples:
```
feat(tray): add minimize-to-tray option
fix(discovery): handle missing wmctrl gracefully
docs(readme): update installation instructions
```

## Submitting Changes

1. Ensure your code follows the style guidelines
2. Update documentation if needed
3. Create a pull request with a clear description
4. Link any related issues

### Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update WHATS_NEW.md for new features
3. The PR will be merged once approved by a maintainer

## Reporting Issues

### Bug Reports

Use the bug report template and include:

- Clear description of the bug
- Steps to reproduce
- Expected behavior
- Environment details (OS, Python version, etc.)
- Relevant logs from `~/.config/argus-overview/argus-overview.log`

### Feature Requests

Use the feature request template and include:

- Problem description
- Proposed solution
- Use case for EVE multi-boxing

## Testing

### Manual Testing

Test your changes with:

1. Multiple EVE windows running
2. Different window configurations
3. Various screen resolutions
4. Both X11 and Wayland (if possible)

### Automated Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src/

# Run specific test
pytest tests/test_character_manager.py -v
```

## Areas for Contribution

### Good First Issues

- Documentation improvements
- Bug fixes with clear reproduction steps
- UI polish and improvements
- Translation support

### Larger Projects

- Wayland native support
- Additional grid layout patterns
- Plugin system
- Cloud sync for profiles

### High Impact Contributions

These are named opportunities for contributors who want to make a significant impact:

**Cross-Platform Port (Qt/Rust)**

The EVE community has expressed interest in a fully cross-platform rewrite that would bring native Mac support and eliminate X11 dependencies on Linux. This is the highest-impact contribution opportunity in the project.

**Language options:**
- **Qt/C++** — Closest to current PySide6 architecture, minimal UI redesign
- **Rust + egui/iced** — Modern, high-performance, single binary distribution
- **Go + Fyne** — Simple cross-platform GUI, fast compile times

**What the architecture must preserve:**
- Platform abstraction layer (`platform/base.py` defines the interface)
- Window capture and preview rendering pipeline
- Hotkey system (global hotkeys, per-character bindings, cycling groups)
- Profile/layout persistence (JSON-based settings)
- Intel channel parser (regex-based, portable as-is)

**Where to start:**
1. Read `docs/ARCHITECTURE.md` and `src/argus_overview/platform/base.py` for the abstraction contract
2. Prototype window enumeration + capture on your target platform
3. Open an issue to discuss your approach before building the full port
4. Proof of concept: list EVE windows + render one preview thumbnail

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- We're all capsuleers here! o7

## Getting Help

- Check existing issues and documentation
- Ask questions in issue discussions
- Join our Discord (when available)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Argus Overview!**

Fly safe, capsuleer! o7
