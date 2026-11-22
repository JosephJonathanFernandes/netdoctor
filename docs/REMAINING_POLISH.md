# NetDoctor — Remaining Polish Implementation Plan

## P0 — Code Signing
- Create `scripts/code-sign.ps1` PowerShell script for Authenticode signing
- Add `app.manifest` for Windows application manifest
- Document certificate requirements and CI signing workflow
- Add `signtool` integration to release.yml

## P0 — Auto-updater End-to-End Test
- Add `--test-update` flag to CLI for simulating update flow
- Add `test_updater.py` unit test with mocked GitHub API
- Document release creation and testing procedure

## P1 — MSI Installer (Inno Setup)
- Create `installer/netdoctor.iss` Inno Setup script
- Configure installation directory, shortcuts, file associations
- Add uninstaller and upgrade support
- Document build process

## P1 — Internationalization (i18n)
- Wrap all user-facing strings with `tr()` / `QCoreApplication.translate`
- Create `.ts` translation files for es, fr, de
- Add language selector to Settings page
- Load translations at startup

## P2 — Accessibility Audit
- Add `QAccessible` roles and descriptions to all widgets
- Add high-contrast theme support
- Ensure keyboard navigation (tab order) works
- Add screen reader announcements for test completion

## P2 — Performance Profiling
- Add `scripts/profile_memory.py` and `scripts/profile_cpu.py`
- Document profiling procedure
- Add memory usage monitoring in MonitoringWorker

## P3 — Screenshots / Demo
- Document screenshot capture procedure
- Add `docs/screenshots/` placeholder structure
- Create demo script outline
