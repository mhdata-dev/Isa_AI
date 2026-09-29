import threading
from datetime import date, timedelta
from dataclasses import asdict
from typing import Optional

import uvicorn
from mcp.server.mcpserver import MCPServer

from config import ACCOUNTS
from providers.microsoft import list_events_microsoft
from oauth_microsoft import oauth_app

mcp = MCPServer("isa-calendar")


def _get_events(start: str, end: str, account: Optional[str]) -> list[dict]:
    account_ids = [account] if account else list(ACCOUNTS.keys())
    events = []
    for acc_id in account_ids:
        acc = ACCOUNTS.get(acc_id)
        if acc is None:
            continue
        try:
            if acc.provider == "microsoft":
                events.extend(list_events_microsoft(acc_id, start, end, acc.timezone))
        except RuntimeError as e:
            events.append({"error": str(e), "account": acc_id})
    events.sort(key=lambda e: e.get("start", "") if isinstance(e, dict) else e.start)
    return [asdict(e) if not isinstance(e, dict) else e for e in events]


@mcp.tool()
def list_accounts() -> list[dict]:
    """List all calendar accounts connected to Isa."""
    return [asdict(a) for a in ACCOUNTS.values()]


@mcp.tool()
def get_today(account: Optional[str] = None) -> list[dict]:
    """Return today's events. Optionally filter by account id."""
    today = date.today().isoformat()
    return _get_events(today, today, account)


@mcp.tool()
def get_tomorrow(account: Optional[str] = None) -> list[dict]:
    """Return tomorrow's events. Optionally filter by account id."""
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    return _get_events(tomorrow, tomorrow, account)


@mcp.tool()
def list_events(start: str, end: str, account: Optional[str] = None) -> list[dict]:
    """
    List events in a date range.

    Args:
        start: ISO date string, e.g. '2026-09-09'
        end:   ISO date string, e.g. '2026-09-15'
        account: optional account id filter ('personal', 'work', 'consulting')
    """
    return _get_events(start, end, account)


def _run_mcp():
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    t = threading.Thread(target=_run_mcp, daemon=True)
    t.start()
    uvicorn.run(oauth_app, host="0.0.0.0", port=8001, log_level="info")
