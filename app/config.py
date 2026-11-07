"""Application constants and configuration for NetDoctor."""

from __future__ import annotations

import os

APP_NAME = "NetDoctor"
APP_VERSION = "2.0.0"
ORGANIZATION = "NetDoctor"
APPLICATION = "NetDoctor"

# GitHub repo for auto-updater (owner/repo)
GITHUB_REPO = "JosephJonathanFernandes/netdoctor"

# Default diagnostic hosts
DIAGNOSTIC_HOST = "1.1.1.1"
DIAGNOSTIC_HOSTS = ["1.1.1.1", "8.8.8.8", "1.0.0.1"]
DNS_HOSTS = ["one.one.one.one", "dns.google", "google.com"]

# Speed test defaults
SPEEDTEST_TIMEOUT = 60.0
CONNECTIVITY_TIMEOUT = 5.0

# Health score weights (must sum to 100)
WEIGHT_LATENCY = 25
WEIGHT_JITTER = 20
WEIGHT_PACKET_LOSS = 25
WEIGHT_STABILITY = 15
WEIGHT_THROUGHPUT = 15  # considered separately but contributes to overall feel

# Database
DEFAULT_DB_NAME = "netdoctor.db"

# Default paths
def get_app_data_dir() -> str:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "NetDoctor")
    return os.path.join(os.path.expanduser("~"), ".local", "share", "netdoctor")

def get_default_db_path() -> str:
    return os.path.join(get_app_data_dir(), DEFAULT_DB_NAME)

# Chart colors
CHART_COLOR_PRIMARY = "#89b4fa"
CHART_COLOR_SUCCESS = "#a6e3a1"
CHART_COLOR_WARNING = "#f9e2af"
CHART_COLOR_ERROR = "#f38ba8"
