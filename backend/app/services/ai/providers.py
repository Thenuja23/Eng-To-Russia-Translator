"""HTTP clients for the optional multi-provider AI ensemble.

Every provider speaks a slightly different dialect, but they all expose a
``complete(system, user)`` method returning plain text. Only providers whose
API key is configured are ever called, and keys never leave the backend.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional

import httpx

from app.core.config import settings

RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


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
                return text
            except _Retryable as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(0.6)
            except ProviderError:
                raise
        raise ProviderError(str(last_error) if last_error else f"{self.name}: failed")


class _Retryable(ProviderError):
    """Transient provider failure (retried once)."""


def build_providers(order: Optional[str] = None) -> List[Provider]:
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
