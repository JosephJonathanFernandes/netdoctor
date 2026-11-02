"""Rule-based diagnostic recommendations engine.

Every recommendation identifies the evidence (measurement) that triggered it.
The engine never changes network configuration and never claims to detect
individual bandwidth-hogging processes unless per-process usage is measured.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Recommendation:
    title: str
    message: str
    evidence: str
    severity: str  # info | warning | critical
    category: str


class RecommendationsEngine:
    def build(
        self,
        latency_ms: Optional[float] = None,
        jitter_ms: Optional[float] = None,
        packet_loss_percent: Optional[float] = None,
        download_mbps: Optional[float] = None,
        upload_mbps: Optional[float] = None,
        wifi_signal_percent: Optional[int] = None,
        dns_ok: bool = True,
        reconnect_count: int = 0,
        gateway_ok: bool = True,
    ) -> list[Recommendation]:
        recs: list[Recommendation] = []

        # --- Latency ---
        if latency_ms is not None:
            if latency_ms > 100:
                recs.append(Recommendation(
                    title="High latency detected",
                    message=(
                        "Repeat the speed test and compare idle versus loaded "
                        "latency. If loaded latency is much higher, your link "
                        "may be saturated or experiencing bufferbloat."
                    ),
                    evidence=f"Latency {latency_ms:.1f} ms (>100 ms threshold)",
                    severity="warning",
                    category="latency",
                ))
            elif latency_ms > 50:
                recs.append(Recommendation(
                    title="Elevated latency",
                    message=(
                        "Latency is above the ideal range. Try testing closer to "
                        "your router, or switch from Wi-Fi to a wired connection "
                        "if available."
                    ),
                    evidence=f"Latency {latency_ms:.1f} ms (50-100 ms range)",
                    severity="info",
                    category="latency",
                ))

        # --- Jitter ---
        if jitter_ms is not None:
            if jitter_ms > 30:
                recs.append(Recommendation(
                    title="High jitter detected",
                    message=(
                        "High jitter can cause stutter in voice/video calls. "
                        "Use a wired connection, reduce Wi-Fi interference, or "
                        "enable QoS on your router if supported."
                    ),
                    evidence=f"Jitter {jitter_ms:.1f} ms (>30 ms threshold)",
                    severity="warning",
                    category="latency",
                ))
            elif jitter_ms > 15:
                recs.append(Recommendation(
                    title="Moderate jitter",
                    message=(
                        "Jitter is elevated. For sensitive applications, prefer "
                        "a wired connection and avoid large downloads during calls."
                    ),
                    evidence=f"Jitter {jitter_ms:.1f} ms (15-30 ms range)",
                    severity="info",
                    category="latency",
                ))

        # --- Packet loss ---
        if packet_loss_percent is not None:
            if packet_loss_percent > 5:
                recs.append(Recommendation(
                    title="High packet loss",
                    message=(
                        "Significant packet loss detected. Check Wi-Fi signal "
                        "strength, Ethernet cables, and the router. Repeat the "
                        "measurement to confirm it is persistent."
                    ),
                    evidence=f"Packet loss {packet_loss_percent:.1f}% (>5% threshold)",
                    severity="critical",
                    category="packet_loss",
                ))
            elif packet_loss_percent > 0.5:
                recs.append(Recommendation(
                    title="Moderate packet loss",
                    message=(
                        "Some packet loss detected. Check cables and Wi-Fi "
                        "signal, then re-test. If it persists, contact your ISP."
                    ),
                    evidence=f"Packet loss {packet_loss_percent:.1f}% (0.5-5% range)",
                    severity="warning",
                    category="packet_loss",
                ))

        # --- Wi-Fi signal ---
        if wifi_signal_percent is not None:
            if wifi_signal_percent < 40:
                recs.append(Recommendation(
                    title="Weak Wi-Fi signal",
                    message=(
                        "Move closer to the router, remove obstructions, or "
                        "investigate sources of interference (microwaves, other "
                        "networks on the same channel)."
                    ),
                    evidence=f"Wi-Fi signal {wifi_signal_percent}% (<40% threshold)",
                    severity="warning",
                    category="wifi",
                ))
            elif wifi_signal_percent < 60:
                recs.append(Recommendation(
                    title="Fair Wi-Fi signal",
                    message=(
                        "Wi-Fi signal is adequate but not strong. For the best "
                        "speed, move closer to the router or use Ethernet."
                    ),
                    evidence=f"Wi-Fi signal {wifi_signal_percent}% (40-60% range)",
                    severity="info",
                    category="wifi",
                ))

        # --- DNS ---
        if not dns_ok:
            recs.append(Recommendation(
                title="DNS resolution failure",
                message=(
                    "Compare DNS resolution using your configured DNS server "
                    "against a public resolver (e.g. 1.1.1.1). If the public "
                    "resolver works, your configured DNS may be the issue."
                ),
                evidence="DNS resolution failed for configured diagnostic host",
                severity="warning",
                category="dns",
            ))

        # --- Gateway ---
        if not gateway_ok:
            recs.append(Recommendation(
                title="Default gateway unreachable",
                message=(
                    "Your device cannot reach the local gateway. Check the "
                    "Ethernet cable or Wi-Fi association, restart the router, "
                    "and verify the network adapter is enabled."
                ),
                evidence="Default gateway not responding to ping",
                severity="critical",
                category="connectivity",
            ))

        # --- Stability ---
        if reconnect_count > 0:
            recs.append(Recommendation(
                title="Repeated disconnections observed",
                message=(
                    "Review the monitoring history for disconnect patterns and "
                    "inspect the router or ISP connection. Check for loose "
                    "cables or overheating equipment."
                ),
                evidence=f"{reconnect_count} reconnect(s) during monitoring",
                severity="warning" if reconnect_count > 2 else "info",
                category="stability",
            ))

        # --- Throughput ---
        if download_mbps is not None and download_mbps < 10:
            recs.append(Recommendation(
                title="Low download speed",
                message=(
                    "Download speed is below 10 Mbps. This may affect video "
                    "streaming and video calls. Consider upgrading your plan or "
                    "checking for background downloads."
                ),
                evidence=f"Download {download_mbps:.1f} Mbps (<10 Mbps)",
                severity="warning",
                category="throughput",
            ))

        # --- General ---
        if not recs:
            recs.append(Recommendation(
                title="No specific recommendations",
                message=(
                    "Your measurements look healthy. No action needed. "
                    "Run periodic tests to track changes over time."
                ),
                evidence="All measured metrics within acceptable ranges",
                severity="info",
                category="general",
            ))

        # Sort by severity
        order = {"critical": 0, "warning": 1, "info": 2}
        recs.sort(key=lambda r: order.get(r.severity, 9))
        return recs
