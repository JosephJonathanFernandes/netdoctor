"""Unit tests for the internet health score."""

from app.services.health_score import HealthScoreService


class TestHealthScore:
    def setup_method(self):
        self.svc = HealthScoreService()

    def test_complete_all_measurements(self):
        result = self.svc.compute(
            latency_ms=25.0,
            jitter_ms=5.0,
            packet_loss_percent=0.0,
            reconnect_count=0,
        )
        assert result.complete is True
        assert result.score is not None
        assert 0 <= result.score <= 100
        assert result.score >= 80  # excellent measurements -> excellent score

    def test_missing_measurements_incomplete(self):
        result = self.svc.compute(
            latency_ms=25.0,
            jitter_ms=None,
            packet_loss_percent=0.0,
        )
        assert result.complete is False
        assert result.score is None
        assert "not measured" in result.message.lower()

    def test_all_missing(self):
        result = self.svc.compute()
        assert result.complete is False
        assert result.score is None

    def test_poor_measurements_low_score(self):
        result = self.svc.compute(
            latency_ms=250.0,
            jitter_ms=80.0,
            packet_loss_percent=8.0,
            reconnect_count=10,
        )
        assert result.complete is True
        assert result.score is not None
        assert result.score < 40

    def test_breakdown_sums_to_total(self):
        result = self.svc.compute(
            latency_ms=10.0,
            jitter_ms=2.0,
            packet_loss_percent=0.0,
            reconnect_count=0,
        )
        total_points = sum(c["points"] for c in result.breakdown.values())
        total_max = sum(c["max"] for c in result.breakdown.values())
        expected = int(total_points / total_max * 100)
        assert result.score == expected

    def test_score_is_clamped(self):
        # Even with weird values the score stays in 0-100 when complete.
        result = self.svc.compute(
            latency_ms=0.0,
            jitter_ms=0.0,
            packet_loss_percent=0.0,
            reconnect_count=0,
            download_mbps=100.0,
        )
        assert result.score == 100

    def test_factors_contain_evidence(self):
        result = self.svc.compute(
            latency_ms=50.0,
            jitter_ms=10.0,
            packet_loss_percent=1.0,
            reconnect_count=1,
        )
        assert any("50.0 ms" in f for f in result.factors)
