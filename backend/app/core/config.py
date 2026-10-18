from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
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
