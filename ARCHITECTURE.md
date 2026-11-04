# NetDoctor Architecture

## Overview

NetDoctor is a single-process, single-window Windows desktop application written
in Python with PySide6. It follows a layered architecture that cleanly
separates UI, business logic, networking, persistence, and cross-cutting
concerns (logging, configuration, exceptions).

## Layers

```
┌─────────────────────────────────────────────────────────┐
│  Presentation Layer (PySide6)                           │
│  app/ui/  –  windows, pages, widgets, theme, charts     │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  Application Layer                                      │
│  app/ui/main_window.py  –  shell, tray, navigation      │
│  app/services/  –  business logic (speed test, diag…)   │
│  app/workers/   –  QThread background workers           │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  Data Access Layer                                      │
│  app/database/  –  SQLite connection, repositories      │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  Utility Layer                                          │
│  app/utils/   –  formatting, platform info, logging…    │
│  app/exceptions.py – custom exception hierarchy         │
│  app/config.py     – constants and paths                │
└─────────────────────────────────────────────────────────┘
```

## Design Principles

- **No GUI thread blocking.** All network I/O and disk I/O run in
  `QThread`-based workers. Results are marshaled back to the GUI thread
  via PySide6 signals.
- **Fail safely.** Network failures, missing executables (ping, nslookup,
  tracert), and database errors are caught, logged, and surfaced to the
  user in plain language. The app never crashes on a bad ping.
- **No fabricated data.** All measurements come from real system calls or
  speedtest-cli. Missing data is shown as "n/a" or "incomplete," never
  hardcoded.
- **Explainable outputs.** Health scores, recommendations, and diagnostic
  findings include the evidence that produced them.
- **Observable.** Structured logging with rotation; desktop notifications
  for test completion and threshold alerts.

## Key Components

| Component | Responsibility |
|-----------|---------------|
| `MainWindow` | Shell, navigation, tray, notifications, shutdown |
| `SpeedTestService` | Orchestrates connectivity → server → DL/UL → jitter → loss |
| `SpeedTestWorker` / `MonitoringWorker` | QThread wrappers |
| `DiagnosticsService` | ipconfig/ping/nslookup/tracert/port checks |
| `HealthScoreService` | Explainable 0–100 score with documented rules |
| `RecommendationsEngine` | Evidence-tagged, severity-ranked suggestions |
| `SpeedTestRepository` / `MonitoringRepository` / `AlertRepository` | SQLite CRUD |
| `Settings` | QSettings wrapper with typed accessors |
| `Database` | SQLite connection with schema migrations |

## Threading Model

All long-running work is confined to `QThread` subclasses. The GUI thread
only handles user input, signal-slot dispatch, and rendering. Workers
communicate results via `pyqtSignal`, which PySide6 automatically queues
to the GUI thread.

## Data Storage

SQLite database (WAL mode) at `%LOCALAPPDATA%\NetDoctor\netdoctor.db`.
Tables: `speed_tests`, `monitoring_samples`, `alerts`, `schema_version`.
Schema versioning enables safe migrations.
