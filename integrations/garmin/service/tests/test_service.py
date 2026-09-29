import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from common import parse_day,date_range,daily_summary
from garmin_client import collect,SyncError,GarminConnectNotFoundError,GarminConnectAuthenticationError,GarminConnectTooManyRequestsError


class FakeGarmin:
    def __getattr__(self,name):
        return lambda *args: [] if name in ('get_activities_by_date','get_body_battery') else {'value':1}


class TestCollection(unittest.TestCase):
    def test_all_metrics_collected(self):
        result=collect(FakeGarmin(),'2026-01-01',pause=lambda _:None)
        self.assertEqual(len(result['records']),7)
        self.assertEqual(result['errors'],[])

    def test_unsupported_metric_does_not_erase_success(self):
        api=FakeGarmin()
        api.get_hrv_data=lambda _: (_ for _ in ()).throw(GarminConnectNotFoundError('private upstream details'))
        result=collect(api,'2026-01-01',pause=lambda _:None)
        self.assertEqual(len(result['records']),6)
        self.assertEqual(result['errors'],[{'kind':'hrv','code':'not_available'}])
        self.assertNotIn('private',str(result))

    def test_auth_failure_stops_calls(self):
        api=FakeGarmin()
        api.get_stats=lambda _: (_ for _ in ()).throw(GarminConnectAuthenticationError('secret'))
        with self.assertRaises(SyncError) as error:
            collect(api,'2026-01-01',pause=lambda _:None)
        self.assertEqual(error.exception.code,'garmin_login_required')
        self.assertNotIn('secret',str(error.exception))

    def test_rate_limit_is_not_swallowed(self):
        api=FakeGarmin()
        api.get_stats=lambda _: (_ for _ in ()).throw(GarminConnectTooManyRequestsError('secret'))
        with self.assertRaises(SyncError) as error:
            collect(api,'2026-01-01',pause=lambda _:None)
        self.assertEqual(error.exception.status,429)


class TestSummary(unittest.TestCase):
    def test_unknown_metrics_stay_null(self):
        summary=daily_summary('2026-01-01',[])
        self.assertIsNone(summary['steps'])
        self.assertIsNone(summary['sleep_seconds'])

    def test_units_and_zero_preserved(self):
        rows=[{'kind':'stats','fetched_at':'2026-01-02','payload':{'totalSteps':0,'totalDistanceMeters':1250}}, {'kind':'sleep','fetched_at':'2026-01-02','payload':{'dailySleepDTO':{'sleepTimeSeconds':28800,'sleepScores':{'overall':{'value':80}}}}}]
        summary=daily_summary('2026-01-01',rows)
        self.assertEqual(summary['steps'],0)
        self.assertEqual(summary['distance_m'],1250)
        self.assertEqual(summary['sleep_seconds'],28800)
        self.assertEqual(summary['sleep_score'],80)

    def test_invalid_dates_and_ranges(self):
        for value in ('2026-02-30','20260101','2099-01-01',"2026-01-01'; DROP TABLE health.records;"):
            with self.assertRaises(ValueError): parse_day(value)
        for start,end in [('2026-02-01','2026-01-01'),('2026-01-01','2026-02-01')]:
            with self.assertRaises(ValueError): date_range(start,end)


class TestHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        secret=Path(cls.temp.name)/'token'
        secret.write_text('test-only-'+'x'*32)
        os.environ['COLLECTOR_TOKEN_FILE']=str(secret)
        from collector import app
        from starlette.testclient import TestClient
        cls.client=TestClient(app)
        cls.headers={'Authorization':'Bearer '+secret.read_text()}

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.temp.cleanup()

    def test_health_and_auth(self):
        self.assertEqual(self.client.get('/healthz').status_code,200)
        self.assertEqual(self.client.get('/status').status_code,401)
        self.assertEqual(self.client.get('/snapshot/2026-01-01').status_code,401)

    def test_bad_date(self):
        self.assertEqual(self.client.get('/snapshot/invalid',headers=self.headers).status_code,400)

    def test_missing_session_has_no_sensitive_error(self):
        with patch('collector.snapshot',side_effect=SyncError('garmin_login_required',409)):
            result=self.client.get('/snapshot/2026-01-01',headers=self.headers)
        self.assertEqual(result.status_code,409)
        self.assertEqual(result.json(),{'error':'garmin_login_required'})

    def test_unexpected_exception_is_redacted(self):
        with patch('collector.snapshot',side_effect=RuntimeError('password=private')):
            result=self.client.get('/snapshot/2026-01-01',headers=self.headers)
        self.assertEqual(result.status_code,502)
        self.assertNotIn('private',result.text)


if __name__=='__main__': unittest.main()
