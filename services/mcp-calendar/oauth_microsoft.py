"""
CAL-007 — Microsoft OAuth 2.0 authorization code flow.

Endpoints (served alongside MCP via a separate HTTP app on port 8001):
  GET  /auth/microsoft?account=personal   → redirect to Microsoft login
  GET  /oauth/microsoft/callback           → receive code, exchange for tokens, store

Environment variables required:
  MICROSOFT_CLIENT_ID
  MICROSOFT_CLIENT_SECRET
  MICROSOFT_TENANT_ID   (default: consumers)
  CALENDAR_ENCRYPTION_KEY
"""

import os
import secrets
import time
from urllib.parse import urlencode, urljoin

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route

from token_store import TokenStore

_CLIENT_ID = os.environ["MICROSOFT_CLIENT_ID"]
_CLIENT_SECRET = os.environ["MICROSOFT_CLIENT_SECRET"]
_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "consumers")
_REDIRECT_URI = os.getenv(
    "MICROSOFT_REDIRECT_URI",
    "https://mira.mhisa.es/oauth/microsoft/callback",
)
_SCOPES = "offline_access Calendars.ReadWrite User.Read"

_AUTHORIZE_URL = f"https://login.microsoftonline.com/{_TENANT_ID}/oauth2/v2.0/authorize"
_TOKEN_URL = f"https://login.microsoftonline.com/{_TENANT_ID}/oauth2/v2.0/token"

# In-memory state store (account_id keyed by state token)
_pending: dict[str, str] = {}


def _auth_url(account_id: str) -> str:
    state = secrets.token_urlsafe(32)
    _pending[state] = account_id
    params = {
        "client_id": _CLIENT_ID,
        "response_type": "code",
        "redirect_uri": _REDIRECT_URI,
        "scope": _SCOPES,
        "state": state,
        "response_mode": "query",
    }
    return f"{_AUTHORIZE_URL}?{urlencode(params)}"


async def auth_start(request: Request):
    account_id = request.query_params.get("account", "personal")
    return RedirectResponse(_auth_url(account_id))


async def auth_callback(request: Request):
    error = request.query_params.get("error")
    if error:
        desc = request.query_params.get("error_description", "")
        return HTMLResponse(f"<h2>OAuth error</h2><pre>{error}: {desc}</pre>", status_code=400)

    code = request.query_params.get("code")
    state = request.query_params.get("state", "")
    account_id = _pending.pop(state, None)

    if not code or account_id is None:
        return HTMLResponse("<h2>Invalid state or missing code.</h2>", status_code=400)

    async with httpx.AsyncClient() as client:
        resp = await client.post(_TOKEN_URL, data={
            "client_id": _CLIENT_ID,
            "client_secret": _CLIENT_SECRET,
            "code": code,
            "redirect_uri": _REDIRECT_URI,
            "grant_type": "authorization_code",
        })

    if resp.status_code != 200:
        return HTMLResponse(f"<h2>Token exchange failed</h2><pre>{resp.text}</pre>", status_code=502)

    data = resp.json()
    expires_at = int(time.time()) + int(data.get("expires_in", 3600))

    store = TokenStore()
    store.save(
        account_id,
        "microsoft",
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token"),
        expires_at=expires_at,
        scopes=data.get("scope", _SCOPES),
    )

    return HTMLResponse(
        f"<h2>✅ Conta <b>{account_id}</b> autorizada com sucesso.</h2>"
        "<p>Podes fechar esta janela.</p>"
    )


oauth_app = Starlette(routes=[
    Route("/auth/microsoft", auth_start),
    Route("/oauth/microsoft/callback", auth_callback),
])
