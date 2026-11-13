from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import List, Optional

# Resolve backend/.env regardless of the directory uvicorn is started from.
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE), env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Russian Cursive Learning & Reading Assistant"
    version: str = "0.1.0"
    default_translator: str = "opustmt"
    nllb_model_name: str = "facebook/nllb-200-distilled-600M"
    opusmt_ru_en: str = "Helsinki-NLP/opus-mt-ru-en"
    opusmt_en_ru: str = "Helsinki-NLP/opus-mt-en-ru"
    # Beam search is noticeably better than greedy decoding on MarianMT, at the
    # cost of a little latency. Set to 1 to restore greedy decoding.
    opusmt_num_beams: int = 4
    device: str = "cpu"
    warn_nllb_noncommercial: bool = True

    # NLLB is a 2.4 GB download with a non-commercial licence, so it is opt-in.
    # Set ENABLE_NLLB=true to expose it via `engine: "nllb"`.
    enable_nllb: bool = False

    # Reject absurdly large inputs instead of blocking the worker.
    max_text_chars: int = 20_000
    max_ocr_upload_bytes: int = 10 * 1024 * 1024
    ocr_space_api_key: Optional[str] = None

    # ------------------------------------------------------ Google Translate ----
    # Optional Google Cloud Translation (Basic v2) engine. Set an API key to
    # enable the "google" engine and the "auto"/"hybrid" modes. The key is
    # server-side only and never exposed to the browser.
    google_translate_api_key: Optional[str] = None
    # Convenience alias for deployments that already use GOOGLE_API_KEY.
    google_api_key: Optional[str] = None
    google_translate_base_url: str = (
        "https://translation.googleapis.com/language/translate/v2"
    )
    google_translate_timeout_seconds: float = 20.0
    google_translate_retries: int = 2
    # Stay well below Google's 30k-character / 128-segment request limits.
    google_translate_max_chars: int = 4_000
    translation_cache_ttl_seconds: int = 900
    translation_cache_max_entries: int = 256

    @property
    def google_translate_configured(self) -> bool:
        return bool((self.google_translate_api_key or self.google_api_key or "").strip())

    @property
    def google_translate_key(self) -> str:
        return (self.google_translate_api_key or self.google_api_key or "").strip()

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

    # ------------------------------------------------------ Vocabulary engine --
    # The word-by-word vocabulary assistant works offline from a curated
    # dictionary and grammar rules. Unknown words can additionally be glossed
    # through a free online lookup (no key). Turn that off for a fully offline
    # server, or to avoid sending learner text to a third party.
    vocab_online_lookup: bool = True
    vocab_lookup_timeout_seconds: float = 5.0
    vocab_max_online_words: int = 15

    perplexity_api_key: Optional[str] = None
    perplexity_model: str = "sonar"
    perplexity_base_url: str = "https://api.perplexity.ai"

    # ---------------------------------------------------------------- auth ----
    # Real accounts, sessions and Google OAuth are handled by this backend.
    # Accounts live in a small SQLite database (path configurable) and passwords
    # are hashed with scrypt, or PBKDF2-HMAC-SHA256 on Python builds without
    # scrypt support. Session tokens are opaque random values stored as
    # hashes; only an HttpOnly cookie ever carries them.
    auth_db_path: str = str(Path(__file__).resolve().parents[2] / "auth.db")
    auth_session_days: int = 30
    auth_cookie_name: str = "etr_session"
    # Only trust X-Forwarded-For when the immediate peer matches this explicit
    # list of proxy IPs/CIDRs. Leave empty when clients can reach the API
    # directly; this prevents callers from choosing their own throttle IP.
    auth_trusted_proxy_ips: str = ""
    # Set true when the site is served over HTTPS in production.
    # In production the site is HTTPS, so cookies must be Secure.
    auth_cookie_secure: bool = True
    # Public origin of the frontend; used for Google redirects and email links.
    auth_app_base_url: str = "https://eng-to-russia-translator.vercel.app"
    # Require a session for the translation/OCR/vocab/AI endpoints. The UI always
    # requires login; this switch also locks the raw API down for deployments
    # that must not serve anonymous traffic.
    auth_protect_features: bool = False

    # Google OAuth 2.0 (Authorization Code flow, handled server-side).
    # Create these in Google Cloud Console -> APIs & Services -> Credentials.
    auth_google_client_id: Optional[str] = None
    auth_google_client_secret: Optional[str] = None
    # Defaults to <auth_app_base_url>/auth/google/callback when omitted.
    auth_google_redirect_uri: Optional[str] = None

    # Transactional email for verification and password reset links. Without an
    # SMTP host the backend still creates real one-time tokens but cannot send
    # them; the API says so instead of pretending an email was delivered.
    auth_smtp_host: Optional[str] = None
    auth_smtp_port: int = 587
    auth_smtp_user: Optional[str] = None
    auth_smtp_password: Optional[str] = None
    auth_smtp_from: Optional[str] = None
    auth_smtp_starttls: bool = True

    @property
    def google_oauth_configured(self) -> bool:
        return bool(
            (self.auth_google_client_id or "").strip()
            and (self.auth_google_client_secret or "").strip()
        )

    @property
    def google_redirect_uri(self) -> str:
        return (
            (self.auth_google_redirect_uri or "").strip()
            or f"{self.auth_app_base_url.rstrip('/')}/auth/google/callback"
        )

    @property
    def email_delivery_configured(self) -> bool:
        return bool((self.auth_smtp_host or "").strip())

    def validate_auth_configuration(self) -> None:
        """Fail startup for contradictory OAuth settings; leave OAuth optional."""
        client_id = (self.auth_google_client_id or "").strip()
        client_secret = (self.auth_google_client_secret or "").strip()
        if bool(client_id) != bool(client_secret):
            raise ValueError(
                "Google OAuth configuration is incomplete: set both "
                "AUTH_GOOGLE_CLIENT_ID and AUTH_GOOGLE_CLIENT_SECRET, or leave both empty."
            )
        if client_id:
            from urllib.parse import urlparse

            redirect = urlparse(self.google_redirect_uri)
            local_http = redirect.hostname in ("localhost", "127.0.0.1", "::1")
            if redirect.scheme != "https" and not (redirect.scheme == "http" and local_http):
                raise ValueError(
                    "Google OAuth callback must use HTTPS outside localhost. "
                    "Set AUTH_GOOGLE_REDIRECT_URI to the public HTTPS callback URL."
                )

    # Comma-separated list of allowed browser origins for CORS.
    cors_origins: str = (
        "http://127.0.0.1:5173,http://localhost:5173,"
        "http://127.0.0.1:4173,http://localhost:4173,"
        "http://127.0.0.1:3000,http://localhost:3000,"
        "https://eng-to-russia-translator.vercel.app"
    )
    # Also allow any localhost/LAN port during development.
    cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1|\[::1\]|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d+)?$"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
