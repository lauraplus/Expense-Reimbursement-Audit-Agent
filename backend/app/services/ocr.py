from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..config import MOCK_DIR, settings


class OCRService:
    def __init__(self):
        fixture_file = MOCK_DIR / "receipts" / "ocr_results.json"
        self.fixtures = json.loads(fixture_file.read_text(encoding="utf-8")) if fixture_file.exists() else {}

    def parse_receipt_image(self, *, category: str, fixture_id: str | None = None, file_path: str | None = None) -> dict[str, Any]:
        if fixture_id:
            fixture = self.fixtures.get(fixture_id)
            if not fixture:
                return self._failed("RECEIPT_FIXTURE_NOT_FOUND", f"未找到票据样例 {fixture_id}")
            normalized = fixture["normalized"]
            return {
                "provider": "mock_fixture",
                "category": category,
                "fixture_id": fixture_id,
                "raw_text": fixture["raw_text"],
                "normalized": normalized,
                "confidence": float(normalized.get("confidence", 0)),
                "low_confidence": float(normalized.get("confidence", 0)) < settings.ocr_min_confidence,
            }
        if not file_path:
            return self._failed("RECEIPT_ATTACHMENT_MISSING", "缺少票据附件")
        return self._parse_with_alibaba_cloud(category=category, file_path=Path(file_path))

    def _parse_with_alibaba_cloud(self, *, category: str, file_path: Path) -> dict[str, Any]:
        if not settings.ocr_access_key_id or not settings.ocr_access_key_secret:
            return self._failed("OCR_CREDENTIALS_MISSING", "未配置阿里云 OCR 环境变量，无法调用真实 OCR")
        if not file_path.exists():
            return self._failed("RECEIPT_FILE_NOT_FOUND", f"附件不存在：{file_path}")
        try:
            from alibabacloud_ocr_api20210707.client import Client as OcrClient
            from alibabacloud_ocr_api20210707 import models as ocr_models
            from alibabacloud_tea_openapi import models as open_api_models
            from alibabacloud_tea_util import models as util_models
        except Exception as exc:  # pragma: no cover - optional SDK
            return self._failed("OCR_SDK_UNAVAILABLE", f"阿里云 OCR SDK 不可用：{exc}")

        try:
            config = open_api_models.Config(
                access_key_id=settings.ocr_access_key_id,
                access_key_secret=settings.ocr_access_key_secret,
            )
            config.endpoint = settings.ocr_endpoint
            client = OcrClient(config)
            with file_path.open("rb") as body:
                request = ocr_models.RecognizeGeneralRequest(body=body)
                response = client.recognize_general_with_options(request, util_models.RuntimeOptions())
            raw_body = response.body.to_map() if hasattr(response.body, "to_map") else response.body
            normalized = self._normalize_general_ocr(category, raw_body)
            return {
                "provider": "alibaba_cloud_ocr",
                "category": category,
                "raw": raw_body,
                "raw_text": normalized.get("raw_text", ""),
                "normalized": normalized,
                "confidence": float(normalized.get("confidence", 0.7)),
                "low_confidence": float(normalized.get("confidence", 0.7)) < settings.ocr_min_confidence,
            }
        except Exception as exc:  # pragma: no cover - external API boundary
            return self._failed("OCR_CALL_FAILED", f"OCR 调用失败：{exc}")

    def _normalize_general_ocr(self, category: str, raw_body: Any) -> dict[str, Any]:
        raw_text = self._flatten_text(raw_body)
        normalized: dict[str, Any] = {"raw_text": raw_text, "confidence": 0.65}
        if category == "traffic_overtime_taxi":
            normalized.update(
                {
                    "from_location": self._match_text(raw_text, r"出发地[:：]\s*([^\n｜|]+)"),
                    "to_location": self._match_text(raw_text, r"(?:目的地|到达地)[:：]\s*([^\n｜|]+)"),
                    "ride_type": self._match_text(raw_text, r"车型[:：]\s*(快车|拼车|出租车|专车|商务车)"),
                    "actual_amount": self._match_amount(raw_text, r"(?:支付金额|实付|金额)[:：]?\s*([0-9]+(?:\.[0-9]+)?)"),
                    "ride_time": self._match_text(raw_text, r"(?:打车时间|用车时间|时间)[:：]?\s*([0-2]?\d:[0-5]\d)"),
                }
            )
        elif category == "travel_hotel":
            normalized.update(
                {
                    "hotel_name": self._match_text(raw_text, r"酒店[:：]\s*([^\n｜|]+)"),
                    "room_rate": self._match_amount(raw_text, r"(?:房费|单价)[:：]?\s*([0-9]+(?:\.[0-9]+)?)"),
                    "nights": self._match_int(raw_text, r"(?:入住|住宿)[:：]?\s*([0-9]+)\s*晚"),
                    "total_amount": self._match_amount(raw_text, r"(?:总额|合计|金额)[:：]?\s*([0-9]+(?:\.[0-9]+)?)"),
                }
            )
        elif category == "team_building":
            normalized.update(
                {
                    "merchant": self._match_text(raw_text, r"(?:商户|门店)[:：]\s*([^\n｜|]+)"),
                    "participants_count": self._match_int(raw_text, r"(?:人数|参与人数)[:：]?\s*([0-9]+)\s*人"),
                    "total_amount": self._match_amount(raw_text, r"(?:金额|总额|合计)[:：]?\s*([0-9]+(?:\.[0-9]+)?)"),
                }
            )
        recognized_fields = [value for key, value in normalized.items() if key not in {"raw_text", "confidence"} and value not in (None, "")]
        if recognized_fields:
            normalized["confidence"] = 0.82
        return normalized

    def _flatten_text(self, value: Any) -> str:
        if isinstance(value, str):
            maybe_json = None
            try:
                maybe_json = json.loads(value)
            except Exception:
                return value
            return self._flatten_text(maybe_json)
        if isinstance(value, dict):
            return "\n".join(self._flatten_text(item) for item in value.values())
        if isinstance(value, list):
            return "\n".join(self._flatten_text(item) for item in value)
        if value is None:
            return ""
        return str(value)

    def _match_text(self, text: str, pattern: str) -> str | None:
        match = re.search(pattern, text)
        return match.group(1).strip() if match else None

    def _match_amount(self, text: str, pattern: str) -> float | None:
        match = re.search(pattern, text)
        return float(match.group(1)) if match else None

    def _match_int(self, text: str, pattern: str) -> int | None:
        match = re.search(pattern, text)
        return int(match.group(1)) if match else None

    def _failed(self, code: str, message: str) -> dict[str, Any]:
        return {
            "provider": "none",
            "error_code": code,
            "error_message": message,
            "raw_text": "",
            "normalized": {},
            "confidence": 0,
            "low_confidence": True,
        }
