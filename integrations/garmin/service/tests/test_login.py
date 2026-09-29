import unittest
from types import SimpleNamespace
from garminconnect import GarminConnectAuthenticationError, GarminConnectTooManyRequestsError
from login import failure_message


class TestLoginDiagnostics(unittest.TestCase):
    def test_nested_rate_limit_takes_priority_over_auth_error(self):
        inner=RuntimeError('private account details')
        inner.response=SimpleNamespace(status_code=429)
        outer=GarminConnectAuthenticationError('private password')
        outer.__cause__=inner
        message=failure_message(outer)
        self.assertIn('garmin_rate_limited',message)
        self.assertNotIn('private',message)

    def test_rate_limit_without_response(self):
        self.assertIn('garmin_rate_limited',failure_message(GarminConnectTooManyRequestsError('secret')))

    def test_unknown_error_never_displays_upstream_message(self):
        self.assertNotIn('secret',failure_message(ValueError('secret')))

    def test_permission_failure(self):
        self.assertIn('session_permission',failure_message(PermissionError('secret path')))
