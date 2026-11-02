# Contributing to NetDoctor

Thank you for your interest in contributing to NetDoctor! This guide explains how to get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code. Please report unacceptable behavior to the project maintainer.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/netdoctor.git
   cd netdoctor
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```
4. Run the app to verify it works:
   ```bash
   python main.py
   ```

## Development Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Implement your changes following the [coding standards](#coding-standards).
3. Add or update tests in the `tests/` directory.
4. Run the test suite:
   ```bash
   python -m pytest tests/
   ```
5. Run the application and manually verify your changes.
6. Commit with a descriptive message:
   ```bash
   git commit -m "feat: describe your change"
   ```
7. Push to your fork and open a pull request against `main`.

## Coding Standards

- Python 3.11+ syntax only
- Type hints on all public functions and methods
- Docstrings for all modules, classes, and public methods
- Max line length: 100 characters
- Use `pathlib` or `os.path` for path operations (no hardcoded Windows paths)
- All network I/O must run in background `QThread` workers — never block the GUI thread
- Never fabricate or hardcode sample data as live results
- Clearly label estimated metrics (ICMP jitter/packet loss, interface counters) vs verified measurements

## Testing

- Write unit tests for all new business logic (health score, recommendations, formatting, etc.)
- Mock external network operations — tests must not require an internet connection
- Use `pytest` and `pytest-qt` for GUI-related tests
- Aim for high coverage of the `app/services/` and `app/utils/` layers

```bash
python -m pytest tests/ -v
```

## Submitting Changes

1. Ensure all tests pass.
2. Update the README if your change affects features, installation, or usage.
3. Open a pull request from your feature branch to `main`.
4. Provide a clear description of the change and any manual verification performed.
5. Respond to maintainer review comments promptly.

## Reporting Issues

Use the GitHub issue tracker. When reporting a bug, include:
- NetDoctor version
- Windows version (10/11)
- Steps to reproduce
- Expected vs actual behavior
- Any error messages from the status bar or console

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
