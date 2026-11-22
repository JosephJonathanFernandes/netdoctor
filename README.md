# NetDoctor

Professional Windows desktop application for one-click internet speed testing and network health monitoring.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://www.qt.io/)
[![SQLite](https://img.shields.io/badge/DB-SQLite-blue.svg)](https://www.sqlite.org/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-pytest-yellow.svg)](tests/)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-lightgrey.svg)](https://www.microsoft.com/windows)
[![i18n](https://img.shields.io/badge/i18n-EN%2FES%2FFR%2FDE-blue.svg)](app/translations/)

## Overview

**NetDoctor** makes testing your internet speed effortless. Open the app, click one button, and get real download/upload/latency results — no need to search Google for a speed test again.

Built as a genuine desktop product (not a web page in a window), NetDoctor combines a polished dark-themed PySide6 interface with real network measurements, SQLite persistence, live monitoring, diagnostics, and an explainable internet health score.

## Key Features

| Feature | Description |
|---------|-------------|
| **One-Click Speed Test** | Real download, upload, and latency via speedtest-cli (speedtest.net) with progressive results and cancellation |
| **Dashboard** | Connection status, last speeds, latency/jitter, session uptime, health score (0–100), smart recommendations |
| **Network Monitor** | Real-time interface traffic with live graph, configurable sampling interval |
| **Test History** | Sortable table, date filtering, historical graphs, averages/min/max, CSV & JSON export |
| **Diagnostics** | Reachability, default gateway, DNS, traceroute, port check, Wi-Fi info — plain-language findings |
| **Health Score** | Explainable 0–100 score with documented rules and trend analysis |
| **Smart Recommendations** | Evidence-tagged, rule-based suggestions prioritized by severity |
| **Alerts** | Threshold-based desktop notifications for latency, jitter, and packet loss |
| **Settings** | Dark/light theme, high contrast, monitoring interval, notifications, minimize-to-tray, start-on-boot, language selection |
| **Desktop Integration** | System tray, notifications, minimize-to-tray, clean shutdown, keyboard shortcuts |
| **Internationalization** | English, Spanish, French, German — translatable via Qt .ts/.qm files |
| **Accessibility** | High contrast mode, keyboard navigation (Ctrl+R/D/H/1/Q), screen reader support |
| **Auto-Updater** | Checks GitHub releases for new versions, downloads and stages updates |
| **Automatic Testing** | Scheduled background speed tests at configurable intervals |
| **Backup & Restore** | SQLite database backup and restore with verification |
| **CLI** | Headless `netdoctor` command for automation (run-test, history, export, stats, check, update, version) |
| **Reports** | Professional HTML and PDF reports from test history |

## Technology Stack

- **Language:** Python 3.11+
- **GUI:** PySide6
- **Database:** SQLite (stdlib)
- **Charts:** Matplotlib
- **System Monitoring:** psutil
- **Speed Testing:** speedtest-cli
- **Internationalization:** Qt .ts/.qm translation files
- **Testing:** pytest + pytest-qt
- **Notifications:** win10toast
- **Packaging:** PyInstaller + Inno Setup (MSI)

No cloud backend, API key, or user account is required for core features. All data stays on your computer.

## Repository Structure

```
netdoctor/
├── main.py                 # Application entry point
├── run.bat                 # Windows launch script
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT License
├── README.md               # This file
├── CONTRIBUTING.md         # Contribution guidelines
├── CODE_OF_CONDUCT.md      # Community code of conduct
├── SECURITY.md             # Security policy
├── PLAN.md                 # Implementation plan
├── ARCHITECTURE.md         # Architecture & design documentation
├── pyproject.toml          # Project configuration
├── .pre-commit-config.yaml # Pre-commit hooks
├── NetDoctor.spec          # PyInstaller spec
├── installer/
│   └── netdoctor.iss       # Inno Setup installer script
├── scripts/
│   ├── code-sign.ps1       # Authenticode code signing script
│   └── profile_performance.py  # Memory/CPU profiling
├── app/
│   ├── __init__.py
│   ├── __main__.py         # python -m netdoctor entry point
│   ├── cli.py              # Headless CLI
│   ├── config.py           # Constants and paths
│   ├── exceptions.py       # Custom exception hierarchy
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py           # SQLite connection & schema migrations
│   │   └── repository.py   # Data access + CSV/JSON export
│   ├── services/
│   │   ├── __init__.py
│   │   ├── speed_test.py   # Speed-test orchestration
│   │   ├── diagnostics.py  # Network diagnostic checks
│   │   ├── health_score.py # 0–100 health score with trends
│   │   ├── recommendations # Rule-based suggestions
│   │   ├── notifications   # Desktop toast notifications
│   │   ├── report_export   # HTML/PDF report generation
│   │   ├── scheduler       # Automatic background speed tests
│   │   ├── backup          # Database backup & restore
│   │   └── updater         # GitHub release auto-updater
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py  # Shell: sidebar, pages, tray, notifications
│   │   ├── dashboard.py
│   │   ├── speed_test_page.py
│   │   ├── monitor_page.py
│   │   ├── history_page.py
│   │   ├── diagnostics_page.py
│   │   ├── settings_page.py
│   │   ├── theme.py        # Glassmorphism QSS dark/light/high-contrast theme
│   │   ├── chart.py        # Matplotlib canvas widget
│   │   └── widgets.py      # Shared stat tiles
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── formatting.py   # Unit formatting helpers
│   │   ├── platform_info.py# Windows ping/ipconfig/netsh/nslookup/tracert
│   │   ├── settings.py     # Pydantic QSettings wrapper
│   │   └── logging.py      # Structured logging with rotation
│   ├── translations/
│   │   ├── netdoctor_es.ts/.qm   # Spanish translation
│   │   ├── netdoctor_fr.ts/.qm   # French translation
│   │   └── netdoctor_de.ts/.qm   # German translation
│   └── workers/
│       ├── __init__.py
│       ├── speed_test_worker.py
│       └── monitoring_worker.py
├── docs/
│   └── REMAINING_POLISH.md   # Remaining polish plan
└── tests/
    ├── __init__.py
    ├── test_database.py
    ├── test_exceptions.py
    ├── test_formatting.py
    ├── test_gui.py
    ├── test_health_score.py
    ├── test_integration.py
    ├── test_logging.py
    ├── test_platform_info.py
    ├── test_recommendations.py
    └── test_speed_test.py
```

## Installation & Usage

### Prerequisites

- Windows 10 or Windows 11
- Python 3.11+ (with "Add Python to PATH" checked during install)

### Run from Source

```bash
# Clone the repository
git clone https://github.com/JosephJonathanFernandes/netdoctor.git
cd netdoctor

# Install dependencies
python -m pip install -r requirements.txt

# Launch the application
python main.py
```

### Windows Launch Script

Double-click `run.bat`. It installs dependencies and launches NetDoctor.

### Build Standalone Executable

```bash
python -m pip install pyinstaller
python -m PyInstaller --noconsole --onefile --name NetDoctor main.py
```

The output is in `dist/NetDoctor.exe`.

### MSI Installer

For distribution, an Inno Setup installer script is provided at `installer/netdoctor.iss`. Install [Inno Setup](https://jrsoftware.org/isinfo.php) and run:

```bash
iscc installer/netdoctor.iss
```

This produces `installer/output/NetDoctor-Setup-2.0.0.exe`.

### Code Signing

To sign the executable for Windows SmartTrust:

```powershell
.\scripts\code-sign.ps1 -File "dist\NetDoctor.exe" -CertificatePath "cert.pfx" -CertificatePassword "your-password"
```

## Internationalization (i18n)

NetDoctor supports multiple languages via Qt translation files:

| Language | Code | File |
|----------|------|------|
| English | `en` | Source (no translation needed) |
| Spanish | `es` | `app/translations/netdoctor_es.qm` |
| French | `fr` | `app/translations/netdoctor_fr.qm` |
| German | `de` | `app/translations/netdoctor_de.qm` |

Change the language in **Settings → Appearance → Language**. To add a new language:

1. Copy `app/translations/netdoctor_es.ts` to `netdoctor_<code>.ts`
2. Translate the strings
3. Compile: `pyside6-lrelease netdoctor_<code>.ts -qm netdoctor_<code>.qm`
4. Add the locale to `SUPPORTED_LOCALES` in `app/config.py`

## Accessibility

- **High contrast mode:** Enable in **Settings → Appearance → High contrast mode**
- **Keyboard shortcuts:**
  - `Ctrl+R` — Run Speed Test
  - `Ctrl+D` — Run Diagnostics
  - `Ctrl+H` — Show History
  - `Ctrl+1` — Show Dashboard
  - `Ctrl+Q` — Quit
- **Screen reader:** All buttons have accessible names and descriptions

## Command Line Interface (CLI)

NetDoctor includes a headless CLI for automation:

```bash
python -m app.cli version          # Show version
python -m app.cli check            # Check internet connectivity
python -m app.cli run-test         # Run a single speed test
python -m app.cli run-test --save  # Run and save to database
python -m app.cli history          # Show recent test history
python -m app.cli export report.csv --format csv  # Export to CSV
python -m app.cli stats            # Show aggregate statistics
python -m app.cli update           # Check for updates
```

Install as a console script: `python -m pip install -e .` then run `netdoctor <command>`.

## Performance Profiling

Profile memory and CPU usage:

```bash
python scripts/profile_performance.py --duration 60 --type both
```

Reports are saved as JSON files for analysis.

## Running Tests

All tests mock external network operations, so no internet connection is required:

```bash
python -m pytest tests/
```

## Data & Privacy

- All data stays on your computer
- Speed tests contact speedtest.net directly; diagnostic pings use public hosts (e.g. 1.1.1.1)
- Results stored in local SQLite at `%LOCALAPPDATA%\NetDoctor\netdoctor.db`
- No telemetry, no accounts, no cloud backend

## Important Design Notes

- **Interface counters ≠ internet throughput.** The Network Monitor labels psutil counters as interface traffic (local + internet), distinct from verified speed-test measurements.
- **Packet loss / jitter are ICMP estimates** toward 1.1.1.1, labelled as estimates — not speedtest-verified measurements.
- **No automatic ISP blame.** Diagnostics present confirmed observations and possible causes only.
- **No per-process monitoring.** The app does not claim to identify individual bandwidth-hogging processes.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to NetDoctor.

## License

NetDoctor is licensed under the [MIT License](LICENSE).

---

Built with ❤️ for Windows users who just want to know their internet speed — without Googling it.
