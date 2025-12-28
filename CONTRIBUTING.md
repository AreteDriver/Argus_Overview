# Contributing to EVE Veles Eyes

Thank you for your interest in contributing to EVE Veles Eyes!

## Getting Started

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/EVE_VelesEyes
   cd EVE_VelesEyes
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/AreteDriver/EVE_VelesEyes
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
EVE_VelesEyes/
├── src/
│   ├── main.py                    # Entry point
│   └── eve_overview_pro/
│       ├── core/                  # Business logic
│       │   ├── character_manager.py
│       │   ├── layout_manager.py
│       │   ├── alert_detector.py
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
- Relevant logs from `~/.config/eve-veles-eyes/eve-veles-eyes.log`

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

**Thank you for contributing to EVE Veles Eyes!**

Fly safe, capsuleer! o7
