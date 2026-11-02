# NetDoctor Implementation Plan

## Stack (verified installed)
- Python 3.14.2
- PySide6 6.12.0 (GUI)
- psutil 7.1.3 (system/network counters)
- matplotlib 3.10.7 (charts)
- speedtest-cli 2.1.3 (speed test backend)
- pytest 9.0.2 (tests)
- SQLite (stdlib) (persistence)

## Phases
Phase 1 — Core MVP: project structure, DB layer, speed-test worker/service, main window + sidebar,
Dashboard, Speed Test page, basic Diagnostics, history persistence, error handling.
Phase 2 — Monitoring: background monitoring worker + live graph, health score, rule-based recommendations.
Phase 3 — Polish: Settings page, system tray + notifications, CSV export, icon, launch script,
PyInstaller instructions, tests, README.

## Key design decisions
- speedtest-cli is the primary speed-test backend (download/upload/latency via speedtest.net).
- Jitter & packet loss are estimated separately via ICMP ping to a diagnostic target; they are
  labelled as estimates, never presented as speedtest.net-verified measurements.
- All network I/O runs in QThread workers so the GUI never blocks.
- SQLite DB auto-creates on first launch; schema version table for safe migrations.
- Dark theme by default; QSettings for local persistence.
- No cloud backend, API key, or user account required.
