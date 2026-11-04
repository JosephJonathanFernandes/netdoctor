"""Unit tests for the custom exception hierarchy."""

from app.exceptions import (
    CancellationError,
    ConfigurationError,
    ConnectivityError,
    DatabaseError,
    DiagnosticError,
    NetDoctorError,
    NetworkError,
    ServerUnavailableError,
    SpeedTestError,
    WorkerError,
)


class TestExceptionHierarchy:
    def test_netdoctor_error_base(self):
        err = NetDoctorError("base error")
        assert isinstance(err, Exception)
        assert str(err) == "base error"

    def test_configuration_error(self):
        err = ConfigurationError("bad config")
        assert isinstance(err, NetDoctorError)

    def test_database_error(self):
        err = DatabaseError("db fail")
        assert isinstance(err, NetDoctorError)

    def test_network_error(self):
        err = NetworkError("net down")
        assert isinstance(err, NetDoctorError)

    def test_connectivity_error(self):
        err = ConnectivityError("no internet")
        assert isinstance(err, NetworkError)
        assert isinstance(err, NetDoctorError)

    def test_speed_test_error(self):
        err = SpeedTestError("test failed")
        assert isinstance(err, NetworkError)

    def test_server_unavailable_error(self):
        err = ServerUnavailableError("server down")
        assert isinstance(err, SpeedTestError)
        assert isinstance(err, NetworkError)
        assert isinstance(err, NetDoctorError)

    def test_diagnostic_error(self):
        err = DiagnosticError("diag failed")
        assert isinstance(err, NetDoctorError)

    def test_worker_error(self):
        err = WorkerError("worker crashed")
        assert isinstance(err, NetDoctorError)

    def test_cancellation_error(self):
        err = CancellationError("user cancelled")
        assert isinstance(err, NetDoctorError)

    def test_catch_base_catches_all(self):
        for exc in [
            ConfigurationError(),
            DatabaseError(),
            NetworkError(),
            ConnectivityError(),
            SpeedTestError(),
            ServerUnavailableError(),
            DiagnosticError(),
            WorkerError(),
            CancellationError(),
        ]:
            try:
                raise exc
            except NetDoctorError:
                pass
            else:
                raise AssertionError(f"{type(exc).__name__} not caught by NetDoctorError")
