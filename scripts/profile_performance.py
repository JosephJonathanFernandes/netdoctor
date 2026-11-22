"""Performance profiling script for NetDoctor.

Profiles memory usage and CPU time of the application during various operations.
Results are saved to a JSON report for analysis.

Usage:
    python scripts/profile_memory.py [--duration 60] [--output profile_memory.json]
    python scripts/profile_cpu.py [--duration 60] [--output profile_cpu.json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import tracemalloc
from datetime import datetime, timezone

import psutil


def profile_memory(duration_seconds: int = 60, output: str = "profile_memory.json") -> None:
    """Profile memory usage over a duration."""
    tracemalloc.start()
    process = psutil.Process(os.getpid())

    samples = []
    start_time = time.time()

    print(f"Profiling memory for {duration_seconds}s...")
    while time.time() - start_time < duration_seconds:
        mem_info = process.memory_info()
        current, peak = tracemalloc.get_traced_memory()
        samples.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_s": round(time.time() - start_time, 2),
            "rss_mb": round(mem_info.rss / 1024 / 1024, 2),
            "vms_mb": round(mem_info.vms / 1024 / 1024, 2),
            "tracemalloc_current_mb": round(current / 1024 / 1024, 2),
            "tracemalloc_peak_mb": round(peak / 1024 / 1024, 2),
        })
        time.sleep(1)

    tracemalloc.stop()

    report = {
        "profile_type": "memory",
        "duration_s": duration_seconds,
        "samples": samples,
        "summary": {
            "peak_rss_mb": round(max(s["rss_mb"] for s in samples), 2),
            "avg_rss_mb": round(sum(s["rss_mb"] for s in samples) / len(samples), 2),
            "peak_tracemalloc_mb": round(max(s["tracemalloc_peak_mb"] for s in samples), 2),
        },
    }

    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True) if os.path.dirname(output) else None
    with open(output, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    print(f"Memory profile saved to {output}")
    print(f"Peak RSS: {report['summary']['peak_rss_mb']} MB")
    print(f"Avg RSS: {report['summary']['avg_rss_mb']} MB")


def profile_cpu(duration_seconds: int = 60, output: str = "profile_cpu.json") -> None:
    """Profile CPU usage over a duration."""
    process = psutil.Process(os.getpid())

    samples = []
    start_time = time.time()

    print(f"Profiling CPU for {duration_seconds}s...")
    while time.time() - start_time < duration_seconds:
        cpu_percent = process.cpu_percent(interval=1)
        samples.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_s": round(time.time() - start_time, 2),
            "cpu_percent": cpu_percent,
        })

    report = {
        "profile_type": "cpu",
        "duration_s": duration_seconds,
        "samples": samples,
        "summary": {
            "peak_cpu_percent": round(max(s["cpu_percent"] for s in samples), 2),
            "avg_cpu_percent": round(sum(s["cpu_percent"] for s in samples) / len(samples), 2),
        },
    }

    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True) if os.path.dirname(output) else None
    with open(output, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    print(f"CPU profile saved to {output}")
    print(f"Peak CPU: {report['summary']['peak_cpu_percent']}%")
    print(f"Avg CPU: {report['summary']['avg_cpu_percent']}%")


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile NetDoctor performance")
    parser.add_argument("--duration", type=int, default=60, help="Profiling duration in seconds")
    parser.add_argument("--output", type=str, default="profile_report.json", help="Output file path")
    parser.add_argument("--type", choices=["memory", "cpu", "both"], default="both", help="Profile type")
    args = parser.parse_args()

    if args.type in ("memory", "both"):
        mem_out = args.output.replace(".json", "_memory.json") if args.output.endswith(".json") else args.output + "_memory.json"
        profile_memory(args.duration, mem_out)

    if args.type in ("cpu", "both"):
        cpu_out = args.output.replace(".json", "_cpu.json") if args.output.endswith(".json") else args.output + "_cpu.json"
        profile_cpu(args.duration, cpu_out)


if __name__ == "__main__":
    main()
