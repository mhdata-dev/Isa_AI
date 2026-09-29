import os
from models import CalendarAccount

ACCOUNTS: dict[str, CalendarAccount] = {
    "personal": CalendarAccount(
        id="personal",
        provider="microsoft",
        label="Hotmail pessoal",
        email=os.getenv("PERSONAL_EMAIL", ""),
        timezone="Europe/Madrid",
        writable=True,
    ),
    "work": CalendarAccount(
        id="work",
        provider="microsoft",
        label="Trabalho",
        email=os.getenv("WORK_EMAIL", ""),
        timezone="Europe/Madrid",
        writable=True,
    ),
    "consulting": CalendarAccount(
        id="consulting",
        provider="zoho",
        label="Zoho",
        email=os.getenv("CONSULTING_EMAIL", ""),
        timezone="Europe/Madrid",
        writable=True,
    ),
}
