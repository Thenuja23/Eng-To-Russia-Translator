from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Russian Cursive Learning & Reading Assistant"
    version: str = "0.1.0"
    default_translator: str = "opustmt"
    nllb_model_name: str = "facebook/nllb-200-distilled-600M"
    opusmt_ru_en: str = "Helsinki-NLP/opus-mt-ru-en"
    opusmt_en_ru: str = "Helsinki-NLP/opus-mt-en-ru"
    device: str = "cpu"
    warn_nllb_noncommercial: bool = True

    # NLLB is a 2.4 GB download with a non-commercial licence, so it is opt-in.
    # Set ENABLE_NLLB=true to expose it via `engine: "nllb"`.
    enable_nllb: bool = False

    # Reject absurdly large inputs instead of blocking the worker.
    max_text_chars: int = 20_000

    # ------------------------------------------------------------------ AI ----
    # Optional multi-provider AI ensemble (OpenAI + Anthropic Claude +
    # Perplexity). The app is fully functional offline / without keys; AI
    # endpoints report 503 "not configured" until at least one key is set.
    # Keys live only on the backend and are never sent to the browser.
    ai_enabled: bool = True
    ai_provider_order: str = "openai,anthropic,perplexity"
    ai_timeout_seconds: float = 45.0
    ai_max_chars: int = 4_000
    ai_max_requests_per_minute: int = 20
    ai_cache_ttl_seconds: int = 900
    ai_temperature: float = 0.2

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-haiku-latest"
    anthropic_base_url: str = "https://api.anthropic.com/v1"

    perplexity_api_key: Optional[str] = None
    perplexity_model: str = "sonar"
    perplexity_base_url: str = "https://api.perplexity.ai"

    # Comma-separated list of allowed browser origins for CORS.
    cors_origins: str = (
        "http://127.0.0.1:5173,http://localhost:5173,"
        "http://127.0.0.1:4173,http://localhost:4173"
    )
    # Also allow any localhost/LAN port during development.
    cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1|\[::1\]|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d+)?$"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
