from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
MOCK_DIR = ROOT_DIR / "mock"
UPLOAD_DIR = DATA_DIR / "uploads"


class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/expense_agent.db")
    ocr_endpoint: str = os.getenv("ALIBABA_CLOUD_OCR_ENDPOINT", "ocr-api.cn-hangzhou.aliyuncs.com")
    ocr_access_key_id: str | None = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
    ocr_access_key_secret: str | None = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    ocr_min_confidence: float = float(os.getenv("OCR_MIN_CONFIDENCE", "0.8"))
    high_amount_review_threshold: float = float(os.getenv("HIGH_AMOUNT_REVIEW_THRESHOLD", "5000"))


settings = Settings()
