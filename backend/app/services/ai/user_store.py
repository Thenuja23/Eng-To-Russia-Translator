"""Per-account AI credentials, preferences and opt-in request history."""
from __future__ import annotations

import json
import uuid
from cryptography.fernet import Fernet

from app.core.config import settings
from app.services.auth import db


def _fernet() -> Fernet:
    key = (settings.ai_credentials_encryption_key or "").strip()
    if not key:
        raise RuntimeError("Student API key storage is unavailable: configure AI_CREDENTIALS_ENCRYPTION_KEY.")
    try:
        return Fernet(key.encode("ascii"))
    except Exception as exc:
        raise RuntimeError("AI_CREDENTIALS_ENCRYPTION_KEY must be a Fernet key.") from exc


def credential_names(user_id: str) -> list[str]:
    with db.connect() as con:
        return [r[0] for r in con.execute("SELECT provider FROM ai_credentials WHERE user_id=?", (user_id,))]


def get_credentials(user_id: str) -> dict[str, str]:
    f = _fernet()
    with db.connect() as con:
        rows = con.execute("SELECT provider,ciphertext FROM ai_credentials WHERE user_id=?", (user_id,)).fetchall()
    return {r["provider"]: f.decrypt(r["ciphertext"].encode()).decode() for r in rows}


def save_credential(user_id: str, provider: str, key: str) -> None:
    ciphertext = _fernet().encrypt(key.encode()).decode()
    with db.connect() as con:
        con.execute("INSERT INTO ai_credentials VALUES(?,?,?,?) ON CONFLICT(user_id,provider) DO UPDATE SET ciphertext=excluded.ciphertext, updated_at=excluded.updated_at", (user_id, provider, ciphertext, db.iso(db.utcnow())))


def delete_credential(user_id: str, provider: str) -> None:
    with db.connect() as con:
        con.execute("DELETE FROM ai_credentials WHERE user_id=? AND provider=?", (user_id, provider))


def preferences(user_id: str) -> dict:
    with db.connect() as con:
        row = con.execute("SELECT data FROM ai_preferences WHERE user_id=?", (user_id,)).fetchone()
    return json.loads(row[0]) if row else {"provider_mode": "auto", "providers": ["openai", "anthropic", "perplexity"], "translation_mode": "accurate", "level": "intermediate", "explanation_language": "en", "include_grammar": False, "include_examples": True, "history_enabled": False}


def save_preferences(user_id: str, data: dict) -> None:
    with db.connect() as con:
        con.execute("INSERT INTO ai_preferences VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at", (user_id, json.dumps(data, ensure_ascii=False), db.iso(db.utcnow())))


def add_history(user_id: str, source: str, translated: str, provider: str, model: str, mode: str, latency_ms: int = 0) -> None:
    if not preferences(user_id).get("history_enabled"):
        return
    with db.connect() as con:
        con.execute("INSERT INTO ai_history(id,user_id,source,translated,provider,model,mode,created_at,latency_ms) VALUES(?,?,?,?,?,?,?,?,?)", (str(uuid.uuid4()), user_id, source, translated, provider, model, mode, db.iso(db.utcnow()), latency_ms))
        # Configurable retention cap, per account.
        con.execute("DELETE FROM ai_history WHERE user_id=? AND id NOT IN (SELECT id FROM ai_history WHERE user_id=? ORDER BY created_at DESC LIMIT ?)", (user_id, user_id, max(0, settings.ai_history_retention_entries)))


def list_history(user_id: str) -> list[dict]:
    with db.connect() as con:
        rows = con.execute("SELECT id,source,translated,provider,model,mode,created_at,latency_ms,token_usage FROM ai_history WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (user_id, settings.ai_history_retention_entries)).fetchall()
    return [dict(r) for r in rows]


def delete_history(user_id: str, entry_id: str | None = None) -> None:
    with db.connect() as con:
        if entry_id:
            con.execute("DELETE FROM ai_history WHERE user_id=? AND id=?", (user_id, entry_id))
        else:
            con.execute("DELETE FROM ai_history WHERE user_id=?", (user_id,))
