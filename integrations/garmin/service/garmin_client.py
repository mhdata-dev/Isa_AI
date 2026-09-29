from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import logging
import os
from pathlib import Path
import time

from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectConnectionError, GarminConnectNotFoundError, GarminConnectTooManyRequestsError
from common import parse_day

logging.getLogger('garminconnect').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)
SESSION_DIR = Path(os.getenv('GARMIN_SESSION_DIR','/session'))


class SyncError(Exception):
    def __init__(self, code, status):
        self.code, self.status = code, status
        super().__init__(code)


@contextmanager
def session_lock():
    SESSION_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (SESSION_DIR/'.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SyncError('sync_or_login_in_progress',409) from None
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def session_available():
    return (SESSION_DIR/'garmin_tokens.json').is_file()


def collect(api, day: str, pause=time.sleep):
    parse_day(day)
    methods = {
        'stats':lambda:api.get_stats(day),
        'sleep':lambda:api.get_sleep_data(day),
        'heart_rate':lambda:api.get_heart_rates(day),
        'hrv':lambda:api.get_hrv_data(day),
        'stress':lambda:api.get_stress_data(day),
        'body_battery':lambda:api.get_body_battery(day,day),
        'activities':lambda:api.get_activities_by_date(day,day),
    }
    result={'schema_version':1,'date':day,'fetched_at':datetime.now(timezone.utc).isoformat(),'records':[],'errors':[]}
    for kind,call in methods.items():
        try:
            payload=call()
            if payload is None:
                result['errors'].append({'kind':kind,'code':'no_data'})
            else:
                result['records'].append({'kind':kind,'payload':payload})
        except GarminConnectTooManyRequestsError:
            raise SyncError('garmin_rate_limited',429) from None
        except GarminConnectAuthenticationError:
            raise SyncError('garmin_login_required',409) from None
        except GarminConnectNotFoundError:
            result['errors'].append({'kind':kind,'code':'not_available'})
        except GarminConnectConnectionError as error:
            status=getattr(getattr(error,'response',None),'status_code',None)
            if status in (401,403):
                raise SyncError('garmin_login_required',409) from None
            if status==429:
                raise SyncError('garmin_rate_limited',429) from None
            result['errors'].append({'kind':kind,'code':'upstream_unavailable'})
        except Exception:
            result['errors'].append({'kind':kind,'code':'unexpected_response'})
        pause(1)
    if not result['records']:
        raise SyncError('no_metrics_collected',502)
    return result


def snapshot(day):
    parse_day(day)
    with session_lock():
        if not session_available():
            raise SyncError('garmin_login_required',409)
        api=Garmin()
        try:
            api.login(str(SESSION_DIR))
        except GarminConnectTooManyRequestsError:
            raise SyncError('garmin_rate_limited',429) from None
        except Exception:
            raise SyncError('garmin_login_required',409) from None
        return collect(api,day)
