"""Unit tests for the rule-based recommendations engine."""

from app.services.recommendations import RecommendationsEngine


class TestRecommendationsEngine:
    def setup_method(self):
        self.engine = RecommendationsEngine()

    def test_high_latency_triggers_recommendation(self):
        recs = self.engine.build(latency_ms=150.0)
        assert any(r.category == "latency" and r.severity == "warning" for r in recs)
        lat_rec = next(r for r in recs if r.category == "latency")
        assert "150.0 ms" in lat_rec.evidence
        assert len(lat_rec.message) > 0

    def test_high_jitter_warning(self):
        recs = self.engine.build(jitter_ms=40.0)
        jit = next((r for r in recs if "jitter" in r.title.lower()), None)
        assert jit is not None
        assert "40.0 ms" in jit.evidence

    def test_high_packet_loss_critical(self):
        recs = self.engine.build(packet_loss_percent=7.0)
        pl = next((r for r in recs if r.category == "packet_loss"), None)
        assert pl is not None
        assert pl.severity == "critical"
        assert "7.0%" in pl.evidence

    def test_weak_wifi_signal(self):
        recs = self.engine.build(wifi_signal_percent=30)
        wifi = next((r for r in recs if r.category == "wifi"), None)
        assert wifi is not None
        assert "30%" in wifi.evidence

    def test_dns_failure(self):
        recs = self.engine.build(dns_ok=False)
        dns = next((r for r in recs if r.category == "dns"), None)
        assert dns is not None
        assert dns.severity == "warning"

    def test_stability_reconnects(self):
        recs = self.engine.build(reconnect_count=5)
        stab = next((r for r in recs if r.category == "stability"), None)
        assert stab is not None
        assert "5" in stab.evidence

    def test_no_issues_general(self):
        recs = self.engine.build(
            latency_ms=20.0,
            jitter_ms=3.0,
            packet_loss_percent=0.0,
            dns_ok=True,
            reconnect_count=0,
        )
        assert any(r.category == "general" for r in recs)

    def test_every_recommendation_has_evidence(self):
        recs = self.engine.build(
            latency_ms=200.0,
            jitter_ms=70.0,
            packet_loss_percent=9.0,
            wifi_signal_percent=20,
            dns_ok=False,
            reconnect_count=8,
        )
        for r in recs:
            assert r.evidence, f"Recommendation {r.title} missing evidence"
            assert r.severity in ("info", "warning", "critical")
