from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Russian Cursive Learning & Reading Assistant"
    version: str = "0.1.0"
    default_translator: str = "opustmt"
    nllb_model_name: str = "facebook/nllb-200-distilled-600M"
    opusmt_ru_en: str = "Helsinki-NLP/opus-mt-ru-en"
    opusmt_en_ru: str = "Helsinki-NLP/opus-mt-en-ru"
    device: str = "cpu"
    warn_nllb_noncommercial: bool = True


settings = Settings()
