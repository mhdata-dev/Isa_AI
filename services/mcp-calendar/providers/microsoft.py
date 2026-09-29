"""
CAL-008 — Microsoft Graph calendar provider.

Fetches events from the Microsoft Graph API using stored OAuth tokens.
Handles token refresh automatically.
"""

import os
import time
from datetime import datetime, timezone

import httpx

from models import CalendarEvent
from token_store import TokenStore, OAuthCredentials

_CLIENT_ID = os.environ["MICROSOFT_CLIENT_ID"]
_CLIENT_SECRET = os.environ["MICROSOFT_CLIENT_SECRET"]
_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "consumers")
_TOKEN_URL = f"https://login.microsoftonline.com/{_TENANT_ID}/oauth2/v2.0/token"
_GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def _refresh_token(store: TokenStore, account_id: str, creds: OAuthCredentials) -> OAuthCredentials:
    if not creds.refresh_token:
        raise RuntimeError(f"No refresh token for account '{account_id}'. Re-authorize via /auth/microsoft?account={account_id}")

    resp = httpx.post(_TOKEN_URL, data={
        "client_id": _CLIENT_ID,
        "client_secret": _CLIENT_SECRET,
        "refresh_token": creds.refresh_token,
        "grant_type": "refresh_token",
    })
    resp.raise_for_status()
    data = resp.json()

    expires_at = int(time.time()) + int(data.get("expires_in", 3600))
    store.save(
        account_id,
        "microsoft",
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token", creds.refresh_token),
        expires_at=expires_at,
        scopes=data.get("scope", creds.scopes),
        email=creds.email,
    )
    return store.load(account_id)


def _get_valid_token(store: TokenStore, account_id: str) -> str:
    creds = store.load(account_id)
    if creds is None:
        raise RuntimeError(f"Account '{account_id}' not authorized. Visit /auth/microsoft?account={account_id}")
    if creds.is_expired():
        creds = _refresh_token(store, account_id, creds)
    return creds.access_token


def _parse_event(raw: dict, account_id: str, timezone: str = "Europe/Madrid") -> CalendarEvent:
    start = raw.get("start", {})
    end = raw.get("end", {})
    start_str = start.get("dateTime", start.get("date", ""))
    end_str = end.get("dateTime", end.get("date", ""))
    return CalendarEvent(
        id=raw.get("id", ""),
        account=account_id,
        provider="microsoft",
        calendar="default",
        title=raw.get("subject", "(sem título)"),
        start=start_str,
        end=end_str,
        timezone=timezone,
        location=raw.get("location", {}).get("displayName") or None,
        description=raw.get("bodyPreview") or None,
        all_day="date" in start,
    )


def list_events_microsoft(account_id: str, start: str, end: str, timezone: str = "Europe/Madrid") -> list[CalendarEvent]:
    store = TokenStore()
    token = _get_valid_token(store, account_id)

    params = {
        "startDateTime": f"{start}T00:00:00Z",
        "endDateTime": f"{end}T23:59:59Z",
        "$select": "id,subject,start,end,location,bodyPreview",
        "$orderby": "start/dateTime",
        "$top": 50,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Prefer": f'outlook.timezone="{timezone}"',
    }
    resp = httpx.get(f"{_GRAPH_BASE}/me/calendarView", params=params, headers=headers)
    resp.raise_for_status()

    return [_parse_event(e, account_id, timezone) for e in resp.json().get("value", [])]
