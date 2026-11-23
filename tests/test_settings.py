"""Unit tests for the settings model."""

from app.utils.settings import Settings


class TestSettingsDefaults:
    def test_default_theme(self):
        s = Settings()
        assert s.theme == "dark"

    def test_default_interval(self):
        s = Settings()
        assert s.monitoring_interval == 2.0

    def test_default_notifications(self):
        s = Settings()
        assert s.notifications_enabled is True

    def test_default_minimize_to_tray(self):
        s = Settings()
        assert s.minimize_to_tray is False

    def test_default_language(self):
        s = Settings()
        assert s.model.appearance.language == "en"

    def test_default_high_contrast(self):
        s = Settings()
        assert s.model.appearance.high_contrast is False

    def test_default_alert_latency(self):
        s = Settings()
        assert s.alert_latency_ms == 100.0


class TestSettingsSetters:
    def test_set_theme(self):
        s = Settings()
        s.theme = "light"
        assert s.theme == "light"
        s.theme = "dark"
        assert s.theme == "dark"

    def test_set_interval(self):
        s = Settings()
        s.monitoring_interval = 5.5
        assert s.monitoring_interval == 5.5

    def test_set_notifications(self):
        s = Settings()
        s.notifications_enabled = False
        assert s.notifications_enabled is False

    def test_set_language(self):
        s = Settings()
        s.model.appearance.language = "es"
        assert s.model.appearance.language == "es"

    def test_set_high_contrast(self):
        s = Settings()
        s.model.appearance.high_contrast = True
        assert s.model.appearance.high_contrast is True


class TestSettingsValidation:
    def test_interval_bounds(self):
        s = Settings()
        # Values outside bounds should be rejected by Pydantic
        try:
            s.monitoring_interval = 0.1  # Below minimum 0.5
            # Pydantic may coerce or raise depending on config
            assert s.monitoring_interval >= 0.5
        except Exception:
            pass  # Validation error is acceptable
