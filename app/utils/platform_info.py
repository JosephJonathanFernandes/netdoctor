"""Platform / operating-system helpers for NetDoctor.

Isolates Windows-specific behaviour (netsh, ipconfig, ping, nslookup, tracert,
port checks) from the rest of the application so the code stays testable and
readable.
"""

from __future__ import annotations

import platform
import re
import shutil
import socket
import subprocess
from typing import Optional

import psutil


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def which(executable: str) -> str | None:
    """Return the full path to a system executable, or None if not found."""
    return shutil.which(executable)


def run_command(
    command: list[str],
    timeout: float = 10.0,
    capture_stderr: bool = True,
) -> subprocess.CompletedProcess:
    """Run an external command safely with a timeout (no shell=True)."""
    return subprocess.run(  # noqa: S603
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def run_command_output(command: list[str], timeout: float = 10.0) -> str | None:
    """Run a command and return its stdout, or None on any failure."""
    try:
        result = run_command(command, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def ping_host(
    host: str,
    count: int = 4,
    timeout: float = 5.0,
) -> dict:
    """Ping a host and return a defensive parse of the result.

    Returns keys: success, packets_sent, packets_received,
    packet_loss_percent, min_ms, avg_ms, max_ms, jitter_ms, raw, error.
    """
    result: dict = {
        "success": False,
        "packets_sent": 0,
        "packets_received": 0,
        "packet_loss_percent": None,
        "min_ms": None,
        "avg_ms": None,
        "max_ms": None,
        "jitter_ms": None,
        "raw": "",
        "error": None,
    }

    if not is_windows():
        result["error"] = "ping parsing is implemented for Windows"
        return result

    ping_exe = which("ping")
    if ping_exe is None:
        result["error"] = "ping.exe not found on PATH"
        return result

    cmd = [ping_exe, "-n", str(count), "-w", str(int(timeout * 1000)), host]
    try:
        proc = run_command(cmd, timeout=timeout + 5.0)
    except subprocess.TimeoutExpired as exc:
        result["error"] = f"ping timed out after {timeout}s"
        result["raw"] = str(exc)
        return result
    except OSError as exc:
        result["error"] = f"could not start ping: {exc}"
        return result

    raw = proc.stdout or ""
    result["raw"] = raw

    times: list[float] = []
    received = 0
    sent = 0

    for line in raw.splitlines():
        line = line.strip()
        if "Reply from" in line:
            received += 1
            sent += 1
            match = re.search(r"time[=<](\d+(?:\.\d+)?) ?ms", line, re.IGNORECASE)
            if match:
                times.append(float(match.group(1)))
        elif "Request timed out" in line or "Destination host unreachable" in line:
            sent += 1
        summary = re.search(r"Sent = (\d+), Received = (\d+), Lost = (\d+)", line, re.IGNORECASE)
        if summary:
            sent = int(summary.group(1))
            received = int(summary.group(2))

    result["packets_sent"] = sent
    result["packets_received"] = received
    if sent > 0:
        lost = sent - received
        result["packet_loss_percent"] = (lost / sent) * 100.0
    if times:
        result["success"] = received > 0
        result["min_ms"] = min(times)
        result["max_ms"] = max(times)
        result["avg_ms"] = sum(times) / len(times)
        if len(times) > 1:
            mean = result["avg_ms"]
            variance = sum((t - mean) ** 2 for t in times) / (len(times) - 1)
            result["jitter_ms"] = variance ** 0.5
        else:
            result["jitter_ms"] = 0.0
    elif sent == 0 and received == 0:
        result["error"] = "no ping replies parsed from output"
    return result


def traceroute_host(
    host: str,
    max_hops: int = 20,
    timeout: float = 15.0,
) -> dict:
    """Run tracert and return a defensive parse of hop information.

    Returns keys: success, hops (list of dicts), raw, error.
    Each hop: {hop, rtt_ms (list), host, ip}
    """
    result: dict = {"success": False, "hops": [], "raw": "", "error": None}
    if not is_windows():
        result["error"] = "traceroute is implemented for Windows (tracert)"
        return result
    tracert = which("tracert")
    if tracert is None:
        result["error"] = "tracert.exe not found on PATH"
        return result
    try:
        proc = run_command([tracert, "-h", str(max_hops), "-w", str(int(timeout * 1000)), host],
                           timeout=timeout + 10.0)
    except subprocess.TimeoutExpired:
        result["error"] = "traceroute timed out"
        return result
    except OSError as exc:
        result["error"] = f"could not start tracert: {exc}"
        return result

    raw = proc.stdout or ""
    result["raw"] = raw
    if proc.returncode != 0 and not raw:
        result["error"] = f"tracert failed (exit code {proc.returncode})"
        return result

    hop_re = re.compile(
        r"\s*(\d+)\s+.*?((?:\d+ms|\*|<1 ms)\s*(?:\d+ms|\*|<1 ms)?\s*(?:\d+ms|\*|<1 ms)?)\s+(.+)?"
    )
    for line in raw.splitlines():
        line = line.strip()
        m = hop_re.match(line)
        if not m:
            continue
        hop_num = int(m.group(1))
        rtt_str = m.group(2) or ""
        target = (m.group(3) or "").strip()
        rtts: list[float] = []
        for token in re.findall(r"(?:\d+)ms|<1 ms", rtt_str):  # noqa: S105
            if token == "<1 ms":
                rtts.append(0.5)
            else:
                rtts.append(float(token.replace("ms", "")))
        ip_match = re.search(r"\[([0-9]{1,3}(?:\.[0-9]{1,3}){3})\]", target)
        ip = ip_match.group(1) if ip_match else None
        host_name = target.split("[")[0].strip() if target else None
        if host_name == ip or not host_name:
            host_name = None
        result["hops"].append({
            "hop": hop_num,
            "rtt_ms": rtts,
            "host": host_name,
            "ip": ip,
        })
    result["success"] = len(result["hops"]) > 0
    return result


def check_port(host: str, port: int, timeout: float = 5.0) -> dict:
    """TCP port check. Returns {open, latency_ms, error}."""
    result: dict = {"open": False, "latency_ms": None, "error": None}
    try:
        start = __import__("time").time()
        with socket.create_connection((host, port), timeout=timeout):
            elapsed = (__import__("time").time() - start) * 1000.0
            result["open"] = True
            result["latency_ms"] = elapsed
    except OSError as exc:
        result["error"] = str(exc)
    return result


def get_default_gateway() -> str | None:
    """Return the IPv4 default gateway address on Windows via ipconfig, or None."""
    if not is_windows():
        return None
    ipconfig = which("ipconfig")
    if ipconfig is None:
        return None
    output = run_command_output([ipconfig], timeout=10.0)
    if not output:
        return None
    match = re.search(
        r"Default Gateway[ .:]*[^\r\n]*([0-9]{1,3}(?:\.[0-9]{1,3}){3})", output
    )
    return match.group(1) if match else None


def get_wifi_info() -> dict:
    """Attempt to retrieve Wi-Fi signal info via netsh on Windows."""
    info: dict = {
        "ssid": None,
        "signal_percent": None,
        "bssid": None,
        "channel": None,
        "available": False,
        "error": None,
    }
    if not is_windows():
        info["error"] = "Wi-Fi info is only available on Windows"
        return info
    netsh = which("netsh")
    if netsh is None:
        info["error"] = "netsh.exe not found on PATH"
        return info
    output = run_command_output([netsh, "wlan", "show", "interfaces"], timeout=10.0)
    if not output:
        info["error"] = "netsh wlan show interfaces returned no output"
        return info
    ssid_match = re.search(r"SSID\s*:\s*(.+)", output)
    signal_match = re.search(r"Signal\s*:\s*(\d+)%", output)
    bssid_match = re.search(r"BSSID\s*:\s*([0-9a-fA-F:-]+)", output)
    channel_match = re.search(r"Channel\s*:\s*(\d+)", output)
    if ssid_match:
        info["ssid"] = ssid_match.group(1).strip()
    if signal_match:
        info["signal_percent"] = int(signal_match.group(1))
    if bssid_match:
        info["bssid"] = bssid_match.group(1).strip()
    if channel_match:
        info["channel"] = int(channel_match.group(1))
    info["available"] = info["ssid"] is not None
    if not info["available"]:
        info["error"] = "no active Wi-Fi interface found"
    return info


def resolve_host(host: str, timeout: float = 10.0) -> dict:
    """Attempt DNS resolution of a host using nslookup on Windows."""
    result: dict = {"success": False, "addresses": [], "error": None, "raw": ""}
    if not is_windows():
        result["error"] = "nslookup resolution is implemented for Windows"
        return result
    nslookup = which("nslookup")
    if nslookup is None:
        result["error"] = "nslookup.exe not found on PATH"
        return result
    try:
        proc = run_command([nslookup, host], timeout=timeout)
    except subprocess.TimeoutExpired:
        result["error"] = "DNS resolution timed out"
        return result
    except OSError as exc:
        result["error"] = f"could not start nslookup: {exc}"
        return result

    raw = proc.stdout or ""
    result["raw"] = raw
    if proc.returncode == 0:
        addresses = re.findall(r"\b([0-9]{1,3}(?:\.[0-9]{1,3}){3})\b", raw)
        seen = set()
        unique = []
        for addr in addresses:
            if addr not in seen:
                seen.add(addr)
                unique.append(addr)
        result["addresses"] = unique
        result["success"] = len(unique) > 0
    else:
        result["error"] = f"nslookup failed (exit code {proc.returncode})"
    return result


def get_network_interfaces() -> list[dict]:
    """Return network interface information using psutil."""
    interfaces = []
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    counters = psutil.net_io_counters(pernic=True)
    for name, st in stats.items():
        iface = {
            "name": name,
            "isup": st.isup,
            "speed_mbps": st.speed,
            "mtu": st.mtu,
            "addresses": [],
            "bytes_sent": None,
            "bytes_recv": None,
        }
        for addr in addrs.get(name, []):
            iface["addresses"].append({
                "family": str(addr.family),
                "address": addr.address,
                "netmask": addr.netmask,
            })
        if name in counters:
            iface["bytes_sent"] = counters[name].bytes_sent
            iface["bytes_recv"] = counters[name].bytes_recv
        interfaces.append(iface)
    return interfaces
