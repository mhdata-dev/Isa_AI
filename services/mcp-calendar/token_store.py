"""
CAL-005 — Token store: SQLite + Fernet encryption.

Stores OAuth tokens per account. The encryption key is the only secret
that must be kept safe — without it, the DB is unreadable.

Usage:
    store = TokenStore()
    store.save("personal", "microsoft", access_token="...", refresh_token="...", expires_at=1234567890, scopes="Calendars.Read")
    creds = store.load("personal")
"""

import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

_DB_PATH = Path(os.getenv("CALENDAR_DB_PATH", "/data/calendar.db"))
_KEY_ENV = "CALENDAR_ENCRYPTION_KEY"


def _get_fernet() -> Fernet:
    key = os.getenv(_KEY_ENV)
    if not key:
        raise RuntimeError(
            f"Environment variable {_KEY_ENV} is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode())


def _db() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS oauth_accounts (
            account_id          TEXT PRIMARY KEY,
            provider            TEXT NOT NULL,
            email               TEXT NOT NULL DEFAULT '',
            access_token_enc    TEXT,
            refresh_token_enc   TEXT,
            expires_at          INTEGER,
            scopes              TEXT,
            updated_at          INTEGER NOT NULL
        )
    """)
    conn.commit()
    return conn


@dataclass
class OAuthCredentials:
    account_id: str
    provider: str
    email: str
    access_token: Optional[str]
    refresh_token: Optional[str]
    expires_at: Optional[int]
    scopes: Optional[str]
    updated_at: int

    def is_expired(self, buffer_secs: int = 300) -> bool:
        if self.expires_at is None:
            return False
        return time.time() >= (self.expires_at - buffer_secs)


class TokenStore:
    def __init__(self):
        self._fernet = _get_fernet()

    def _enc(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return self._fernet.encrypt(value.encode()).decode()

    def _dec(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        try:
            return self._fernet.decrypt(value.encode()).decode()
        except InvalidToken:
            raise RuntimeError("Failed to decrypt token — wrong CALENDAR_ENCRYPTION_KEY?")

    def save(
        self,
        account_id: str,
        provider: str,
        *,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        expires_at: Optional[int] = None,
        scopes: Optional[str] = None,
        email: str = "",
    ) -> None:
        with _db() as conn:
            conn.execute("""
                INSERT INTO oauth_accounts
                    (account_id, provider, email, access_token_enc, refresh_token_enc, expires_at, scopes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(account_id) DO UPDATE SET
                    provider          = excluded.provider,
                    email             = excluded.email,
                    access_token_enc  = excluded.access_token_enc,
                    refresh_token_enc = excluded.refresh_token_enc,
                    expires_at        = excluded.expires_at,
                    scopes            = excluded.scopes,
                    updated_at        = excluded.updated_at
            """, (
                account_id,
                provider,
                email,
                self._enc(access_token),
                self._enc(refresh_token),
                expires_at,
                scopes,
                int(time.time()),
            ))

    def load(self, account_id: str) -> Optional[OAuthCredentials]:
        with _db() as conn:
            row = conn.execute(
                "SELECT * FROM oauth_accounts WHERE account_id = ?", (account_id,)
            ).fetchone()
        if row is None:
            return None
        return OAuthCredentials(
            account_id=row["account_id"],
            provider=row["provider"],
            email=row["email"],
            access_token=self._dec(row["access_token_enc"]),
            refresh_token=self._dec(row["refresh_token_enc"]),
            expires_at=row["expires_at"],
            scopes=row["scopes"],
            updated_at=row["updated_at"],
        )

    def delete(self, account_id: str) -> None:
        with _db() as conn:
            conn.execute("DELETE FROM oauth_accounts WHERE account_id = ?", (account_id,))

    def list_accounts(self) -> list[str]:
        with _db() as conn:
            rows = conn.execute("SELECT account_id FROM oauth_accounts").fetchall()
        return [r["account_id"] for r in rows]
