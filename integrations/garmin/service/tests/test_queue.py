import asyncio
import unittest
from unittest.mock import patch


class TestQueue(unittest.IsolatedAsyncioTestCase):
    async def test_overlapping_requests_are_serialized(self):
        # test_service initializes the collector with a temporary test secret.
        from test_service import TestHttp
        TestHttp.setUpClass()
        try:
            import collector
            active=0
            peak=0
            async def work(request):
                nonlocal active,peak
                active+=1
                peak=max(peak,active)
                await asyncio.sleep(0.01)
                active-=1
                return 'ok'
            with patch.object(collector,'snapshot_queue',asyncio.Lock()), patch.object(collector,'authorized',return_value=True), patch.object(collector,'daily_serial',side_effect=work):
                results=await asyncio.gather(*(collector.daily(None) for _ in range(7)))
            self.assertEqual(results,['ok']*7)
            self.assertEqual(peak,1)
        finally:
            TestHttp.tearDownClass()
