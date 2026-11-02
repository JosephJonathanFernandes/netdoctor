"""Internet health score: an explainable 0-100 rating.

Rule-based and documented. NOT an industry-standard rating. Missing measurements
produce an 'incomplete' assessment rather than treating missing data as perfect.
Throughput is considered separately from the core score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.utils.formatting import clamp, format_ms, format_percent


@dataclass
class HealthScore:
    score: Optional[int]
    complete: bool
    breakdown: dict
    factors: list[str]
    message: str
    trend: Optional[str] = None  # "improving" | "declining" | "stable"


class HealthScoreService:
    MAX_LATENCY = 25
    MAX_JITTER = 20
    MAX_PACKET_LOSS = 25
    MAX_STABILITY = 15
    MAX_THROUGHPUT = 15

    def compute(
        self,
        latency_ms: Optional[float] = None,
        jitter_ms: Optional[float] = None,
        packet_loss_percent: Optional[float] = None,
        reconnect_count: int = 0,
        download_mbps: Optional[float] = None,
        upload_mbps: Optional[float] = None,
        previous_score: Optional[int] = None,
    ) -> HealthScore:
        breakdown = {}
        factors = []

        lp, lr = self._score_latency(latency_ms)
        breakdown["latency"] = {"points": lp, "max": self.MAX_LATENCY, "reason": lr, "value": latency_ms}
        factors.append(f"Latency {format_ms(latency_ms)} -> {lp}/{self.MAX_LATENCY} pts" if latency_ms is not None else "Latency not measured")

        jp, jr = self._score_jitter(jitter_ms)
        breakdown["jitter"] = {"points": jp, "max": self.MAX_JITTER, "reason": jr, "value": jitter_ms}
        factors.append(f"Jitter {format_ms(jitter_ms)} -> {jp}/{self.MAX_JITTER} pts" if jitter_ms is not None else "Jitter not measured")

        plp, plr = self._score_packet_loss(packet_loss_percent)
        breakdown["packet_loss"] = {"points": plp, "max": self.MAX_PACKET_LOSS, "reason": plr, "value": packet_loss_percent}
        factors.append(f"Packet loss {format_percent(packet_loss_percent)} -> {plp}/{self.MAX_PACKET_LOSS} pts" if packet_loss_percent is not None else "Packet loss not measured")

        sp, sr = self._score_stability(reconnect_count)
        breakdown["stability"] = {"points": sp, "max": self.MAX_STABILITY, "reason": sr, "value": reconnect_count}
        factors.append(f"Stability (reconnects={reconnect_count}) -> {sp}/{self.MAX_STABILITY} pts")

        tp, tr = self._score_throughput(download_mbps, upload_mbps)
        breakdown["throughput"] = {"points": tp, "max": self.MAX_THROUGHPUT, "reason": tr, "value": download_mbps}
        if download_mbps is not None:
            factors.append(f"Download {download_mbps:.1f} Mbps -> {tp}/{self.MAX_THROUGHPUT} pts")
        else:
            factors.append("Download speed not measured")

        total_points = sum(c["points"] for c in breakdown.values())
        total_max = sum(c["max"] for c in breakdown.values())

        measured = sum(1 for v in (latency_ms, jitter_ms, packet_loss_percent) if v is not None)
        complete = measured == 3

        score: Optional[int] = None
        if complete:
            score = int(clamp(round(total_points / total_max * 100), 0, 100))

        trend = None
        if score is not None and previous_score is not None:
            if score > previous_score + 5:
                trend = "improving"
            elif score < previous_score - 5:
                trend = "declining"
            else:
                trend = "stable"

        message = self._message(score, complete, breakdown, trend)
        return HealthScore(
            score=score,
            complete=complete,
            breakdown=breakdown,
            factors=factors,
            message=message,
            trend=trend,
        )

    def _score_latency(self, ms):
        if ms is None:
            return 0, "Not measured"
        if ms <= 20:
            return self.MAX_LATENCY, "Excellent (<=20 ms)"
        if ms <= 50:
            return int(self.MAX_LATENCY * 0.85), "Good (21-50 ms)"
        if ms <= 100:
            return int(self.MAX_LATENCY * 0.6), "Fair (51-100 ms)"
        if ms <= 200:
            return int(self.MAX_LATENCY * 0.35), "Poor (101-200 ms)"
        return int(self.MAX_LATENCY * 0.15), "Very poor (>200 ms)"

    def _score_jitter(self, ms):
        if ms is None:
            return 0, "Not measured"
        if ms <= 5:
            return self.MAX_JITTER, "Excellent (<=5 ms)"
        if ms <= 15:
            return int(self.MAX_JITTER * 0.8), "Good (6-15 ms)"
        if ms <= 30:
            return int(self.MAX_JITTER * 0.55), "Fair (16-30 ms)"
        if ms <= 60:
            return int(self.MAX_JITTER * 0.3), "Poor (31-60 ms)"
        return int(self.MAX_JITTER * 0.15), "Very poor (>60 ms)"

    def _score_packet_loss(self, percent):
        if percent is None:
            return 0, "Not measured"
        if percent == 0:
            return self.MAX_PACKET_LOSS, "Excellent (0%)"
        if percent <= 0.5:
            return int(self.MAX_PACKET_LOSS * 0.85), "Good (<=0.5%)"
        if percent <= 2:
            return int(self.MAX_PACKET_LOSS * 0.55), "Fair (0.5-2%)"
        if percent <= 5:
            return int(self.MAX_PACKET_LOSS * 0.25), "Poor (2-5%)"
        return int(self.MAX_PACKET_LOSS * 0.1), "Very poor (>5%)"

    def _score_stability(self, reconnect_count):
        if reconnect_count == 0:
            return self.MAX_STABILITY, "No observed reconnects"
        if reconnect_count <= 2:
            return int(self.MAX_STABILITY * 0.6), "Minor reconnects"
        if reconnect_count <= 5:
            return int(self.MAX_STABILITY * 0.3), "Several reconnects"
        return 0, "Frequent reconnects"

    def _score_throughput(self, dl, ul):
        # Throughput is informational; score based on download relative to 100 Mbps target.
        if dl is None:
            return 0, "Not measured"
        if dl >= 100:
            return self.MAX_THROUGHPUT, "Excellent (>=100 Mbps)"
        if dl >= 50:
            return int(self.MAX_THROUGHPUT * 0.8), "Good (50-100 Mbps)"
        if dl >= 25:
            return int(self.MAX_THROUGHPUT * 0.6), "Fair (25-50 Mbps)"
        if dl >= 10:
            return int(self.MAX_THROUGHPUT * 0.35), "Poor (10-25 Mbps)"
        return int(self.MAX_THROUGHPUT * 0.15), "Very poor (<10 Mbps)"

    def _message(self, score, complete, breakdown, trend):
        if not complete:
            missing = [n for n, c in breakdown.items() if c["value"] is None]
            names = ", ".join(missing) if missing else "some measurements"
            return f"Incomplete assessment: {names} not measured. Run a speed test to complete the score."
        if score is None:
            return "Unable to compute score."
        suffix = ""
        if trend == "improving":
            suffix = " (improving)"
        elif trend == "declining":
            suffix = " (declining)"
        if score >= 80:
            return f"Excellent connection health ({score}/100){suffix}."
        if score >= 60:
            return f"Good connection health ({score}/100){suffix}. Minor issues may appear under load."
        if score >= 40:
            return f"Fair connection health ({score}/100){suffix}. Expect occasional issues."
        return f"Poor connection health ({score}/100){suffix}. Investigation recommended."
