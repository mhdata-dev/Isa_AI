from datetime import date, datetime
from zoneinfo import ZoneInfo
import os
from pathlib import Path

KINDS = ('stats', 'sleep', 'heart_rate', 'hrv', 'stress', 'body_battery', 'activities')


def parse_day(value: str) -> date:
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value or parsed > datetime.now(ZoneInfo('Europe/Madrid')).date():
        raise ValueError('Use a past or current date in YYYY-MM-DD format.')
    return parsed


def date_range(start: str, end: str, maximum: int = 31):
    first, last = parse_day(start), parse_day(end)
    if not 0 <= (last-first).days < maximum:
        raise ValueError(f'Use an ordered range of at most {maximum} days.')
    return first, last


def read_secret(environment: str) -> str:
    value = Path(os.environ[environment]).read_text().strip()
    if len(value) < 24:
        raise RuntimeError('Service secret is missing or too short.')
    return value


def nested(data, *keys):
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


def daily_summary(day, records):
    """Select fields with their original Garmin units; absent values remain null."""
    by_kind = {r['kind']:r['payload'] for r in records}
    stats = by_kind.get('stats') or {}
    sleep = nested(by_kind.get('sleep'), 'dailySleepDTO') or {}
    hrv = nested(by_kind.get('hrv'), 'hrvSummary') or {}
    battery = by_kind.get('body_battery') or []
    battery = next((item for item in battery if item.get('date') == str(day)), {}) if isinstance(battery,list) else {}
    return {
        'date':str(day),
        'source':'Garmin Connect',
        'steps':stats.get('totalSteps'),
        'distance_m':stats.get('totalDistanceMeters'),
        'calories_kcal':stats.get('totalKilocalories'),
        'resting_heart_rate_bpm':stats.get('restingHeartRate'),
        'min_heart_rate_bpm':stats.get('minHeartRate'),
        'max_heart_rate_bpm':stats.get('maxHeartRate'),
        'sleep_seconds':sleep.get('sleepTimeSeconds'),
        'sleep_score':nested(sleep,'sleepScores','overall','value'),
        'hrv_last_night_ms':hrv.get('lastNightAvg'),
        'hrv_status':hrv.get('status'),
        'average_stress':nested(by_kind.get('stress'),'avgStressLevel'),
        'body_battery_charged':battery.get('charged'),
        'body_battery_drained':battery.get('drained'),
        'available_metrics':[{ 'kind':r['kind'], 'fetched_at':str(r['fetched_at']) } for r in records],
    }
