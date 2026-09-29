"""Fake events for CAL-001 to CAL-004 — replaced by real providers in CAL-008."""
from datetime import date, timedelta
from models import CalendarEvent

_TODAY = date.today().isoformat()
_TOMORROW = (date.today() + timedelta(days=1)).isoformat()


FAKE_EVENTS: list[CalendarEvent] = [
    CalendarEvent(
        id="fake-001",
        title="Dentista",
        start=f"{_TODAY}T15:00:00+02:00",
        end=f"{_TODAY}T16:00:00+02:00",
        timezone="Europe/Madrid",
        account="personal",
        provider="microsoft",
        calendar="Calendar",
        all_day=False,
        location="Barcelona",
    ),
    CalendarEvent(
        id="fake-002",
        title="Daily standup",
        start=f"{_TODAY}T09:30:00+02:00",
        end=f"{_TODAY}T10:00:00+02:00",
        timezone="Europe/Madrid",
        account="work",
        provider="microsoft",
        calendar="Work",
        all_day=False,
    ),
    CalendarEvent(
        id="fake-003",
        title="Reunião cliente",
        start=f"{_TOMORROW}T11:00:00+02:00",
        end=f"{_TOMORROW}T12:00:00+02:00",
        timezone="Europe/Madrid",
        account="consulting",
        provider="zoho",
        calendar="Consulting",
        all_day=False,
        attendees=["cliente@empresa.com"],
    ),
]
