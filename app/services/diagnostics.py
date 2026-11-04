"""Network diagnostics service for NetDoctor.

Runs real checks using Windows system commands (ipconfig, ping, nslookup, tracert)
and the standard library. Every finding is labelled as an observation or a
possible cause -- the engine never automatically blames the ISP from a single
failed ping.
"""

from __future__ import annotations

import logging
import socket
import time
from typing import Optional

from app.config import DIAGNOSTIC_HOSTS, DNS_HOSTS
from app.exceptions import DiagnosticError
from app.utils.logging import get_logger
from app.utils.platform_info import (
    check_port,
    get_default_gateway,
    get_network_interfaces,
    get_wifi_info,
    ping_host,
    resolve_host,
    traceroute_host,
)

logger = get_logger(__name__)


class DiagnosticsService:
    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    def run_full_diagnostics(self) -> dict:
        logger.info("Starting full diagnostics suite")
        findings = []
        try:
            findings.append(self._check_internet_reachability())
            findings.append(self._check_default_gateway())
            findings.append(self._check_dns_resolution())
            findings.append(self._check_latency())
            findings.append(self._check_jitter())
            findings.append(self._check_packet_loss())
            findings.append(self._check_traceroute())
            findings.append(self._check_port_443())
            findings.append(self._check_network_interfaces())
            findings.append(self._check_wifi())
        except Exception as exc:
            logger.exception("Diagnostics suite failed unexpectedly")
            raise DiagnosticError(f"Diagnostics failed: {exc}") from exc

        summary = self._summarize(findings)
        logger.info("Diagnostics complete: %d checks", len(findings))
        return {"findings": findings, "summary": summary}

    # -- checks -- #
    def _check_internet_reachability(self) -> dict:
        observations = []
        possible_causes = []
        ok = False
        for host, port in [("1.1.1.1", 443), ("8.8.8.8", 443)]:
            try:
                with socket.create_connection((host, port), timeout=self.timeout):
                    ok = True
                    observations.append(f"Reachable {host}:{port}")
                    break
            except OSError:
                observations.append(f"Could not connect to {host}:{port}")
        if not ok:
            possible_causes.append(
                "No external connectivity. Possible causes: router offline, "
                "ISP outage, or a firewall blocking outbound TCP/443."
            )
        else:
            observations.append("External internet connectivity appears to be working.")
        return {
            "category": "connectivity",
            "title": "Internet reachability",
            "status": "pass" if ok else "fail",
            "observations": observations,
            "possible_causes": possible_causes,
        }

    def _check_default_gateway(self) -> dict:
        observations = []
        possible_causes = []
        gateway = get_default_gateway()
        status = "fail"
        if gateway is None:
            observations.append("Default gateway could not be discovered via ipconfig.")
            possible_causes.append(
                "No active network interface, or ipconfig output could not be parsed."
            )
        else:
            observations.append(f"Default gateway: {gateway}")
            ping = ping_host(gateway, count=3, timeout=3.0)
            if ping["success"]:
                status = "pass"
                observations.append(
                    f"Default gateway is reachable (avg {ping['avg_ms']:.1f} ms)."
                )
            else:
                observations.append("Default gateway is not responding to ping.")
                possible_causes.append(
                    "Local network issue: bad cable, weak Wi-Fi, or router "
                    "not responding to ICMP."
                )
        return {
            "category": "gateway",
            "title": "Default gateway",
            "status": status,
            "observations": observations,
            "possible_causes": possible_causes,
            "gateway": gateway,
        }

    def _check_dns_resolution(self) -> dict:
        observations = []
        possible_causes = []
        resolved_any = False
        for host in DNS_HOSTS:
            result = resolve_host(host, timeout=self.timeout)
            if result["success"]:
                resolved_any = True
                addrs = ", ".join(result["addresses"][:3]) or "n/a"
                observations.append(f"Resolved {host} -> {addrs}")
            else:
                observations.append(f"DNS resolution failed for {host}.")
                possible_causes.append(
                    f"The configured DNS server could not resolve {host}. "
                    "Possible causes: misconfigured DNS, DNS server offline, "
                    "or network blocking DNS queries."
                )
        status = "pass" if resolved_any else "fail"
        if resolved_any:
            observations.append("DNS resolution is working for at least one host.")
        return {
            "category": "dns",
            "title": "DNS resolution",
            "status": status,
            "observations": observations,
            "possible_causes": possible_causes,
        }

    def _check_latency(self) -> dict:
        ping = ping_host(DIAGNOSTIC_HOSTS[0], count=4, timeout=5.0)
        observations = []
        possible_causes = []
        if ping["success"]:
            status = "pass"
            observations.append(
                f"Latency to {DIAGNOSTIC_HOSTS[0]}: avg {ping['avg_ms']:.1f} ms "
                f"(min {ping['min_ms']:.1f}, max {ping['max_ms']:.1f})."
            )
            if ping["max_ms"] and ping["min_ms"] and (ping["max_ms"] - ping["min_ms"]) > 50:
                possible_causes.append(
                    "Latency varies considerably during this test, which can "
                    "indicate congestion or an unstable connection."
                )
        else:
            status = "fail"
            observations.append(f"Could not measure latency to {DIAGNOSTIC_HOSTS[0]}.")
            possible_causes.append(
                "No reply from the diagnostic host. This may be ICMP being "
                "blocked rather than an actual connectivity problem."
            )
        return {
            "category": "latency",
            "title": "Latency",
            "status": status,
            "observations": observations,
            "possible_causes": possible_causes,
            "avg_ms": ping.get("avg_ms"),
        }

    def _check_jitter(self) -> dict:
        ping = ping_host(DIAGNOSTIC_HOSTS[0], count=10, timeout=5.0)
        observations = []
        possible_causes = []
        if ping["success"] and ping.get("jitter_ms") is not None:
            status = "pass"
            jitter = ping["jitter_ms"]
            observations.append(
                f"Jitter estimate over {ping['packets_received']} replies: "
                f"{jitter:.1f} ms."
            )
            if jitter > 30:
                status = "warn"
                possible_causes.append(
                    "Elevated jitter can cause stutter in voice/video calls. "
                    "Repeat the test and compare idle versus loaded latency."
                )
        else:
            status = "fail"
            observations.append("Could not estimate jitter (no successful replies).")
        return {
            "category": "jitter",
            "title": "Jitter",
            "status": status,
            "observations": observations,
            "possible_causes": possible_causes,
            "jitter_ms": ping.get("jitter_ms"),
        }

    def _check_packet_loss(self) -> dict:
        ping = ping_host(DIAGNOSTIC_HOSTS[0], count=10, timeout=5.0)
        observations = []
        possible_causes = []
        if ping["success"]:
            loss = ping.get("packet_loss_percent") or 0.0
            observations.append(
                f"Packet-loss estimate to {DIAGNOSTIC_HOSTS[0]}: {loss:.1f}% "
                f"({ping['packets_received']} of {ping['packets_sent']} replies)."
            )
            if loss > 0:
                possible_causes.append(
                    "Packet loss detected. Check Wi-Fi signal strength, "
                    "cables, and the router; then repeat the measurement."
                )
        else:
            observations.append(
                f"Could not estimate packet loss to {DIAGNOSTIC_HOSTS[0]} "
                "(no replies). ICMP may be blocked."
            )
            loss = None
        return {
            "category": "packet_loss",
            "title": "Packet loss (ICMP estimate)",
            "status": "pass" if ping["success"] else "fail",
            "observations": observations,
            "possible_causes": possible_causes,
            "packet_loss_percent": loss,
            "note": (
                "ICMP-based estimate toward 1.1.1.1; not a measurement toward "
                "the speed-test server."
            ),
        }

    def _check_traceroute(self) -> dict:
        observations = []
        possible_causes = []
        trace = traceroute_host(DIAGNOSTIC_HOSTS[0], max_hops=15, timeout=15.0)
        if trace["success"]:
            hops = trace["hops"]
            observations.append(
                f"Traceroute to {DIAGNOSTIC_HOSTS[0]}: {len(hops)} hop(s) traced."
            )
            for hop in hops[:5]:
                rtts = hop["rtt_ms"]
                rtt_str = ", ".join(f"{r:.1f}ms" for r in rtts) if rtts else "*"
                observations.append(
                    f"  Hop {hop['hop']}: {rtt_str} ({hop['host'] or hop['ip'] or 'n/a'})"
                )
            for hop in hops:
                if hop["rtt_ms"] and max(hop["rtt_ms"]) > 100:
                    possible_causes.append(
                        f"Elevated latency at hop {hop['hop']} "
                        f"({max(hop['rtt_ms']):.0f} ms)."
                    )
                    break
            status = "pass"
        else:
            status = "fail"
            observations.append(f"Could not trace route to {DIAGNOSTIC_HOSTS[0]}.")
            possible_causes.append(
                "ICMP traceroute may be blocked by a firewall along the path."
            )
        return {
            "category": "traceroute",
            "title": "Traceroute",
            "status": status,
            "observations": observations,
            "possible_causes": possible_causes,
        }

    def _check_port_443(self) -> dict:
        observations = []
        possible_causes = []
        check = check_port("1.1.1.1", 443, timeout=self.timeout)
        if check["open"]:
            status = "pass"
            observations.append(
                f"HTTPS port (443) on 1.1.1.1 is open "
                f"({check['latency_ms']:.0f} ms)."
            )
        else:
            status = "fail"
            observations.append("HTTPS port (443) on 1.1.1.1 is not reachable.")
            possible_causes.append(
                "Outbound TCP/443 may be blocked by a firewall or security software."
            )
        return {
            "category": "port_443",
            "title": "HTTPS port (443)",
            "status": status,
            "observations": observations,
            "possible_causes": possible_causes,
        }

    def _check_network_interfaces(self) -> dict:
        observations = []
        try:
            interfaces = get_network_interfaces()
            count = 0
            for iface in interfaces:
                count += 1
                state = "up" if iface["isup"] else "down"
                speed = f"{iface['speed_mbps']} Mbps" if iface["speed_mbps"] else "unknown"
                observations.append(
                    f"Interface '{iface['name']}': {state}, speed {speed}, MTU {iface['mtu']}"
                )
                for addr in iface["addresses"][:2]:
                    observations.append(f"  {addr['family']}: {addr['address']}")
            if count == 0:
                observations.append("No network interfaces found.")
        except Exception as exc:
            logger.exception("Failed to enumerate network interfaces")
            observations.append(f"Could not enumerate interfaces: {exc}")
        return {
            "category": "interfaces",
            "title": "Network interfaces",
            "status": "pass" if observations else "fail",
            "observations": observations,
            "possible_causes": [],
        }

    def _check_wifi(self) -> dict:
        observations = []
        possible_causes = []
        info = get_wifi_info()
        if not info["available"]:
            observations.append(info.get("error") or "Wi-Fi information unavailable.")
            observations.append(
                "Wi-Fi signal information is unavailable for this network interface."
            )
            possible_causes.append(
                "The active interface may be wired Ethernet, or the Wi-Fi "
                "adapter does not expose signal info through netsh."
            )
            status = "fail"
        else:
            status = "pass"
            observations.append(f"Wi-Fi SSID: {info['ssid']}")
            if info.get("signal_percent") is not None:
                observations.append(f"Signal strength: {info['signal_percent']}%")
                if info["signal_percent"] < 40:
                    possible_causes.append(
                        "Weak Wi-Fi signal. Move closer to the router or "
                        "investigate interference."
                    )
            if info.get("bssid"):
                observations.append(f"BSSID: {info['bssid']}")
            if info.get("channel"):
                observations.append(f"Channel: {info['channel']}")
        return {
            "category": "wifi",
            "title": "Wi-Fi connection",
            "status": status,
            "observations": observations,
            "possible_causes": possible_causes,
        }

    def _summarize(self, findings: list[dict]) -> str:
        failed = [f for f in findings if f["status"] == "fail"]
        warned = [f for f in findings if f["status"] == "warn"]
        if not failed and not warned:
            return ("No obvious problems detected. All checks passed. "
                    "Performance may still vary with server and load.")
        parts = []
        if failed:
            parts.append(f"Checks needing attention: {', '.join(f['title'] for f in failed)}.")
        if warned:
            parts.append(f"Advisory: {', '.join(f['title'] for f in warned)}.")
        parts.append(
            "These are observations, not a definitive ISP diagnosis. A single "
            "failed endpoint does not prove the ISP is at fault."
        )
        return " ".join(parts)
