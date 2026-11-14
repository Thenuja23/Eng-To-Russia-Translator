"""HTTP clients for the optional multi-provider AI ensemble.

Every provider speaks a slightly different dialect, but they all expose a
``complete(system, user)`` method returning plain text. Only providers whose
API key is configured are ever called, and keys never leave the backend.
"""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import List, Optional

import httpx

from app.core.config import settings

RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}
_health_lock = threading.Lock()
_health: dict[str, dict] = {}


class ProviderError(RuntimeError):
    """Raised when a provider cannot produce an answer."""


@dataclass
class ProviderConfig:
    name: str
    kind: str  # "openai" | "anthropic" | "perplexity"
    model: str
    api_key: Optional[str]
    base_url: str


class Provider:
    def __init__(self, cfg: ProviderConfig, timeout: float = 45.0):
        self.cfg = cfg
        self.timeout = timeout

    # -- identity ---------------------------------------------------------
    @property
    def name(self) -> str:
        return self.cfg.name

    @property
    def model(self) -> str:
        return self.cfg.model

    @property
    def configured(self) -> bool:
        return bool(self.cfg.api_key)

    def describe(self, priority: int) -> dict:
        return {
            "name": self.name,
            "model": self.model,
            "configured": self.configured,
            "priority": priority,
        }

    # -- transport --------------------------------------------------------
    def _post(self, path: str, headers: dict, payload: dict) -> dict:
        url = f"{self.cfg.base_url.rstrip('/')}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=headers, json=payload)
        except Exception as exc:  # noqa: BLE001 - network errors are retried below
            raise ProviderError(f"{self.name}: connection failed ({exc})") from exc
        if resp.status_code >= 400:
            body = (resp.text or "")[:280].replace("\n", " ")
            if resp.status_code in RETRYABLE_STATUS:
                raise _Retryable(f"{self.name}: HTTP {resp.status_code} {body}")
            raise ProviderError(f"{self.name}: HTTP {resp.status_code} {body}")
        try:
            return resp.json()
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"{self.name}: invalid JSON response") from exc

    def _openai_like(self, system: str, user: str, max_tokens: int, temperature: float) -> str:
        data = self._post(
            "/chat/completions",
            headers={
                "Authorization": f"Bearer {self.cfg.api_key}",
                "Content-Type": "application/json",
            },
            payload={
                "model": self.cfg.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"{self.name}: unexpected response shape") from exc

    def _anthropic(self, system: str, user: str, max_tokens: int, temperature: float) -> str:
        data = self._post(
            "/messages",
            headers={
                "x-api-key": self.cfg.api_key or "",
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            payload={
                "model": self.cfg.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        try:
            blocks = data.get("content") or []
            text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
            return text
        except (AttributeError, TypeError) as exc:
            raise ProviderError(f"{self.name}: unexpected response shape") from exc

    # -- public -----------------------------------------------------------
    def complete(
        self,
        system: str,
        user: str,
        max_tokens: int = 900,
        temperature: Optional[float] = None,
    ) -> str:
        if not self.configured:
            raise ProviderError(f"{self.name}: missing API key")

        started = time.time()
        now = time.time()
        with _health_lock:
            state = _health.setdefault(self.name, {"failures": 0, "open_until": 0, "last_success": None, "last_failure": None, "latency_ms": None, "error_category": None})
            if state["open_until"] > now:
                raise ProviderError(f"{self.name}: temporarily unavailable after repeated failures")

        temp = settings.ai_temperature if temperature is None else temperature
        last_error: Optional[Exception] = None
        for attempt in (0, 1):
            try:
                if self.cfg.kind == "anthropic":
                    text = self._anthropic(system, user, max_tokens, temp)
                else:
                    text = self._openai_like(system, user, max_tokens, temp)
                text = (text or "").strip()
                if not text:
                    raise ProviderError(f"{self.name}: empty response")
                with _health_lock:
                    state.update(failures=0, open_until=0, last_success=time.time(), latency_ms=int((time.time()-started)*1000), error_category=None)
                return text
            except _Retryable as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(0.6)
            except ProviderError:
                self._record_failure(state, started, "provider")
                raise
        self._record_failure(state, started, "transient")
        raise ProviderError(str(last_error) if last_error else f"{self.name}: failed")

    def _record_failure(self, state: dict, started: float, category: str) -> None:
        with _health_lock:
            state["failures"] += 1
            state["last_failure"] = time.time()
            state["latency_ms"] = int((time.time()-started)*1000)
            state["error_category"] = category
            if state["failures"] >= 3:
                state["open_until"] = time.time() + 60


class _Retryable(ProviderError):
    """Transient provider failure (retried once)."""


def build_providers(order: Optional[str] = None, credentials: Optional[dict[str, str]] = None, models: Optional[dict[str, str]] = None) -> List[Provider]:
    """Build the configured provider list in the requested order."""
    catalog = {
        "openai": ProviderConfig(
            name="openai",
            kind="openai",
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        ),
        "anthropic": ProviderConfig(
            name="anthropic",
            kind="anthropic",
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_base_url,
        ),
        "perplexity": ProviderConfig(
            name="perplexity",
            kind="perplexity",
            model=settings.perplexity_model,
            api_key=settings.perplexity_api_key,
            base_url=settings.perplexity_base_url,
        ),
    }
    credentials = credentials or {}
    models = models or {}
    for name, cfg in catalog.items():
        if name in credentials:
            cfg.api_key = credentials[name]
        if models.get(name):
            cfg.model = models[name]
    raw = order if order is not None else settings.ai_provider_order
    names = [n.strip().lower() for n in raw.split(",") if n.strip()]
    providers = [
        Provider(catalog[n], timeout=settings.ai_timeout_seconds)
        for n in names
        if n in catalog
    ]
    # Anything omitted from the order string is appended so a mistyped order
    # can never silently disable a configured provider.
    for name, cfg in catalog.items():
        if name not in names:
            providers.append(Provider(cfg, timeout=settings.ai_timeout_seconds))
    return providers
