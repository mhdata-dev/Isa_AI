from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CalendarAccount:
    id: str
    provider: str
    label: str
    email: str
    timezone: str
    writable: bool


@dataclass
class CalendarEvent:
    id: str
    title: str
    start: str
    end: str
    timezone: str
    account: str
    provider: str
    calendar: str
    all_day: bool
    location: Optional[str] = None
    description: Optional[str] = None
    attendees: list[str] = field(default_factory=list)
    status: str = "confirmed"
